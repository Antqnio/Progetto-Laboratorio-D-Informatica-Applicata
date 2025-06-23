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

# Copy requirements and install dependencies
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

# Copy the current directory contents
COPY . .

# Make port 9000 available
EXPOSE 9000

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]