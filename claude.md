# Coolify Deployment API

A FastAPI-based REST API and CLI tool for automating application deployments to Coolify.

## Overview

This project provides two ways to deploy applications to Coolify:
1. **REST API** (`api.py`) - For frontend integration and programmatic access
2. **CLI Tool** (`deploy_to_coolify.py`) - For manual/interactive deployments

## Features

- Create projects and applications in Coolify
- Set environment variables
- Trigger deployments
- Monitor deployment status
- Full orchestration or step-by-step control
- CORS-enabled for frontend integration
- Comprehensive error handling

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
COOLIFY_URL=https://app.coolify.io
API_TOKEN=your_coolify_api_token
DEPLOY_SERVER_UUID=your_server_uuid
DOCKERHUB_IMAGE=your_dockerhub_image
```

**Required Variables:**
- `COOLIFY_URL` - Your Coolify instance URL
- `API_TOKEN` - Coolify API token (get from Keys & Tokens in Coolify dashboard)
- `DEPLOY_SERVER_UUID` - UUID of the server to deploy to
- `DOCKERHUB_IMAGE` - Docker Hub image name for deployments

## Usage

### REST API (`api.py`)

#### Start the API Server

```bash
# Method 1: Run directly
python api.py

# Method 2: Run with uvicorn
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

#### Interactive Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### API Endpoints

##### Root & Health

- `GET /` - API information and available endpoints
- `GET /health` - Health check with configuration status

##### Step-by-Step Deployment

**Step 1: Create Project**
```bash
POST /api/projects

Request:
{
  "name": "MyProject",
  "description": "Optional description"
}

Response:
{
  "uuid": "project-uuid",
  "name": "MyProject",
  "message": "Project created successfully"
}
```

**Step 2: Get Environment**
```bash
GET /api/projects/{project_uuid}/environment

Response:
{
  "environment_uuid": "env-uuid",
  "environment_name": "production",
  "project_uuid": "project-uuid"
}
```

**Step 3: Create Application**
```bash
POST /api/applications

Request:
{
  "project_uuid": "project-uuid",
  "environment_name": "production",
  "git_repository": "https://github.com/user/repo",
  "git_branch": "main",
  "name": "my-app",
  "container_port": 3000,
  "host_port": 3001,
  "build_pack": "nixpacks"
}

Response:
{
  "uuid": "app-uuid",
  "name": "my-app",
  "message": "Application created successfully"
}
```

**Step 4: Set Environment Variables**
```bash
POST /api/applications/{app_uuid}/envs

Request:
{
  "key": "DATABASE_URL",
  "value": "postgres://...",
  "is_preview": false,
  "is_literal": true
}

Response:
{
  "uuid": "env-var-uuid",
  "message": "Environment variable 'DATABASE_URL' set successfully"
}
```

**Step 5: Trigger Deployment**
```bash
POST /api/applications/{app_uuid}/deploy

Response:
{
  "message": "Deployment triggered successfully",
  "uuid": "app-uuid"
}
```

**Step 6: Check Deployment Status**
```bash
GET /api/applications/{app_uuid}/status

Response:
{
  "status": "finished",
  "message": "Deployment completed successfully"
}
```

##### Full Deployment (All Steps)

```bash
POST /api/deploy

Request:
{
  "project_name": "MyProject",
  "git_repository": "https://github.com/user/repo",
  "git_branch": "main",
  "app_name": "my-app",
  "container_port": 3000,
  "host_port": 3001,
  "env_vars": {
    "DATABASE_URL": "postgres://user:pass@host:5432/db",
    "API_KEY": "secret-key",
    "NODE_ENV": "production"
  }
}

Response:
{
  "project_uuid": "project-uuid",
  "environment_uuid": "env-uuid",
  "app_uuid": "app-uuid",
  "app_name": "my-app",
  "deployment_status": "in_progress",
  "coolify_url": "https://app.coolify.io/applications/app-uuid",
  "message": "Full deployment initiated successfully"
}
```

#### Example cURL Requests

**Full Deployment:**
```bash
curl -X POST http://localhost:8000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "MyProject",
    "git_repository": "https://github.com/user/repo",
    "git_branch": "main",
    "container_port": 3000,
    "host_port": 3001,
    "env_vars": {
      "DATABASE_URL": "postgres://...",
      "API_KEY": "secret"
    }
  }'
```

**Create Application Only:**
```bash
curl -X POST http://localhost:8000/api/applications \
  -H "Content-Type: application/json" \
  -d '{
    "project_uuid": "your-project-uuid",
    "environment_name": "production",
    "git_repository": "https://github.com/user/repo",
    "git_branch": "main",
    "name": "my-app",
    "container_port": 3000,
    "host_port": 3001
  }'
```

**Set Environment Variable:**
```bash
curl -X POST http://localhost:8000/api/applications/{app_uuid}/envs \
  -H "Content-Type: application/json" \
  -d '{
    "key": "DATABASE_URL",
    "value": "postgres://..."
  }'
```

### CLI Tool (`deploy_to_coolify.py`)

For interactive deployments with prompts:

```bash
python deploy_to_coolify.py
```

The script will prompt you for:
- GitHub repository URL
- Branch name
- Project name
- Container port
- Host port
- Environment variables (key-value pairs)

The CLI tool then:
1. Creates a new project
2. Gets the environment UUID
3. Creates the application
4. Sets environment variables
5. Triggers deployment
6. Monitors deployment status

## Deployment Flow

Both the API and CLI follow this 6-step process:

