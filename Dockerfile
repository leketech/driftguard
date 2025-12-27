# DriftGuard Dockerfile
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    openssh \
    bash \
    build-base \
    librdkafka-dev

# Install Terraform
RUN curl -sSL https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip -o terraform.zip && \
    unzip terraform.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform.zip

# Install Helm
RUN curl -sSL https://get.helm.sh/helm-v3.14.2-linux-amd64.tar.gz -o helm.tar.gz && \
    tar -xzf helm.tar.gz && \
    mv linux-amd64/helm /usr/local/bin/ && \
    rm -rf helm.tar.gz linux-amd64

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser -D driftguard
USER driftguard

# Expose metrics port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["python", "agent/main.py"]