# Simple Railway Dockerfile - Backend only with embedded frontend
FROM golang:1.22-alpine AS backend-builder

WORKDIR /app
RUN apk add --no-cache git nodejs npm

# Build frontend first
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci

COPY frontend/ ./
RUN npm run build-only

# Build backend
WORKDIR /app/backend
COPY backend/go.mod backend/go.sum ./
RUN go mod download

COPY backend/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /server ./cmd/server

# Production stage
FROM alpine:3.19
WORKDIR /app

RUN apk --no-cache add ca-certificates tzdata

COPY --from=backend-builder /server ./server
COPY --from=backend-builder /app/frontend/dist ./static

ENV SERVER_PORT=8080
ENV SERVER_HOST=0.0.0.0
ENV STATIC_DIR=/app/static

EXPOSE 8080

CMD ["./server"]
