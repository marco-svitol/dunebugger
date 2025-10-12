# Use Python slim image for Raspberry Pi
FROM --platform=linux/arm64 python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies required for GPIO and audio
RUN apt-get update && apt-get install -y \
    # GPIO and hardware access
    python3-dev \
    python3-pip \
    build-essential \
    # Audio dependencies for VLC
    vlc-bin \
    vlc-plugin-base \
    libvlc-dev \
    alsa-utils \
    # Remove PulseAudio to avoid conflicts in container
    # pulseaudio \
    # System utilities
    curl \
    wget \
    git \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create directories for mounted volumes (they will be empty until mounted)
RUN mkdir -p ./app/config ./music ./sfx ./sequences

# Set the Python path
ENV PYTHONPATH=/app

# Set audio environment variables for container
ENV ALSA_CARD=0
ENV VLC_VERBOSE=2

# Create a non-root user for security (but with gpio group access)
RUN groupadd -r appuser && useradd -r -g appuser appuser
# Create gpio group and add user to dialout, gpio, and audio groups for hardware access
RUN groupadd -f gpio && usermod -a -G dialout,gpio,audio appuser

# Change ownership of app directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose any ports your application might use (adjust as needed)
# EXPOSE 8080

# Health check (optional - adjust the command as needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Default command to run the application
CMD ["python3", "/app/app/main.py"]