FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY scripts/wait-for-it.sh /app/scripts/wait-for-it.sh
RUN chmod +x /app/scripts/wait-for-it.sh

CMD ["bash", "-c", "/wait-for-it.sh db:5432 -- python manage.py migrate && daphne -b 0.0.0.0 -p 8000 web_project.asgi:application"]
