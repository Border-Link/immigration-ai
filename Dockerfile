# --------------------------
# Base image and Python version
# --------------------------
ARG PYTHON_VERSION=3.14-slim-bullseye
FROM python:${PYTHON_VERSION}

LABEL authors="Oluwatosin Amokeodo"

# --------------------------
# Environment variables
# --------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PATH="/root/.local/bin:${PATH}"

# --------------------------
# System dependencies
# --------------------------
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    libjpeg-dev \
    libcairo2 \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# --------------------------
# Set working directory
# --------------------------
WORKDIR /src

# --------------------------
# Create Python virtual environment
# --------------------------
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# --------------------------
# Copy and install dependencies
# --------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --------------------------
# Copy source code
# --------------------------
COPY ./src /src

# --------------------------
# Optional: copy development .env file
# --------------------------
ARG COPY_ENV=false
COPY .env .env

# --------------------------
# Build arguments for runtime config
# --------------------------
ARG SECRET_KEY
ARG DEBUG=0
ARG PROJECT_NAME="personal-finance-manager"

ENV SECRET_KEY=${SECRET_KEY}
ENV DEBUG=${DEBUG}
ENV PROJECT_NAME=${PROJECT_NAME}

# --------------------------
# Expose port
# --------------------------
EXPOSE 8000

# --------------------------
# Default command
# --------------------------
# If PRODUCTION=true, run Gunicorn, else default to Django dev server
ARG PRODUCTION=false
CMD if [ "${PRODUCTION}" = "true" ]; then \
        gunicorn --bind 0.0.0.0:8000 finance.wsgi:application; \
    else \
        python manage.py runserver 0.0.0.0:8000; \
    fi
