FROM python:3.13.3-slim-bookworm

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application code
COPY app.py .
COPY templates/ ./templates/

EXPOSE 5000

# Run
CMD ["gunicorn", "--bind", "0.0.0.0:4000", "app:app"]
