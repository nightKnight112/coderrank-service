FROM python:3.11-slim

# Install dependencies for Docker and sshpass
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     sshpass \
#     curl \
#     gnupg2 \
#     ca-certificates \
#     lsb-release && \
#     curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
#     echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
#     apt-get update && \
#     apt-get install -y --no-install-recommends docker-ce-cli && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*

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
