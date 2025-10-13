# Frontend Integration Guide

This guide shows how to integrate your frontend with the Coolify REST API for smooth deployments.

## API Endpoint

**Base URL:** `http://localhost:8000` (development)

**Main Deployment Endpoint:** `POST /api/deploy`

## Frontend Form Fields → API Mapping

Your frontend collects these fields and maps them directly to the API request:

| Frontend Field | API Field | Required | Validation | Example |
|----------------|-----------|----------|------------|---------|
| Project name | `project_name` | ✅ Yes | Letters and numbers only | `MyProject` |
| Aedify subdomain | `subdomain` | ✅ Yes | No special chars/spaces, lowercase | `myapp` |
| GitHub repo URL | `git_repository` | ✅ Yes | Valid GitHub URL | `https://github.com/user/repo` |
| Branch | `git_branch` | ⚪ Optional | Any valid branch name | `main` (default) |
| Base directory | `base_directory` | ⚪ Optional | Format: `/dir/subdir` | `/apps/frontend` |
| Port (internal) | `container_port` | ⚪ Optional | Number | `3000` (default) |
| Port (external) | `host_port` | ⚪ Optional | Number | `3001` (default) |
| ENV variables | `env_vars` | ⚪ Optional | Key-value pairs | `{"KEY": "value"}` |

## Request Format

### Simple Deployment (Minimum Required Fields)

```javascript
const deploymentData = {
  project_name: "MyProject",           // Letters and numbers only
  subdomain: "myapp",                  // Will become myapp.aedify.ai
  git_repository: "https://github.com/user/repo"
};

const response = await fetch('http://localhost:8000/api/deploy', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(deploymentData)
});

const result = await response.json();
```

### Full Deployment (All Fields)

```javascript
const deploymentData = {
  project_name: "MyProject",
  subdomain: "myapp",
  git_repository: "https://github.com/user/repo",
  git_branch: "main",
  base_directory: "/apps/frontend",
  container_port: 3000,
  host_port: 3001,
  env_vars: {
    "DATABASE_URL": "postgres://...",
    "API_KEY": "secret-key",
    "NODE_ENV": "production"
  }
};

const response = await fetch('http://localhost:8000/api/deploy', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(deploymentData)
});

const result = await response.json();
```

## Response Format

### Success Response (200)

```json
{
  "project_uuid": "abc123...",
  "environment_uuid": "def456...",
  "app_uuid": "ghi789...",
  "app_name": "repo",
  "deployment_status": "in_progress",
  "coolify_url": "https://app.coolify.io/applications/ghi789",
  "fqdn": "myapp.aedify.ai",
  "url": "https://myapp.aedify.ai",
  "message": "Full deployment initiated successfully"
}
```

**Key fields to show the user:**
- `url` - The live URL of their deployed app
- `fqdn` - The domain name
- `deployment_status` - Current status
- `coolify_url` - Link to Coolify dashboard

### Error Response (400/422)

```json
{
  "detail": "Subdomain can only contain letters, numbers, and hyphens (no spaces or special characters)"
}
```

## Frontend Validation (Client-Side)

Add these validations in your frontend form **before** sending to the API:

### Project Name
```javascript
function validateProjectName(name) {
  const regex = /^[a-zA-Z0-9]+$/;
  if (!name) return "Project name is required";
  if (!regex.test(name)) return "Project name can only contain letters and numbers";
  return null; // valid
}
```

### Subdomain
```javascript
function validateSubdomain(subdomain) {
  const regex = /^[a-z0-9-]+$/;
  if (!subdomain) return "Subdomain is required";

  // Convert to lowercase and remove spaces
  subdomain = subdomain.toLowerCase().trim();

  if (!regex.test(subdomain)) {
    return "Subdomain can only contain lowercase letters, numbers, and hyphens";
  }

  if (subdomain.startsWith('-') || subdomain.endsWith('-')) {
    return "Subdomain cannot start or end with a hyphen";
  }

  return null; // valid
}
```

### GitHub URL
```javascript
function validateGitHubUrl(url) {
  if (!url) return "GitHub repository URL is required";

  if (!url.startsWith('https://github.com/')) {
    return "Must be a valid GitHub repository URL (https://github.com/...)";
  }

  return null; // valid
}
```

## Environment Variables Form

For the ENV variables section, use a dynamic form that allows users to add multiple key-value pairs:

