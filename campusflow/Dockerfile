# Reproducible production image: build React once, serve it and FastAPI together.
FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STUDENTS_DB=/data/students.db
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend-build /build/frontend/dist/ /app/frontend/dist/
WORKDIR /app/backend
EXPOSE 10000
CMD ["sh", "-c", "python bootstrap_demo.py && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
