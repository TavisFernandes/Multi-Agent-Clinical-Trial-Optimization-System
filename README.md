# Multi-Agent Clinical Trial Optimization System

## Overview
This repository is a prototype platform for clinical trial intelligence that combines:
- a FastAPI backend for text and image analysis,
- a multi-agent reasoning loop (Retriever, Architect, Critic),
- a React 3D dashboard for immersive visualization,
- pre-trained clinical and image models stored in `Models/`.

The system is designed to analyze clinical text or image input, route it through the appropriate pipeline, and then refine an evidence-grounded report with iterative agent feedback.

## Key Features
- Text pipeline with named entity recognition (NER) and clinical analysis.
- Image pipeline for CNN/ResNet-based classification.
- Multi-agent reasoning loop with retriever, architect, and critic agents.
- FastAPI endpoints for synchronous and streamed analysis.
- WebSocket support for live agent event streaming.
- Static React dashboard served from Docker-built production assets.
- Legacy frontend available at `/ui/index.html`.

## Architecture
### Backend
- `app.py`: FastAPI entrypoint.
  - `/analyze`: HTTP POST for single-run analysis.
  - `/analyze/stream`: HTTP POST for real-time server-sent event streaming.
  - `/ws/agents`: WebSocket endpoint for immersive dashboard event streaming.
  - `/health`: health check endpoint.
  - `/dashboard`: serves the built React dashboard.
  - `/ui`: serves legacy static frontend.

- `Pipeline/`: orchestrates input classification and model execution.
  - `main_pipeline.py`: routes input to either text or image processing.
  - `task_classifier.py`: determines whether input is text or image.
  - `text_pipeline.py`: runs NER and LSTM-based clinical text processing.
  - `image_pipeline.py`: runs CNN/ResNet-style image classification.

- `Agents/`: multi-agent loop logic.
  - `retriever_agent.py`: finds relevant clinical documents.
  - `architect_agent.py`: generates or improves the report.
  - `critic_agent.py`: reviews output and identifies missing fields.
  - `agent_loop.py`: controls the iterative reasoning flow.

- `Utils/model_registry.py`: loads and manages trained models from `/models`.

### Dashboard
- `Dashboard/`: React + Vite + Three.js dashboard source.
- Uses `@react-three/fiber`, `@react-three/drei`, and `framer-motion` for 3D visualization.
- The dashboard loads its production build into the backend Docker image and serves it under `/dashboard`.

## Docker-based Run Instructions
This repository is configured to run with Docker Compose.

### Prerequisites
- Docker installed on Windows.
- Docker Compose available.
- The `Models/` folder must contain trained model files such as `.h5` models.

### Run the application
From the repository root:

```powershell
docker compose up --build
```

### Access the app
- Open `http://localhost:8000/` for the 3D dashboard.
- Open `http://localhost:8000/dashboard/` directly if needed.
- Open `http://localhost:8000/ui/index.html` to access the legacy frontend.

### Notes
- The Docker image builds the React dashboard in a Node stage, then installs Python dependencies in a second stage.
- The backend listens on port `8000` and expects model files in `/models`, which is mounted from the host via `docker-compose.yml`.
- `MODELS_DIR` is set to `/models` inside the container.

## Important Project Details
- The backend uses `uvicorn app:app --host 0.0.0.0 --port 8000`.
- If `Dashboard/dist` exists after build, the default root redirects to `/dashboard/`; otherwise it redirects to `/ui/index.html`.
- The main pipeline returns structured results with `route`, `ner_entities`, `analysis`, and `survival_prediction`.
- The agent loop is limited to a maximum of 3 iterations per request.

## Dashboard Technical Notes
- Built with Vite and React (`Dashboard/package.json`).
- The UI has a landing page and a `MedicalDashboard` component.
- The dashboard is designed to display agent reasoning events and NER graph payloads from the WebSocket.
- The legacy UI is served from `Frontend/` if the dashboard build is unavailable.

## Known Shortcomings
This project is a research-oriented prototype, not production-ready. Key limitations include:
- No authentication, authorization, or user management.
- Limited error handling for model failures and malformed input.
- No automated model download or model version management.
- The pipeline is tightly coupled to available `.h5` models and local `Models/` files.
- No explicit training workflow or reproducible model training scripts included.
- The NER and survival logic are basic and may not generalize to new clinical domains.
- Dashboard and backend are served from the same container, which may not scale well.
- Input type handling is simplistic: text vs image only.
- No built-in rate limiting, logging backend, or observability stack.
- No formal validation for clinical correctness or regulatory compliance.

## Research Use
This repository is best used for prototype evaluation, architecture research, or proof-of-concept demonstration of a multi-agent clinical reasoning system. It should be adapted and hardened before any real clinical deployment.
