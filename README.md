# er-aws-msk

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI](https://img.shields.io/pypi/v/er-aws-msk)][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]
![PyPI - License](https://img.shields.io/pypi/l/er-aws-msk)

This is a template for a Python project. It can be used via GitHub's template feature or by copying and pasting the files into your project.

## Features

- [Poetry](https://python-poetry.org/) for dependency management.
- [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.
- Containerized CI/CD tasks.
- Secure `.gitignore` and `.dockerignore` files.
- Example code and tests.

## Usage

1. Create a new GitHub repository using this template.
1. Replace the dummy project name `er-aws-msk` with your project name.

   ```bash
    find . -type d -name .git -prune  -o -type f -exec sed -i "s/er-aws-msk/your-project-name/g" {} \;
    git mv er_aws_msk $PROJECT_PACKAGE
    find . -type d -name .git -prune  -o -type f -exec sed -i "s/er_aws_msk/$PROJECT_PACKAGE/g" {} \;
    ```

1. Replace the dummy python package name `er_aws_msk` (snake_case!) with your package name.

   ```bash
    export PROJECT_PACKAGE=your_project_name # snake_case
    git mv er_aws_msk $PROJECT_PACKAGE
    find . -type d -name .git -prune  -o -type f -exec sed -i "s/er_aws_msk/$PROJECT_PACKAGE/g" {} \;
    ```

[pypi-link]:                https://pypi.org/project/er-aws-msk/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/er-aws-msk
