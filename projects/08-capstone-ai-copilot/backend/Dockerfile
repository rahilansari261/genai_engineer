# Same pattern as Projects 5, 6, and 7 — see their READMEs for why this
# repo runs backends in Docker. python:3.12-slim, layer-cached pip
# install, dev-mode --reload.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