```javascript
// State management (React example)
const [envVars, setEnvVars] = useState([{ key: '', value: '' }]);

// Add new env var row
const addEnvVar = () => {
  setEnvVars([...envVars, { key: '', value: '' }]);
};

// Remove env var row
const removeEnvVar = (index) => {
  const updated = envVars.filter((_, i) => i !== index);
  setEnvVars(updated);
};

// Update env var
const updateEnvVar = (index, field, value) => {
  const updated = [...envVars];
  updated[index][field] = value;
  setEnvVars(updated);
};

// Convert to API format
const formatEnvVars = (envVars) => {
  const formatted = {};
  envVars.forEach(({ key, value }) => {
    if (key && value) { // Only include if both key and value exist
      formatted[key] = value;
    }
  });
  return Object.keys(formatted).length > 0 ? formatted : null;
};

// When submitting
const deploymentData = {
  project_name: projectName,
  subdomain: subdomain,
  git_repository: gitRepo,
  env_vars: formatEnvVars(envVars) // Only include if there are vars
};
```

## Complete React Example

```jsx
import { useState } from 'react';

function DeploymentForm() {
  const [formData, setFormData] = useState({
    project_name: '',
    subdomain: '',
    git_repository: '',
    git_branch: 'main',
    base_directory: '',
    container_port: 3000,
    host_port: 3001
  });

  const [envVars, setEnvVars] = useState([{ key: '', value: '' }]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Format env vars
      const env_vars = {};
      envVars.forEach(({ key, value }) => {
        if (key && value) {
          env_vars[key] = value;
        }
      });

      // Prepare payload
      const payload = {
        ...formData,
        env_vars: Object.keys(env_vars).length > 0 ? env_vars : undefined
      };

      // Remove empty optional fields
      if (!payload.base_directory) delete payload.base_directory;

      // Make API request
      const response = await fetch('http://localhost:8000/api/deploy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Deployment failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const addEnvVar = () => {
    setEnvVars([...envVars, { key: '', value: '' }]);
  };

  const removeEnvVar = (index) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
  };

  const updateEnvVar = (index, field, value) => {
    const updated = [...envVars];
    updated[index][field] = value;
    setEnvVars(updated);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Project Name */}
      <div>
        <label>Project Name (letters and numbers)</label>
        <input
          type="text"
          value={formData.project_name}
          onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
          pattern="[a-zA-Z0-9]+"
          required
        />
      </div>

      {/* Subdomain */}
      <div>
        <label>Aedify Subdomain (no special characters or spaces)</label>
        <input
          type="text"
          value={formData.subdomain}
          onChange={(e) => setFormData({ ...formData, subdomain: e.target.value.toLowerCase() })}
          pattern="[a-z0-9-]+"
          required
        />
        <small>Your app will be available at: {formData.subdomain || 'subdomain'}.aedify.ai</small>
      </div>

      {/* GitHub Repo */}
      <div>
        <label>GitHub Repository URL</label>
        <input
          type="url"
          value={formData.git_repository}
          onChange={(e) => setFormData({ ...formData, git_repository: e.target.value })}
          placeholder="https://github.com/user/repo"
          required
        />
      </div>

      {/* Branch */}
      <div>
        <label>Branch (default: main)</label>
        <input
          type="text"
          value={formData.git_branch}
          onChange={(e) => setFormData({ ...formData, git_branch: e.target.value })}
        />
      </div>

      {/* Base Directory (Optional) */}
      <div>
        <label>Base Directory (optional)</label>
        <input
          type="text"
          value={formData.base_directory}
          onChange={(e) => setFormData({ ...formData, base_directory: e.target.value })}
          placeholder="/main-directory/sub-directory"
        />
      </div>

      {/* Port Configuration */}
      <div>
        <label>Container Port</label>
        <input
          type="number"
          value={formData.container_port}
          onChange={(e) => setFormData({ ...formData, container_port: parseInt(e.target.value) })}
        />
      </div>

      <div>
        <label>Host Port</label>
        <input
          type="number"
          value={formData.host_port}
          onChange={(e) => setFormData({ ...formData, host_port: parseInt(e.target.value) })}
        />
      </div>

      {/* Environment Variables */}
      <div>
        <label>Environment Variables (optional)</label>
        {envVars.map((envVar, index) => (
          <div key={index} style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
            <input
              type="text"
              placeholder="NAME"
              value={envVar.key}
              onChange={(e) => updateEnvVar(index, 'key', e.target.value)}
            />
            <input
              type="text"
              placeholder="VALUE"
              value={envVar.value}
              onChange={(e) => updateEnvVar(index, 'value', e.target.value)}
            />
            <button type="button" onClick={() => removeEnvVar(index)}>Remove</button>
          </div>
        ))}
        <button type="button" onClick={addEnvVar}>+ Add Environment Variable</button>
      </div>

      {/* Submit */}
      <button type="submit" disabled={loading}>
        {loading ? 'Deploying...' : 'Deploy'}
      </button>

      {/* Error Display */}
      {error && (
        <div style={{ color: 'red' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Success Display */}
      {result && (
        <div style={{ color: 'green' }}>
          <h3>Deployment Initiated!</h3>
          <p><strong>Your app URL:</strong> <a href={result.url} target="_blank">{result.url}</a></p>
          <p><strong>Status:</strong> {result.deployment_status}</p>
          <p><strong>Coolify Dashboard:</strong> <a href={result.coolify_url} target="_blank">View Deployment</a></p>
        </div>
      )}
    </form>
  );
}
```

