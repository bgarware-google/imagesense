# Use official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    U2NET_HOME=/app/.u2net

WORKDIR /app

# Install system dependencies needed for OpenCV, image processing, and font rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-create model and runtime directories
RUN mkdir -p /app/.u2net /app/tmp /app/fonts

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Cloud Run default port
EXPOSE 8080

# Run Gradio app
CMD ["python", "app.py"]
