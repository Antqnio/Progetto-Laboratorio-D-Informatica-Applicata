FROM python:3.12.11-alpine3.22@sha256:2c0f3b8d6e4f1a5c7b9d8e2f3c4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2

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