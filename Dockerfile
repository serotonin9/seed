FROM python:3.10.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies with legacy resolver
COPY requirements.txt .
RUN pip install --upgrade pip==23.0.1 setuptools wheel && \
    pip install \
    --no-cache-dir \
    --use-deprecated=legacy-resolver \
    -r requirements.txt

COPY . .

CMD ["python", "seed.py"]
