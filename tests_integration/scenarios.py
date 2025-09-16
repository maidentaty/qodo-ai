from cover_agent.settings.config_schema import CoverageType

TESTS = [
    # Python FastAPI Example
    {
        "docker_image": "embeddeddevops/python_fastapi:latest",
        "source_file_path": "app.py",
        "test_file_path": "test_app.py",
        "test_command": r"pytest --cov=. --cov-report=xml --cov-report=term",
        "model": "gpt-4o-mini",
    },
]