## Auto-Injected System Variables

The API automatically injects these environment variables (users don't need to provide them):

- `COOLIFY_FQDN` - Set to the full domain (e.g., `myapp.aedify.ai`)
- `URL` - Set to the full HTTPS URL (e.g., `https://myapp.aedify.ai`)

These are available to the application during build and runtime.

## Checking Deployment Status

After deployment is initiated, you can poll for status updates:

```javascript
async function checkDeploymentStatus(appUuid) {
  const response = await fetch(`http://localhost:8000/api/applications/${appUuid}/status`);
  const data = await response.json();
  return data.status; // "finished", "in_progress", "failed", etc.
}

// Poll every 5 seconds
const pollInterval = setInterval(async () => {
  const status = await checkDeploymentStatus(result.app_uuid);

  if (status === 'finished') {
    console.log('Deployment complete!');
    clearInterval(pollInterval);
  } else if (status === 'failed') {
    console.log('Deployment failed');
    clearInterval(pollInterval);
  }
}, 5000);
```

## Error Handling

The API returns clear error messages. Handle these in your frontend:

### Common Errors

| Status Code | Error | Cause | Solution |
|-------------|-------|-------|----------|
| 400 | Invalid project name | Contains special characters | Show validation message |
| 400 | Invalid subdomain | Contains spaces/special chars | Show validation message |
| 400 | Invalid GitHub URL | Not a GitHub repo | Show validation message |
| 401 | Unauthorized | Invalid API token | Check server config |
| 500 | Internal error | Server issue | Show generic error, retry |

### Example Error Handler

```javascript
try {
  const response = await fetch('http://localhost:8000/api/deploy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(deploymentData)
  });

  if (!response.ok) {
    const errorData = await response.json();

    // Extract error message
    let errorMessage = 'Deployment failed';

    if (typeof errorData.detail === 'string') {
      errorMessage = errorData.detail;
    } else if (errorData.detail && errorData.detail.detail) {
      errorMessage = errorData.detail.detail;
    }

    throw new Error(errorMessage);
  }

  const result = await response.json();
  // Handle success
} catch (error) {
  // Show error to user
  setError(error.message);
}
```

## Testing with cURL

Test the API before frontend integration:

```bash
curl -X POST http://localhost:8000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "TestProject",
    "subdomain": "testapp",
    "git_repository": "https://github.com/user/repo",
    "git_branch": "main",
    "env_vars": {
      "API_KEY": "test-key"
    }
  }'
```

## Interactive API Documentation

FastAPI provides interactive documentation at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You can test all endpoints directly from the browser!

## Tips for Smooth Frontend Integration

1. **Validation First**: Validate all inputs on the frontend before sending to API
2. **Loading States**: Show clear loading indicators during deployment
3. **Error Messages**: Display API error messages clearly to users
4. **Auto-lowercase**: Convert subdomain to lowercase automatically in the form
5. **Optional Fields**: Make it clear which fields are optional
6. **URL Preview**: Show the final URL (subdomain.aedify.ai) as user types
7. **Deployment Status**: Poll for status and show progress to user
8. **Success State**: Display the live URL prominently after successful deployment

## Production Considerations

When moving to production:

1. **Update Base URL**: Change from `localhost:8000` to your production API URL
2. **Add Authentication**: Implement API key authentication if needed
3. **Rate Limiting**: Handle rate limit errors gracefully
4. **Timeout Handling**: Set appropriate timeouts for deployment requests
5. **CORS**: Ensure your production domain is allowed in CORS settings
