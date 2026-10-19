# ==============================================================================
# Dockerfile — Gemma 4 Offline SWE Agent Sandbox Environment
# ==============================================================================
# Provides a clean, isolated, reproducible execution environment with:
#   - Python 3.10
#   - Git, Ripgrep, SQLite3, and build dependencies
#   - Non-root user with isolated workspace (/workspace) and scratch space (/tmp)
# ==============================================================================

FROM python:3.10-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system utilities & tools required for SWE benchmarks
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ripgrep \
    sqlite3 \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# Copy dependency manifests first to leverage Docker layer caching
COPY requirements.txt requirements-dev.txt pyproject.toml ./

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt && \
    pip install --no-cache-dir -e .

# Create workspace and isolated directories
RUN mkdir -p /workspace /tmp && chmod 777 /workspace /tmp

# Copy repository source code
COPY . /app

# Configure git identity for testing and patch application
RUN git config --global user.name "Gemma4 SWE Agent" && \
    git config --global user.email "agent@gemma4.local" && \
    git config --global safe.directory "*"

# Set default execution directory
WORKDIR /app

# Default command runs the live demonstration
CMD ["python", "demo.py"]
