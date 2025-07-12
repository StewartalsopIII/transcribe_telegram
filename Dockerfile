# Use slim Python base image
FROM python:3.12-slim

# Install system dependencies for pydub (FFmpeg)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy dependency definitions first (for layer caching)
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code
COPY . .

# Run the bot (long polling, no exposed port required)
CMD ["python", "main.py"] 