FROM python:3.11-slim

WORKDIR /app

COPY Sprint_5/src/interface/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Sprint_5/src/interface/app.py Sprint_5/src/interface/corpus_store.py Sprint_5/src/interface/annotation_store.py Sprint_5/src/interface/search_service.py ./
COPY Sprint_5/src/interface/frontend/ frontend/

COPY Sprint_5/data/ /data/

ENV DATA_DIR=/data

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]