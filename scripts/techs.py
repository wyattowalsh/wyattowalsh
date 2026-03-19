"""
Technology Data Processing for Project Documentation.

This module handles the loading, parsing, and processing of technology data
from a Markdown file. It defines a `Technology` Pydantic model for structured
data representation and includes functions to:
- Parse technology entries from Markdown content.
- Categorize technologies based on predefined sections.
- Potentially generate Markdown or other output formats for documentation.

The script focuses on extracting structured information (name, level, category)
from a semi-structured Markdown format, making it suitable for populating
project READMEs, skills matrices, or generating visualizations like word clouds.
"""

import re
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError
from rich.table import Table

from .utils import console, get_logger  # Changed to relative import

logger = get_logger(module=__name__)  # Initialize logger


# Define a Pydantic model for a technology entry
class Technology(BaseModel):
    """Represents a technology with its name, proficiency level, and category."""

    name: str = Field(..., description="Name of the technology")
    level: int = Field(
        ...,
        description="Proficiency level (1-5)",
        ge=1,
        le=5,
    )
    category: Optional[str] = Field(
        None, description="Category of the technology (e.g., Frontend, Backend)"
    )
    notes: Optional[str] = Field(None, description="Additional notes or usage context")


# Predefined categories for technologies (can be expanded)
# The order here can influence the order in generated outputs if maintained.
PREDEFINED_CATEGORIES = [
    "Programming Languages",
    "Frontend Frameworks & Libraries",
    "Backend Frameworks & Libraries",
    "Databases & Storage",
    "Cloud & DevOps",
    "AI & Machine Learning",
    "Testing & QA",
    "Project Management & Collaboration",
    "Data Science & Analytics",
    "Mobile Development",
    "Game Development",
    "Security",
    "Operating Systems",
    "Web Servers & Load Balancers",
    "APIs & Microservices",
    "CI/CD & Automation",
    "Containerization & Orchestration",
    "Monitoring & Logging",
    "Version Control Systems",
    "IDEs & Code Editors",
    "Design & Prototyping Tools",
    "Blockchain & Web3",
    "IoT (Internet of Things)",
    "AR/VR (Augmented/Virtual Reality)",
    "Cybersecurity Tools",
    "Networking",
    "Big Data Technologies",
    "Business Intelligence (BI) Tools",
    "Content Management Systems (CMS)",
    "Marketing Automation Tools",
    "Other Tools & Libraries",
]


def parse_technology_line(
    line: str, current_category: Optional[str]
) -> Optional[Technology]:
    """
    Parses a single line of Markdown to extract technology information.

    Expected format: "- Technology Name (Level: X)" or "- Technology Name (Level: X) - Notes"

    Args:
        line: The Markdown line to parse.
        current_category: The current category context from Markdown headers.

    Returns:
        A Technology object if parsing is successful, otherwise None.
    """
    # Regex to capture: Technology Name, Level, and optional Notes
    # Example: "- Python (Level: 5) - Primary language for backend and scripts."
    # Group 1: Name (Python)
    # Group 2: Level (5)
    # Group 3: Optional notes ( Primary language for backend and scripts.)
    match = re.match(
        r"^\s*-\s*(.+?)\s*\(Level:\s*(\d)\s*\)(?:\s*-\s*(.+))?$", line.strip()
    )
    if match:
        name = match.group(1).strip()
        level_str = match.group(2).strip()
        notes = match.group(3).strip() if match.group(3) else None
        try:
            level = int(level_str)
            if not 1 <= level <= 5:
                logger.warning(
                    f"Invalid level '{level}' for '{name}'. Must be 1-5. Skipping."
                )
                return None
            return Technology(
                name=name, level=level, category=current_category, notes=notes
            )
        except ValueError:
            logger.warning(
                f"Could not parse level '{level_str}' for '{name}'. Skipping."
            )
            return None
        except ValidationError as e:
            logger.warning("Validation error for {name!r}: {e}. Skipping.", name=name, e=e)
            return None
    return None


