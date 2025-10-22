FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies required to build some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --default-timeout=600 --no-cache-dir -r /app/requirements.txt

# Copy project files
COPY . /app

# Expose port
EXPOSE 8000

# Start the application with uvicorn
CMD ["uvicorn", "deployscript:app", "--host", "0.0.0.0", "--port", "8000"]
