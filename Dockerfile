# Single image: FastAPI backend + built console served from the same origin (PRD 14 / B5).
#   docker build -t deepastambha . && docker run -p 8000:8000 deepastambha
# Mount data/, models/ and replay/ at /data, /models, /replay (see docker-compose.yml).

FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-hin tesseract-ocr-eng libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch
COPY backend/ ./
RUN pip install --no-cache-dir -e ".[dev]"
COPY --from=frontend /frontend/dist /frontend/dist
ENV FRONTEND_DIST=/frontend/dist
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
