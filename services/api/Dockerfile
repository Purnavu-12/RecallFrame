FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/root/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
# Install CPU-only Torch first so sentence-transformers does not resolve the
# much larger CUDA-enabled PyPI build in the CPU-default Compose image.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch==2.14.1"
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV HF_HOME=/home/recallframe/.cache/huggingface
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin recallframe \
    && mkdir -p /data/media "$HF_HOME" \
    && chown -R recallframe:recallframe /data/media /home/recallframe
USER recallframe
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
