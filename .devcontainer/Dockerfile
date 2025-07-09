FROM python:3.12.3

# Install system libraries needed by OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgtk2.0-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists

# Set the working directory
WORKDIR /app


# Declare a volume for gesture configurations
VOLUME ["/app/static/configs"]

# Copy the current directory contents (including requirments)
COPY . .

# Give execute permission to the start_client.sh script
RUN chmod 755 start_client.sh

# Install dependencies
RUN pip install --no-cache-dir -r docker_client_requirements.lock \
&& rm -f docker_client_requirements.lock

# Make port 9000 available
EXPOSE 9000

# Run container as non root (-m option create new user's home folder,
# which is needed for this build)
RUN groupadd -r appuser && useradd -m -r -g appuser appuser
# Add created user to video group to let him use webcams
RUN usermod -aG video appuser
USER appuser

# Define environment variable (if needed)
# ENV OPENCV_LOG_LEVEL=DEBUG