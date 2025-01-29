# Use an official Python image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to install dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the local backend folder to the container
COPY . .

# Expose the backend port (ensure this matches your app's port)
EXPOSE 8080

# Command to run the backend
CMD ["python", "api.py"]
