FROM python:3.11-slim

WORKDIR /app

COPY src/interface/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/interface/app.py src/interface/corpus_store.py src/interface/annotation_store.py src/interface/search_service.py ./
COPY src/interface/frontend/ frontend/

COPY data/ /data/

ENV DATA_DIR=/data

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]