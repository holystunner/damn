FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy core modules
COPY core/ /app/core/

# Copy API service
COPY api_service.py /app/

# Create workspace directory
RUN mkdir -p /tmp/agent_factory/jobs /tmp/agent_factory/orders /tmp/agent_factory/deliveries

# Environment variables (override at runtime)
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_DIR=/tmp/agent_factory
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run API service
CMD ["python", "-m", "uvicorn", "api_service:app", "--host", "0.0.0.0", "--port", "8000"]
