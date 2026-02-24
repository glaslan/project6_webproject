FROM python:3.13.3-slim-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY app.py .
COPY templates/ ./templates/
COPY database.db .
COPY images/ ./images/

EXPOSE 4000

# Run with waitress (production WSGI server)
CMD ["python", "app.py"]
