# Railway Deployment Guide

This guide will walk you through deploying the Coolify REST API to Railway with PostgreSQL persistence.

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository (already set up: `michaelhu88/coolify-rest-api`)

## Step 1: Create Railway Project

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authenticate with GitHub if needed
5. Select `michaelhu88/coolify-rest-api`

## Step 2: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically:
   - Provision a PostgreSQL instance
   - Set the `DATABASE_URL` environment variable
   - Connect it to your app

## Step 3: Configure Environment Variables

In the Railway dashboard, go to your app's **"Variables"** tab and add:

```
COOLIFY_URL=https://coolify.aedify.ai
API_TOKEN=1|hfvFe134A1OgZNznr2nYh7weJ5RTbn1DJcelkmMw78c34b24
DEPLOY_SERVER_UUID=q44484cg0w44wg4sw0ooo808
DOCKERHUB_IMAGE=meshare1401/coolify-test
```

**Note:** `DATABASE_URL` is automatically set by Railway when you add PostgreSQL.

## Step 4: Deploy

Railway will automatically deploy your app when:
- You push to GitHub (if auto-deploy is enabled)
- You click **"Deploy"** in the Railway dashboard

The deployment process:
1. Railway detects Python app via `requirements.txt`
2. Installs dependencies
3. Runs database migrations (table creation on first startup)
4. Starts the app using the `Procfile` command

## Step 5: Get Your Railway URL

1. Go to **"Settings"** tab in Railway
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. Copy your Railway URL (e.g., `your-app.up.railway.app`)

## Step 6: Update Frontend

Update `index.html` to use your Railway URL instead of localhost:

```javascript
// Change this line:
const response = await fetch('http://localhost:8000/api/deploy', {

// To this (use your actual Railway URL):
const response = await fetch('https://your-app.up.railway.app/api/deploy', {
```

## Verification

Test your deployed API:

```bash
# Health check
curl https://your-app.up.railway.app/health

# Root endpoint
curl https://your-app.up.railway.app/
```

## Port Counter Persistence

The port counter is now stored in PostgreSQL with:
- Atomic transactions (thread-safe)
- Persistent across deployments and restarts
- Row-level locking to prevent race conditions

Database schema:
```sql
CREATE TABLE port_counter (
    id INTEGER PRIMARY KEY DEFAULT 1,
    current_port INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT single_row CHECK (id = 1)
);
```

## Monitoring

Monitor your deployment in Railway:
- **Logs**: View real-time application logs
- **Metrics**: CPU, memory, network usage
- **Database**: Query metrics and connection stats

## Updating Your Deployment

To update your deployed app:

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```
3. Railway will automatically redeploy (if auto-deploy is enabled)

## Troubleshooting

### Port Counter Not Working
- Check that `DATABASE_URL` is set in Railway variables
- View logs for database connection errors
- Ensure PostgreSQL service is running

### Deployment Failed
- Check Railway logs for error messages
- Verify all environment variables are set
- Ensure `requirements.txt` is up to date

### CORS Issues
- The API allows all origins (`*`) by default
- For production, update CORS settings in `api.py`:
  ```python
  allow_origins=["https://your-frontend-domain.com"]
  ```

## Cost

Railway pricing (as of 2024):
- **Free Tier**: $5 worth of usage per month
- **PostgreSQL**: Uses execution time + storage
- **Hobby Plan**: $5/month for more resources

For this simple API, the free tier should be sufficient for development/testing.

## Next Steps

1. Deploy frontend to Vercel/Netlify/Railway
2. Set up custom domain (optional)
3. Add monitoring/alerting
4. Implement API authentication for production use
5. Consider upgrading to Railway Pro for production workloads
