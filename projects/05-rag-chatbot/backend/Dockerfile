# Kept deliberately simple (one stage, dev-mode server with --reload) —
# this is a learning project run with `docker compose up`, not a
# production deployment. See the project README for why Docker is used
# here at all: it keeps this project's heavier dependencies (torch,
# chromadb, langchain) off your host machine entirely, contained to this
# image instead of a host Python installation.
FROM python:3.12-slim

WORKDIR /app

# Copying just requirements.txt first (before the rest of the source) means
# Docker can cache this slow `pip install` layer — re-running `docker
# compose up --build` after only a code change won't reinstall torch again,
# it'll reuse this cached layer and only redo the fast "copy code" step below.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
