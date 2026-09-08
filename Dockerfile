FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for LightGBM OpenMP support and C building
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY . /app/

# Create folders for persistent volume mounts
RUN mkdir -p /app/data /app/models

EXPOSE 8080

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
