ARG BASE_IMAGE=python:3.12.9-slim
FROM $BASE_IMAGE

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# system update & package install
RUN apt-get  update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    openssl libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# pip & requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Execute
CMD ["sh", "-c", "alembic upgrade heads && python main.py"]
