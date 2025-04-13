#!/bin/bash
# ─────────────────────────────────────────────────────────────
# EC2 User‑Data – Housing Alert AI on Amazon Linux 2023 
# (Using pyenv, pyenv-virtualenv, Python 3.12 with all commands running as root)
# ─────────────────────────────────────────────────────────────
set -euxo pipefail

### 1. System packages and build dependencies
dnf update --allowerasing -y
dnf install --allowerasing -y git gcc-c++ make \
  openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel curl

### 2. Install pyenv and pyenv-virtualenv for root

# Run the installer as root so that pyenv is installed in /root/.pyenv
curl https://pyenv.run | bash

# Append pyenv initialization to root's ~/.bashrc so that it loads automatically on login
cat << 'EOF' >> /root/.bashrc

# Pyenv initialization
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
if command -v pyenv 1>/dev/null 2>&1; then
    # Initialize pyenv
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    # Initialize pyenv-virtualenv
    eval "$(pyenv virtualenv-init -)"
fi
EOF

# Export environment for the current script execution (running as root) for subsequent commands
export PYENV_ROOT="/root/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

### 3. Install Python 3.12 via pyenv
pyenv install -s 3.12.0
pyenv global 3.12.0

### 4. Install Poetry globally using the pyenv Python
python -m pip install --upgrade pip
curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local/poetry python -
ln -s /usr/local/poetry/bin/poetry /usr/local/bin/poetry

cat > .env <<'EOF'
AWS_REGION=us-east-1
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-7-sonnet-20250219-v1:0
UPSTAGE_API_KEY=replace_me
S3_BUCKET=minerva-1-pdf-bucket
DYNAMO_USER_TABLE=minerva-1-user-info-table
DYNAMO_NOTICE_TABLE=minerva-1-pdf-info-table
EOF

# Set Poetry to create virtual environments inside the project directory
export POETRY_VIRTUALENVS_IN_PROJECT=true

# Use the pyenv-installed Python for the Poetry virtual environment
poetry env use "$(pyenv which python)"
poetry install --no-root

export PYTHONPATH=$PWD/src
poetry run streamlit run src/housing_alert/streamlit_app.py

echo "Setup complete. App running on port 8501 (Python 3.12 via pyenv and pyenv-virtualenv)."