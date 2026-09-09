FROM python:3.11-slim

WORKDIR /app

# Copy all project files
COPY . /app

# Expose server port
EXPOSE 8080

# Environment defaults
ENV PORT=8080

# Start Landigo Express server
CMD ["python", "server.py"]
