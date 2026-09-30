# DEEPASTAMBHA public demo on Hugging Face Spaces (Docker, free CPU tier).
# Code is cloned from the public GitHub repo at build time; the analysed demo
# database and the ledger signing key come from a PRIVATE Hugging Face dataset
# repo at start-up (Space secret HF_TOKEN). Kept awake by deploy/keepalive.
FROM node:20-slim AS frontend
ARG REPO=https://github.com/Shantanu58-tech/PS_2.git
ARG REF=main
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "$REF" "$REPO" /src
WORKDIR /src/frontend
RUN npm ci && npm run build

FROM python:3.11-slim
COPY requirements-runtime.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1 \
    MODE=replay DEMO_READONLY=true EMBED_BACKEND=hashing EMOTION_BACKEND=lexicon \
    AUTO_ANALYTICS=false ENABLE_OTS=false
WORKDIR /home/user/app
COPY --from=frontend --chown=user /src/backend /home/user/app/backend
COPY --from=frontend --chown=user /src/frontend/dist /home/user/app/frontend/dist
COPY --from=frontend --chown=user /src/data /home/user/app/data
COPY --from=frontend --chown=user /src/eval /home/user/app/eval
COPY --from=frontend --chown=user /src/replay /home/user/app/replay
COPY --chown=user start.sh /home/user/start.sh
EXPOSE 7860
CMD ["bash", "/home/user/start.sh"]
