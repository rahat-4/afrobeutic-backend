FROM python:3.13.7-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

 # Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy entire project (adjust if needed)
COPY . .

# Collect static files
RUN python core/manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