```
1. Create Project
   ↓
2. Get Environment UUID
   ↓
3. Create Application (instant_deploy: false)
   ↓
4. Set Environment Variables
   ↓
5. Trigger Manual Deployment
   ↓
6. Monitor Deployment Status
```

### Why Manual Deployment?

The application is created with `instant_deploy: false` because:
- Environment variables need to be injected first
- Coolify needs time to provision the application
- Manual deployment ensures env vars are available during build

## Architecture

### API Structure (`api.py`)

```
api.py
├── Configuration (environment variables)
├── Pydantic Models (request/response validation)
├── FastAPI App Setup
│   └── CORS Middleware
├── Helper Functions
│   ├── coolify_post()
│   ├── coolify_get()
│   └── validate_github_url()
└── Endpoints
    ├── Root & Health
    ├── Step 1-6 (individual)
    └── Full Deployment (orchestrator)
```

### Key Components

**Pydantic Models:**
- Input validation
- API documentation
- Type safety
- Response schemas

**Helper Functions:**
- `coolify_post()` - POST requests to Coolify API
- `coolify_get()` - GET requests to Coolify API
- `validate_github_url()` - Validate and format GitHub URLs

**Error Handling:**
- HTTPException for API errors
- Detailed error responses
- Status code preservation

## Configuration

### Port Mapping

- `container_port` - Port your application runs on inside the container (default: 3000)
- `host_port` - External port to expose on the host machine (default: 3001)

Example: If your app runs on port 8080 internally, use:
```json
{
  "container_port": 8080,
  "host_port": 8080
}
```

### Build Pack

Currently supports:
- `nixpacks` (default)

Nixpacks automatically detects your application type and builds appropriately.

### Environment Variables

Environment variables are set with:
- `is_preview: false` - Not for preview environments
- `is_literal: true` - Values are used as-is (not interpolated)

**Note:** `is_multiline` and `is_shown_once` fields are not supported by the Coolify API.

## Error Handling

The API provides detailed error responses:

```json
{
  "detail": {
    "status_code": 422,
    "detail": {
      "message": "Validation failed.",
      "errors": {
        "field_name": ["Error message"]
      }
    }
  }
}
```

Common errors:
- `400` - Invalid request (e.g., malformed GitHub URL)
- `401` - Authentication failed (check API token)
- `404` - Resource not found (invalid UUID)
- `422` - Validation failed (invalid field values)
- `500` - Internal server error

## Development

### Running in Development Mode

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-reloading when code changes.

### Testing Endpoints

Use the interactive Swagger UI at `http://localhost:8000/docs` to:
- Test endpoints
- View request/response schemas
- Execute API calls with built-in client

### CORS Configuration

The API is configured with permissive CORS for development:
```python
allow_origins=["*"]  # Configure this for production
```

**Production:** Update CORS settings to allow only your frontend domain:
```python
allow_origins=["https://your-frontend-domain.com"]
```

## Troubleshooting

### 422 Error When Setting Environment Variables

**Problem:** Coolify rejects environment variables with validation error.

**Solution:** Ensure you're only sending supported fields:
- ✅ `key`, `value`, `is_preview`, `is_literal`
- ❌ `is_multiline`, `is_shown_once` (not supported)

### Application Not Found After Creation

**Problem:** 404 error when setting environment variables immediately after app creation.

**Solution:** The API includes a 3-second delay after app creation to ensure Coolify provisions the application:
```python
time.sleep(3)
```

If still failing, increase the delay.

### GitHub URL Validation Fails

**Problem:** GitHub URL rejected by validation.

**Solution:** Ensure URL format:
- ✅ `https://github.com/user/repo.git`
- ✅ `https://github.com/user/repo` (automatically adds .git)
- ❌ `github.com/user/repo`
- ❌ `git@github.com:user/repo.git`

### Deployment Status Unknown

**Problem:** Status endpoint returns "unknown" or "no_deployments".

**Solution:**
- Wait a few seconds after triggering deployment
- Check Coolify dashboard for deployment logs
- Verify application UUID is correct

## Production Deployment

### Security Considerations

1. **API Token**: Store securely, never commit to version control
2. **CORS**: Configure allowed origins for production
3. **HTTPS**: Use reverse proxy (nginx, Caddy) with SSL
4. **Rate Limiting**: Add rate limiting middleware
5. **Authentication**: Consider adding API key authentication

### Running in Production

```bash
# Using uvicorn with production settings
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4

# Or use gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py .
COPY .env .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t coolify-api .
docker run -p 8000:8000 --env-file .env coolify-api
```

## API Reference Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/api/projects` | POST | Create project |
| `/api/projects/{uuid}/environment` | GET | Get environment |
| `/api/applications` | POST | Create application |
| `/api/applications/{uuid}/envs` | POST | Set env variable |
| `/api/applications/{uuid}/deploy` | POST | Trigger deployment |
| `/api/applications/{uuid}/status` | GET | Get deployment status |
| `/api/deploy` | POST | Full deployment |

## Contributing

When contributing:
1. Follow existing code structure
2. Add Pydantic models for new endpoints
3. Include error handling
4. Update this documentation

## License

[Specify your license here]

## Support

For issues related to:
- **This API**: Open an issue in this repository
- **Coolify API**: Check [Coolify Documentation](https://coolify.io/docs)
- **Deployment Issues**: Check Coolify dashboard logs

## Changelog

### v1.0.0
- Initial release
- REST API with 6-step deployment process
- Full deployment orchestrator
- CLI tool for interactive deployments
- Environment variable injection
- Deployment monitoring
