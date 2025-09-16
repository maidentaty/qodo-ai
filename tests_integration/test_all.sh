#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit if any command in a pipeline fails
set -x  # Print commands and their arguments as they are executed

# Default model name
MODEL="gpt-4o-2024-11-20"
SUPPRESS_LOG_FILES=""

# Function to display usage
usage() {
    echo "Usage: $0 [--model model_name]"
    echo "  --model model_name      Set the model name (default: gpt-4o-mini)"
    echo "  --suppress-log-files    Suppress generation of log files"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift
            ;;
        --suppress-log-files)
            SUPPRESS_LOG_FILES="--suppress-log-files"
            ;;
        *)
            usage
            ;;
    esac
    shift
done

# Set the log_db_arg variable if LOG_DB_PATH is set
log_db_arg=""
if [ -n "$LOG_DB_PATH" ]; then
    log_db_arg="--log-db-path $LOG_DB_PATH"
fi

# Python FastAPI Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/python_fastapi:latest" \
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --model "gpt-4o-mini" \
  $log_db_arg \
  $SUPPRESS_LOG_FILES

