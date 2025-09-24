import os

ROOT_IMPORTANT_FILES = [
    # Version Control
    ".gitignore",
    ".gitattributes",
    # Documentation
    "README",
    "README.md",
    "README.txt",
    "README.rst",
    "CONTRIBUTING",
    "CONTRIBUTING.md",
    "CONTRIBUTING.txt",
    "CONTRIBUTING.rst",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "CHANGELOG",
    "CHANGELOG.md",
    "CHANGELOG.txt",
    "CHANGELOG.rst",
    "SECURITY",
    "SECURITY.md",
    "SECURITY.txt",
    "CODEOWNERS",
    # Python Package Management and Dependencies
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    # Configuration and Settings
    ".env",
    ".env.example",
    ".editorconfig",
    ".pylintrc",
    ".flake8",
    ".dockerignore",
    ".gitpod.yml",
    "sonar-project.properties",
    "renovate.json",
    "dependabot.yml",
    ".pre-commit-config.yaml",
    "mypy.ini",
    "tox.ini",
    ".yamllint",
    "pyrightconfig.json",
    # Python Build and Compilation
    "MANIFEST.in",
    # Python Testing
    "pytest.ini",
    # CI/CD
    ".travis.yml",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
    "appveyor.yml",
    "circle.yml",
    ".circleci/config.yml",
    ".github/dependabot.yml",
    "codecov.yml",
    ".coveragerc",
    # Docker and Containers
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.override.yml",
    # Cloud and Infrastructure (Language Agnostic)
    "app.yaml",
    "terraform.tf",
    "main.tf",
    "cloudformation.yaml",
    "cloudformation.json",
    "ansible.cfg",
    "kubernetes.yaml",
    "k8s.yaml",
    # Database (Generic)
    "schema.sql",
    # API Documentation (Language Agnostic)
    "swagger.yaml",
    "swagger.json",
    "openapi.yaml",
    "openapi.json",
    # Python Development Environment
    ".python-version",
    "Vagrantfile",
    # Quality and Metrics
    ".codeclimate.yml",
    "codecov.yml",
    # Documentation (Language Agnostic)
    "mkdocs.yml",
    "readthedocs.yml",
    ".readthedocs.yaml",
    # Python Linting and Formatting
    ".isort.cfg",
    ".markdownlint.json",
    ".markdownlint.yaml",
    # Security
    ".bandit",
    ".secrets.baseline",
    # Python Misc
    ".pypirc",
    ".gitkeep",
]


# Normalize the lists once
NORMALIZED_ROOT_IMPORTANT_FILES = set(
    os.path.normpath(path) for path in ROOT_IMPORTANT_FILES
)


def is_important(file_path):
    file_name = os.path.basename(file_path)
    dir_name = os.path.normpath(os.path.dirname(file_path))
    normalized_path = os.path.normpath(file_path)

    # Check for GitHub Actions workflow files
    if dir_name == os.path.normpath(".github/workflows") and file_name.endswith(".yml"):
        return True

    return normalized_path in NORMALIZED_ROOT_IMPORTANT_FILES


def filter_important_files(file_paths):
    """
    Filter a list of file paths to return only those that are commonly important in Python codebases.

    :param file_paths: List of file paths to check
    :return: List of file paths that match important file patterns for Python projects
    """
    return list(filter(is_important, file_paths))
