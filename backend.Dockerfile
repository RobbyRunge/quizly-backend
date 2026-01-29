FROM python:3.12-slim

LABEL maintainer="mail@robby-runge.de"
LABEL version="1.0"
LABEL description="Python 3.12 Slim Debian-based image for Quizly backend"

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash \
    libpq-dev \
    gcc \
    postgresql-client \
    ffmpeg \
    nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    chmod +x backend.entrypoint.sh backend.entrypoint.dev.sh backend.entrypoint.prod.sh

EXPOSE 8000