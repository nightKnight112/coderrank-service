FROM python:3.11-slim

RUN apt-get update && apt-get install -y default-jdk

# Set up working directory
WORKDIR /app

# Copy the application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask app port
EXPOSE 5000

# Default command to run the Python app
CMD ["python", "./app.py"]
