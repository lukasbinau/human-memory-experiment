FROM node:22-alpine AS frontend-build

WORKDIR /build
COPY package*.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY frontend ./frontend
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY hukommelseseksperiment_300_ord.csv ./
COPY --from=frontend-build /build/dist ./dist

ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]