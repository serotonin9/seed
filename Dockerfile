FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .

RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "seed.py"]
