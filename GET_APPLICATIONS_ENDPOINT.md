# GET Applications Endpoint

## Overview

Retrieve all applications from your Coolify instance. This endpoint returns a complete list of applications with detailed information including deployment status, configuration, and server details.

## Endpoint

```
GET /api/applications
```

## Authentication

No authentication required for this wrapper API endpoint. The API handles Coolify authentication internally using the configured `API_TOKEN`.

## Request

### cURL Example

```bash
curl -X GET "http://localhost:8000/api/applications" \
  -H "Accept: application/json"
```

### Python Example

```python
import requests

response = requests.get("http://localhost:8000/api/applications")
applications = response.json()

for app in applications:
    print(f"App: {app['name']} | Status: {app['status']} | UUID: {app['uuid']}")
```

## Response

### Success (200 OK)

Returns an array of application objects. Each application includes:

#### Core Fields
- `uuid` (string) - Unique identifier for the application
- `name` (string) - Application name
- `description` (string|null) - Application description
- `status` (string) - Current status (e.g., "running:healthy", "exited:unhealthy")
- `fqdn` (string|null) - Fully qualified domain name
- `created_at` (string) - Creation timestamp
- `updated_at` (string) - Last update timestamp
- `deleted_at` (string|null) - Deletion timestamp

#### Git Configuration
- `git_repository` (string) - Git repository URL
- `git_branch` (string) - Git branch name
- `git_commit_sha` (string) - Current commit SHA
- `git_full_url` (string|null) - Full git URL

#### Build Configuration
- `build_pack` (string) - Build pack type (e.g., "nixpacks")
- `build_command` (string|null) - Custom build command
- `install_command` (string|null) - Custom install command
- `start_command` (string|null) - Custom start command
- `base_directory` (string) - Base directory for build
- `publish_directory` (string|null) - Publish directory

#### Ports & Network
- `ports_exposes` (string) - Exposed container ports
- `ports_mappings` (string) - Port mappings (e.g., "3000:3000")
- `custom_network_aliases` (string|null) - Custom network aliases

#### Health Checks
- `health_check_enabled` (boolean) - Whether health checks are enabled
- `health_check_path` (string) - Health check endpoint path
- `health_check_port` (string|null) - Port for health checks
- `health_check_method` (string) - HTTP method for health check
- `health_check_return_code` (integer) - Expected return code
- `health_check_scheme` (string) - Protocol (http/https)
- `health_check_interval` (integer) - Check interval in seconds
- `health_check_timeout` (integer) - Timeout in seconds
- `health_check_retries` (integer) - Number of retries
- `health_check_start_period` (integer) - Start period in seconds

#### Resource Limits
- `limits_memory` (string) - Memory limit
- `limits_memory_swap` (string) - Swap memory limit
- `limits_memory_swappiness` (integer) - Swappiness value
- `limits_memory_reservation` (string) - Memory reservation
- `limits_cpus` (string) - CPU limit
- `limits_cpuset` (string|null) - CPU set
- `limits_cpu_shares` (integer) - CPU shares

#### Deployment Configuration
- `environment_id` (integer) - Environment ID
- `destination_id` (integer) - Destination ID
- `destination_type` (string) - Type of destination
- `source_id` (integer) - Source ID
- `source_type` (string) - Type of source
- `private_key_id` (integer) - Private key ID

#### Docker Configuration
- `docker_registry_image_name` (string|null) - Docker registry image
- `docker_registry_image_tag` (string|null) - Docker image tag
- `dockerfile_location` (string|null) - Dockerfile path
- `dockerfile_target_build` (string|null) - Target build stage
- `docker_compose_location` (string) - Docker compose file location
- `custom_docker_run_options` (string|null) - Custom docker run options

#### Additional Configuration
- `redirect` (string) - Redirect configuration
- `custom_labels` (string|null) - Custom Docker labels
- `custom_nginx_configuration` (string) - Custom Nginx config
- `is_http_basic_auth_enabled` (boolean) - Basic auth status
- `http_basic_auth_username` (string|null) - Basic auth username
- `post_deployment_command` (string|null) - Post-deployment command
- `pre_deployment_command` (string|null) - Pre-deployment command
- `watch_paths` (string|null) - Paths to watch for changes

#### Nested Objects
- `destination` (object) - Destination server details including:
  - `id`, `uuid`, `name`, `network`
  - `server` (object) - Full server configuration
    - `proxy` (object) - Proxy settings
    - `settings` (object) - Server settings

### Response Example

```json
[
  {
    "uuid": "vgsccks40oswss4s4s088ogk",
    "name": "my-nextjs-app",
    "description": null,
    "status": "running:healthy",
    "fqdn": "https://myapp.example.com",
    "git_repository": "user/repo.git",
    "git_branch": "main",
    "git_commit_sha": "HEAD",
    "build_pack": "nixpacks",
    "ports_exposes": "3000",
    "ports_mappings": "3000:3000",
    "health_check_enabled": true,
    "health_check_path": "/",
    "health_check_method": "GET",
    "health_check_return_code": 200,
    "limits_memory": "0",
    "limits_cpus": "0",
    "environment_id": 3,
    "created_at": "2025-10-13T19:38:14.000000Z",
    "updated_at": "2025-10-13T19:38:14.000000Z",
    "destination": {
      "id": 4,
      "uuid": "zo8g8w8w40kok0c44k8gs8og",
      "name": "coolify",
      "server": {
        "uuid": "q44484cg0w44wg4sw0ooo808",
        "name": "Deploy Server",
        "ip": "10.131.1.83"
      }
    }
  }
]
```

### Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Unauthorized"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Failed to fetch applications from Coolify"
}
```

## Use Cases

### 1. List All Applications
Retrieve and display all applications with their status:

```python
import requests

response = requests.get("http://localhost:8000/api/applications")
apps = response.json()

print(f"Total applications: {len(apps)}")
for app in apps:
    print(f"- {app['name']}: {app['status']}")
```

### 2. Filter by Status
Find all healthy running applications:

```python
apps = requests.get("http://localhost:8000/api/applications").json()
healthy_apps = [app for app in apps if app['status'] == 'running:healthy']
```

### 3. Get Application by Name
Search for a specific application:

```python
apps = requests.get("http://localhost:8000/api/applications").json()
my_app = next((app for app in apps if app['name'] == 'my-app'), None)
if my_app:
    print(f"Found: {my_app['uuid']}")
```

### 4. Monitor Application Health
Check health status of all applications:

```python
apps = requests.get("http://localhost:8000/api/applications").json()
for app in apps:
    if 'unhealthy' in app['status']:
        print(f"⚠️  {app['name']} is unhealthy!")
    elif 'running' in app['status']:
        print(f"✅ {app['name']} is running")
```

## Notes

- The endpoint proxies directly to Coolify's `/api/v1/applications` endpoint
- Response includes deeply nested objects (destination, server, proxy, settings)
- All timestamps are in ISO 8601 format (UTC)
- Some fields may be `null` if not configured
- The response can be large if you have many applications
- Application status values include:
  - `running:healthy` - Application is running and healthy
  - `running:unhealthy` - Application is running but failing health checks
  - `exited:unhealthy` - Application has stopped
  - Other status values may exist depending on Coolify version

## Related Endpoints

- `POST /api/applications` - Create a new application
- `GET /api/applications/{uuid}/status` - Get deployment status for a specific application
- `POST /api/applications/{uuid}/deploy` - Trigger deployment for a specific application
- `POST /api/applications/{uuid}/envs` - Set environment variables for an application
