# Use --platform to ensure x86_64 architecture for ECS Fargate compatibility
FROM --platform=linux/amd64 python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first
COPY pyproject.toml poetry.lock ./

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry==1.8.3
RUN poetry config virtualenvs.create false
RUN poetry install --only main

# Copy application files
COPY app.py ashrae_data.csv ./

# Copy assets folder for logo and other static files
COPY assets/ assets/

# Copy Streamlit configuration
COPY .streamlit/ .streamlit/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
# Ensure all files have correct permissions before switching user
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false", "--global.developmentMode=false"] 