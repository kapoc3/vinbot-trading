# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Set working directory
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Configure Poetry: Do not create a virtual environment inside the container
RUN poetry config virtualenvs.create false

# Install Python dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

# Copy project files
COPY . .

# Create data directory for persistence
RUN mkdir -p /app/data

# Exposure port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
