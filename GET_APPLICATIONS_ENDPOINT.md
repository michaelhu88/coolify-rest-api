# GET Applications Endpoint

Retrieve all applications from your Coolify instance.

## Endpoint

```
GET /api/applications
```

## Request

```bash
curl -X GET "http://10.131.1.75:8000/api/applications"
```

## Response

Returns an array of application objects with details including:
- `uuid`, `name`, `description`, `status`
- `fqdn` - Fully qualified domain name
- `git_repository`, `git_branch`, `git_commit_sha`
- `build_pack`, `ports_exposes`, `ports_mappings`
- `health_check_*` - Health check configuration
- `created_at`, `updated_at`
- Nested `destination` and `server` objects

### Example Response

```json
[
  {
    "uuid": "vgsccks40oswss4s4s088ogk",
    "name": "my-nextjs-app",
    "status": "running:healthy",
    "fqdn": "https://myapp.example.com",
    "git_repository": "user/repo.git",
    "git_branch": "main",
    "ports_mappings": "3000:3000"
  }
]
```

## Usage

```python
import requests

apps = requests.get("http://10.131.1.75:8000/api/applications").json()

# List all apps
for app in apps:
    print(f"{app['name']}: {app['status']}")

# Find by name
my_app = next((app for app in apps if app['name'] == 'my-app'), None)

# Filter by status
healthy = [app for app in apps if app['status'] == 'running:healthy']
```
