FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py corpus_store.py annotation_store.py search_service.py ./
COPY templates/ templates/
COPY static/ static/

ENV DATA_DIR=/data

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
