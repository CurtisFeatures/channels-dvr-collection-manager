FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ /app/
COPY templates/ /app/templates/
COPY static/ /app/static/

# Create config directory
RUN mkdir -p /config

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "main.py"]
