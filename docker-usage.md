# Docker Usage for FlashNotify

This document explains how to properly run the FlashNotify application using Docker and Docker Compose.

## Prerequisites

Make sure you have Docker and Docker Compose installed on your system.

## Running the Application

### Using Docker Compose (Recommended)

The easiest way to run the complete FlashNotify application is using Docker Compose:

```bash
# Build and start all services (app, database, redis, nginx)
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

This will start:
- The main application service on port 8000
- PostgreSQL database on port 5432
- Redis server on port 6379
- Nginx reverse proxy on ports 80 and 443

### Accessing the Services

- **FastAPI Application**: http://localhost:8000/docs (API documentation)
- **Flask Application**: http://localhost:80 (through Nginx)
- **Admin Dashboard**: http://localhost/admin (after login)
- **Database**: PostgreSQL on localhost:5432
- **Redis**: On localhost:6379

### Individual Container (Alternative)

If you want to run just the application container:

```bash
# Build the image
docker build -t flashnotify .

# Run the container (note: this won't include DB and Redis)
docker run -p 8000:8000 flashnotify
```

## Environment Variables

The application uses the following environment variables (defined in docker-compose.yml):

- `ENVIRONMENT`: Set to 'dev' for development
- `FASTAPI_PORT`: Port for FastAPI (default: 8000)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SESSION_SECRET`: Secret key for sessions

## Troubleshooting

1. **Port already in use**: Make sure ports 80, 8000, 5432, and 6379 are available
2. **Database connection errors**: Wait for the database container to start before the app container
3. **SSL certificate errors**: The default nginx config expects SSL certificates in the ./ssl directory

## Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (will delete database data)
docker-compose down -v
```

## Development

For development, you can mount the current directory as a volume:

```bash
docker run -p 8000:8000 -v $(pwd):/app flashnotify
```

## Note

The `--flashnotify` flag used in the original attempt does not exist. Docker does not have a built-in flag for this application. Use the methods described above to properly run the FlashNotify application.