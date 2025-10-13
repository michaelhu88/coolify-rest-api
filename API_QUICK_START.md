# API Quick Start for Frontend

## Base URL
```
http://localhost:8000
```

## Main Endpoint

### Deploy Application
```
POST /api/deploy
```

**Request Body:**
```json
{
  "project_name": "MyProject",
  "subdomain": "myapp",
  "git_repository": "https://github.com/user/repo",
  "git_branch": "main",
  "base_directory": "/apps/web",
  "container_port": 3000,
  "host_port": 3001,
  "env_vars": {
    "API_KEY": "your-key",
    "DATABASE_URL": "postgres://..."
  }
}
```

**Required Fields:**
- `project_name` - Letters and numbers only
- `subdomain` - No spaces/special chars
- `git_repository` - GitHub URL

**Optional Fields:**
- `git_branch` - Default: `"main"`
- `base_directory` - For monorepos
- `container_port` - Default: `3000`
- `host_port` - Default: `3001`
- `env_vars` - Key-value pairs

**Response (200):**
```json
{
  "project_uuid": "abc123",
  "app_uuid": "def456",
  "fqdn": "myapp.aedify.ai",
  "url": "https://myapp.aedify.ai",
  "deployment_status": "in_progress",
  "coolify_url": "https://app.coolify.io/applications/def456",
  "message": "Full deployment initiated successfully"
}
```

**Error (400):**
```json
{
  "detail": "Subdomain can only contain letters, numbers, and hyphens"
}
```

## JavaScript Example

```javascript
const response = await fetch('http://localhost:8000/api/deploy', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_name: "MyProject",
    subdomain: "myapp",
    git_repository: "https://github.com/user/repo",
    env_vars: {
      "API_KEY": "secret"
    }
  })
});

const result = await response.json();
console.log('Deployed to:', result.url);
```

## cURL Example

```bash
curl -X POST http://localhost:8000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "TestProject",
    "subdomain": "testapp",
    "git_repository": "https://github.com/user/repo"
  }'
```

## Interactive Docs

Test the API in your browser:
```
http://localhost:8000/docs
```
