# SATYA-NET public demo on Render (free web service: 512 MB RAM, 0.1 CPU).
# Build context = repo root. The image carries code and the built console but no
# private data: start.sh downloads the analysed demo DB and ledger keys from a
# private Hugging Face dataset (HF_TOKEN env var). No ML models are needed on the
# server because every analytic is precomputed in the bundled database.
FROM node:20-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
COPY deploy/huggingface/requirements-runtime.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PYTHONUNBUFFERED=1 MALLOC_ARENA_MAX=2 \
    MODE=replay DEMO_READONLY=true EMBED_BACKEND=hashing EMOTION_BACKEND=lexicon \
    AUTO_ANALYTICS=false ENABLE_OTS=false
WORKDIR /home/user/app
COPY --chown=user backend ./backend
COPY --chown=user data ./data
COPY --chown=user eval ./eval
COPY --chown=user replay ./replay
COPY --from=frontend --chown=user /src/frontend/dist ./frontend/dist
COPY --chown=user deploy/render/start.sh /home/user/start.sh
CMD ["bash", "/home/user/start.sh"]
