FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/

# Create directories for volumes
RUN mkdir -p /root/.ssh /app/config

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=4044

# Expose port
EXPOSE 4044

# Run the application
CMD ["python", "-m", "app.main"]