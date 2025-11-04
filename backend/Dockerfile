FROM python:3.11-slim

# Install system dependencies for Tesseract, image processing, and PostgreSQL
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hun \
    tesseract-ocr-eng \
    libtesseract-dev \
    libpq-dev \
    gcc \
    g++ \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p /tmp/eventhint_uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

