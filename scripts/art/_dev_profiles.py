"""
_dev_profiles.py
~~~~~~~~~~~~~~~~
Development-only mock profiles for local animation testing.

These profiles contain fictional data for use with:
    uv run python -m scripts.art.animate --profile <name>

Do not use in production; live data comes from fetch_metrics.collect().
"""
from __future__ import annotations

# Mock profiles for prototyping
PROFILES = {
    "wyatt": {
        "label": "wyattowalsh", "stars": 42, "forks": 12, "watchers": 8,
        "followers": 85, "following": 60, "public_repos": 35, "orgs_count": 3,
        "contributions_last_year": 1200, "total_commits": 4800,
        "open_issues_count": 5, "network_count": 18,
        "repos": [
            {"name": "gnn-mol", "language": "Python", "stars": 12, "age_months": 24},
            {"name": "ball", "language": "Python", "stars": 8, "age_months": 36},
            {"name": "portfolio", "language": "TypeScript", "stars": 5, "age_months": 18},
            {"name": "dotfiles", "language": "Shell", "stars": 3, "age_months": 60},
            {"name": "nba-db", "language": "Python", "stars": 6, "age_months": 48},
            {"name": "wyattowalsh", "language": "Python", "stars": 2, "age_months": 12},
            {"name": "research", "language": "Jupyter Notebook", "stars": 4, "age_months": 30},
        ],
        "contributions_monthly": {
            "01": 120, "02": 95, "03": 180, "04": 210, "05": 140, "06": 60,
            "07": 45, "08": 80, "09": 150, "10": 200, "11": 170, "12": 90,
        },
    },
    "prolific": {
        "label": "Prolific OSS", "stars": 5200, "forks": 890, "watchers": 340,
        "followers": 12000, "following": 150, "public_repos": 180, "orgs_count": 8,
        "contributions_last_year": 3800, "total_commits": 42000,
        "open_issues_count": 120, "network_count": 2400,
        "repos": [
            {"name": f"p-{i}", "language": lang, "stars": s, "age_months": a}
            for i, (lang, s, a) in enumerate([
                ("Python", 1200, 84), ("JavaScript", 800, 96), ("TypeScript", 600, 48),
                ("Go", 400, 60), ("Rust", 350, 36), ("C++", 280, 108),
                ("Python", 200, 72), ("Shell", 150, 120), ("Ruby", 120, 90),
                ("Java", 100, 60), ("Python", 80, 24), ("TypeScript", 60, 36),
            ])
        ],
        "contributions_monthly": {
            "01": 380, "02": 420, "03": 350, "04": 400, "05": 310, "06": 280,
            "07": 290, "08": 320, "09": 360, "10": 400, "11": 380, "12": 310,
        },
    },
    "newcomer": {
        "label": "New Developer", "stars": 3, "forks": 1, "watchers": 2,
        "followers": 8, "following": 45, "public_repos": 6, "orgs_count": 1,
        "contributions_last_year": 180, "total_commits": 320,
        "open_issues_count": 2, "network_count": 3,
        "repos": [
            {"name": "hello-world", "language": "Python", "stars": 1, "age_months": 8},
            {"name": "todo-app", "language": "JavaScript", "stars": 2, "age_months": 5},
        ],
        "contributions_monthly": {"08": 25, "09": 30, "10": 40, "11": 35, "12": 40},
    },
}
