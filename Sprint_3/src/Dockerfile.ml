FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn openai
COPY ml_backend.py .
CMD ["python", "ml_backend.py"]
