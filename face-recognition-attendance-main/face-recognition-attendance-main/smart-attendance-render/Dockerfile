FROM python:3.11-slim

# System deps needed to compile dlib + run opencv-python-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1 \
    libglib2.0-0 \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads reports encodings

# Render sets $PORT at runtime — default to 10000 for local docker runs
ENV PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} app:app --timeout 120"]
