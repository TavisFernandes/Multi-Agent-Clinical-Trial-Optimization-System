# --- Build React + R3F dashboard (production assets under /dashboard/) ---
FROM node:20-alpine AS dashboard-builder
WORKDIR /build
COPY Dashboard/package.json ./
RUN npm install
COPY Dashboard/ ./
RUN npm run build

# --- FastAPI + static frontends ---
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY Agents ./Agents
COPY Pipeline ./Pipeline
COPY Utils ./Utils
COPY Datasets ./Datasets
COPY Frontend ./Frontend
COPY --from=dashboard-builder /build/dist ./dashboard/dist

ENV MODELS_DIR=/models
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
