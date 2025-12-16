FROM python:3.11-slim

LABEL org.opencontainers.image.title="Bedrock access gateway"
LABEL org.opencontainers.image.description="Lightweight API that proxies Open WebUI requests to AWS Bedrock."

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONPATH=/app

USER appuser

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