def load_technologies(md_file_path: Path) -> List[Technology]:
    """
    Loads technology data from a Markdown file.

    The Markdown file should be structured with H2 (##) for categories and
    list items for technologies with levels.

    Args:
        md_file_path: Path to the Markdown file containing technology data.

    Returns:
        A list of Technology objects.
    """
    if not md_file_path.exists():
        logger.error("Technologies file not found: {md_file_path}", md_file_path=md_file_path)
        return []

    technologies = []
    current_category: Optional[str] = None

    try:
        with open(md_file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line_stripped = line.strip()
                if line_stripped.startswith("## "):
                    current_category = line_stripped[3:].strip()
                    if current_category not in PREDEFINED_CATEGORIES:
                        logger.info(
                            f"Found custom category: '{current_category}' \
(line {line_num})"
                        )
                elif line_stripped.startswith("-") and current_category:
                    tech = parse_technology_line(line_stripped, current_category)
                    if tech:
                        technologies.append(tech)
                elif (
                    line_stripped
                    and not line_stripped.startswith("#")
                    and not current_category
                ):
                    # This case handles lines that might be technologies but are not under a category
                    # This could happen if the MD file is not well-formed
                    logger.debug(
                        f"Line '{line_num}' ('{line_stripped}') not under a category. Attempting parse without category."
                    )
                    tech = parse_technology_line(line_stripped, "Uncategorized")
                    if tech:
                        technologies.append(tech)
    except FileNotFoundError:
        logger.error("File not found: {md_file_path}", md_file_path=md_file_path)
        return []
    except Exception as e:
        logger.error("Error reading or parsing {md_file_path}: {e}", md_file_path=md_file_path, e=e, exc_info=True)
        return []

    logger.info(
        f"Successfully loaded {len(technologies)} technologies from \
{md_file_path}"
    )
    return technologies


def display_technologies(technologies: List[Technology]) -> None:
    """
    Displays the list of technologies in a Rich Table, grouped by category.

    Args:
        technologies: A list of Technology objects.
    """
    if not technologies:
        console.print("[yellow]No technologies to display.[/yellow]")
        return

    table = Table(
        title="Technology Stack & Proficiency",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Category", style="dim cyan", width=30)
    table.add_column("Technology Name", style="green")
    table.add_column("Level (1-5)", justify="right", style="blue")
    table.add_column("Notes", style="italic yellow")

    # Group technologies by category
    categorized_techs: dict[str, List[Technology]] = {}
    for tech in technologies:
        cat = tech.category or "Uncategorized"
        if cat not in categorized_techs:
            categorized_techs[cat] = []
        categorized_techs[cat].append(tech)

    # Sort categories by predefined order, then alphabetically for custom ones
    sorted_categories = sorted(
        categorized_techs.keys(),
        key=lambda c: (
            (
                PREDEFINED_CATEGORIES.index(c)
                if c in PREDEFINED_CATEGORIES
                else float("inf")
            ),
            c,
        ),
    )

    for category_name in sorted_categories:
        # Add a section for each category (consider using Rich Panel or Text for header)
        # For simplicity, just adding rows directly
        first_in_category = True
        for tech in sorted(
            categorized_techs[category_name], key=lambda t: t.name.lower()
        ):
            notes_str = tech.notes if tech.notes else "-"
            if first_in_category:
                table.add_row(category_name, tech.name, str(tech.level), notes_str)
                first_in_category = False
            else:
                table.add_row("", tech.name, str(tech.level), notes_str)
        if category_name != sorted_categories[-1]:
            table.add_row(end_section=True)  # Adds a separator line

    console.print(table)


# Example usage (for testing or direct script execution)
if __name__ == "__main__":
    logger.info("Executing technology script directly for testing...")

    # Define the path to your technologies.md file
    # Assumes the script is in a 'scripts' directory, and 'techs.md' is one level up.
    tech_file_path = Path(__file__).parent.parent / "techs.md"
    logger.info("Attempting to load technologies from: {tech_file_path}", tech_file_path=tech_file_path)

    if not tech_file_path.exists():
        logger.error(
            f"Techs file {tech_file_path} not found. \
Make sure it exists in the project root."
        )
        console.print(
            f"[bold red]Error:[/bold red] {tech_file_path} not found. \
Create it with your technology list."
        )
    else:
        loaded_technologies = load_technologies(tech_file_path)
        if loaded_technologies:
            logger.info(
                f"Loaded {len(loaded_technologies)} technologies. Displaying them..."
            )
            display_technologies(loaded_technologies)
        else:
            logger.warning("No technologies were loaded. Check the file format.")
            console.print("[yellow]No technologies loaded from the file.[/yellow]")

    # --- Example of generating a simple Markdown output (not part of CLI by default) ---
    # This is a conceptual example. A more robust version would use a template engine.
    # def generate_tech_markdown_section(technologies: List[Technology]) -> str:
    #     markdown_output = "## My Tech Stack\n"
    #     categorized = {}
    #     for tech in technologies:
    #         cat = tech.category or "Other"
    #         if cat not in categorized:
    #             categorized[cat] = []
    #         categorized[cat].append(tech)
    #
    #     for category_name in sorted(categorized.keys()):
    #         markdown_output += f"\n### {category_name}\n"
    #         for tech in sorted(categorized[category_name], key=lambda t: t.name):
    #             level_stars = "⭐" * tech.level + "🌑" * (5 - tech.level)
    #             notes_part = f" - {tech.notes}" if tech.notes else ""
    #             markdown_output += f"- **{tech.name}**: {level_stars}{notes_part}\n"
    #     return markdown_output
    #
    # if loaded_technologies:
    #     md_section = generate_tech_markdown_section(loaded_technologies)
    #     output_md_path = Path(__file__).parent.parent / "generated_tech_stack.md"
    #     try:
    #         with open(output_md_path, "w", encoding="utf-8") as f_out:
    #             f_out.write(md_section)
    #         logger.info(f"Generated tech stack markdown at: {output_md_path}")
    #         console.print(f"[green]Generated Markdown section to {output_md_path}[/green]")
    #     except Exception as e_write:
    #         logger.error(f"Could not write markdown output: {e_write}")
    #         console.print(f"[red]Error writing markdown: {e_write}[/red]")
