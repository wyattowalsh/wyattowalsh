# Contributing to wyattowalsh

First off, thank you for considering contributing to `wyattowalsh`! This project is hosted on GitHub at [https://github.com/wyattowalsh/wyattowalsh](https://github.com/wyattowalsh/wyattowalsh). It's people like you that make open source such a great community.

We welcome many types of contributions, including:

*   New features
*   Bug fixes
*   Documentation improvements
*   Issue triage and discussions
*   Feedback and suggestions

## Getting Started

If you're new to the project, a good place to start is by looking at the [open issues](https://github.com/wyattowalsh/wyattowalsh/issues), particularly those labeled `good first issue` or `help wanted` on the [main repository page](https://github.com/wyattowalsh/wyattowalsh).
You may also find helpful information in our [project documentation](https://readme.w4w.dev), including our [Development Notes](https://readme.w4w.dev/notes) and the project [Roadmap](https://readme.w4w.dev/roadmap).

Before you start working on an issue, please leave a comment to let others know you're interested in taking it on. This helps prevent duplicated effort.

### Setting up your Development Environment

1.  **Fork the repository** on GitHub.
2.  **Clone your fork locally:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/wyattowalsh.git
    cd wyattowalsh
    ```
3.  **Set up the Python environment using `uv`:**
    Refer to the main `README.md` and `Makefile` for instructions on setting up the development environment with `uv`. Typically, this involves:
    ```bash
    uv venv  # Create virtual environment
    uv sync  # Install dependencies
    # or simply `make install` or `make venv`
    ```
4.  **Create a new branch** for your changes:
    ```bash
    git checkout -b feature/your-feature-name # For new features
    # or
    git checkout -b fix/your-bug-fix-name   # For bug fixes
    ```

### Making Changes

*   Ensure your code adheres to the project's coding standards. Use the linting and formatting tools provided:
    ```bash
    make format
    make lint
    ```
*   Consult the [Development Notes](https://readme.w4w.dev/notes) for any specific guidelines related to the area you are working on.
*   Write clear, concise, and well-documented code.
*   Add tests for any new features or bug fixes. Ensure all tests pass:
    ```bash
    make test
    ```
*   Update documentation if your changes require it.
*   Ensure your commit messages are clear and descriptive. We loosely follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Submitting a Pull Request

1.  **Push your changes** to your fork:
    ```bash
    git push origin feature/your-feature-name
    ```
2.  **Open a Pull Request** (PR) to the `master` branch of the `wyattowalsh/wyattowalsh` repository.
3.  Fill out the PR template with as much detail as possible.
4.  Link any relevant issues in your PR description (e.g., "Fixes #123").
5.  Ensure all automated checks (CI/CD workflows) pass.

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [wyattowalsh@gmail.com](mailto:wyattowalsh@gmail.com).

## Issue and Pull Request Lifecycle

*   Once a PR is submitted, maintainers will review it. Constructive feedback may be provided, and you might be asked to make changes.
*   After review and approval, your PR will be merged.
*   Issues will be triaged and labeled by maintainers.

## Questions?

Feel free to open an issue if you have questions or need clarification on anything.
Please also check our [project documentation](https://readme.w4w.dev) for answers.

Thank you for your contribution! 