FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN black --check . && flake8 .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
