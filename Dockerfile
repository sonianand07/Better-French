FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/live data/processed data/archive

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 frenchmax && \
    chown -R frenchmax:frenchmax /app
USER frenchmax

# Expose port for health checks
EXPOSE 8001

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=2m --retries=3 \
  CMD python3 -c "import os; exit(0 if os.path.exists('scheduler.pid') else 1)" || exit 1

# Run the scheduler
CMD ["python3", "scripts/scheduler_main.py"] 