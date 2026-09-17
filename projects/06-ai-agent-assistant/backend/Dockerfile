# Same pattern as Project 5's backend Dockerfile — python:3.12-slim (not
# 3.11 — some pinned dependency versions here need it), layer-cached pip
# install, dev-mode server with --reload. See Project 5's README for why
# this repo runs backends in Docker starting there.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
