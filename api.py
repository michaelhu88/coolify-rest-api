#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict
import requests
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === CONFIG ===
COOLIFY_URL = os.getenv("COOLIFY_URL")
API_TOKEN = os.getenv("API_TOKEN")
DEPLOY_SERVER_UUID = os.getenv("DEPLOY_SERVER_UUID")
DOCKERHUB_IMAGE = os.getenv("DOCKERHUB_IMAGE")
DATABASE_URL = os.getenv("DATABASE_URL")  # Railway provides this

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Port counter configuration
CONTAINER_PORT = 3000  # Fixed container port
INITIAL_HOST_PORT = 3003  # Starting port for auto-increment

# === PYDANTIC MODELS ===

class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")

class ProjectCreateResponse(BaseModel):
    uuid: str
    name: str
    message: str = "Project created successfully"

class ApplicationCreateRequest(BaseModel):
    project_uuid: str
    environment_name: str
    git_repository: str
    git_branch: str = "main"
    name: str
    container_port: int = 3000
    host_port: int = 3001
    domain: Optional[str] = Field(None, description="User's chosen subdomain (e.g., 'myapp' for myapp.aedify.ai)")
    build_pack: str = "nixpacks"

class ApplicationCreateResponse(BaseModel):
    uuid: str
    name: str
    message: str = "Application created successfully"

class EnvVarRequest(BaseModel):
    key: str
    value: str
    is_preview: bool = False
    is_literal: bool = True

class EnvVarResponse(BaseModel):
    uuid: Optional[str] = None
    message: str = "Environment variable set successfully"

class DeployRequest(BaseModel):
    uuid: str

class DeployResponse(BaseModel):
    message: str = "Deployment triggered successfully"
    uuid: str

class DeploymentStatusResponse(BaseModel):
    status: str
    message: str

class FullDeploymentRequest(BaseModel):
    project_name: str = Field(..., description="Project name (letters and numbers only)")
    subdomain: str = Field(..., description="Aedify subdomain (no special characters or spaces)")
    git_repository: str = Field(..., description="GitHub repository URL")
    git_branch: str = Field(default="main", description="Branch name")
    base_directory: Optional[str] = Field(None, description="Base directory (e.g., /main-directory/sub-directory)")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables as key-value pairs")

class FullDeploymentResponse(BaseModel):
    project_uuid: str
    environment_uuid: str
    app_uuid: str
    app_name: str
    deployment_status: str
    coolify_url: str
    fqdn: str = Field(..., description="Fully qualified domain name")
    url: str = Field(..., description="Full HTTPS URL for the application")
    message: str = "Full deployment completed"

# === FASTAPI APP ===

app = FastAPI(
    title="Coolify Deployment API",
    description="API for deploying applications to Coolify",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    print("🚀 Starting Coolify Deployment API...")
    if DATABASE_URL:
        print("📊 Initializing PostgreSQL port counter...")
        initialize_port_counter()
    else:
        print("⚠️  WARNING: DATABASE_URL not set. Port counter will not work!")
        print("   Set DATABASE_URL environment variable to use PostgreSQL.")

# === HELPER FUNCTIONS ===

def coolify_post(endpoint: str, payload: dict):
    """Make POST request to Coolify API"""
    try:
        url = f"{COOLIFY_URL}{endpoint}"
        r = requests.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        error_detail = {"status_code": e.response.status_code}
        try:
            error_detail["detail"] = e.response.json()
        except:
            error_detail["detail"] = e.response.text
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def coolify_get(endpoint: str):
    """Make GET request to Coolify API"""
    try:
        url = f"{COOLIFY_URL}{endpoint}"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        error_detail = {"status_code": e.response.status_code}
        try:
            error_detail["detail"] = e.response.json()
        except:
            error_detail["detail"] = e.response.text
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def validate_github_url(url: str) -> str:
    """Validate and format GitHub URL"""
    if not url.startswith("https://github.com/") and not url.startswith("http://github.com/"):
        raise HTTPException(status_code=400, detail="URL must be a GitHub repository")
    if not url.endswith(".git"):
        url = f"{url}.git"
    return url

def generate_system_env_vars(domain: str) -> Dict[str, str]:
    """
    Generate system-level environment variables based on user's domain.

    Args:
        domain: User's chosen subdomain (e.g., 'myapp' for myapp.aedify.ai)

    Returns:
        Dict of system environment variables to inject
    """
    # Ensure domain doesn't already include .aedify.ai
    if domain.endswith(".aedify.ai"):
        fqdn = domain
    else:
        fqdn = f"{domain}.aedify.ai"

    return {
        "COOLIFY_FQDN": fqdn,
        "URL": f"https://{fqdn}"
    }

def validate_subdomain(subdomain: str) -> str:
    """
    Validate and sanitize subdomain input.

    Rules:
    - Only letters, numbers, and hyphens
    - No spaces or special characters
    - Convert to lowercase
    - Strip whitespace

    Args:
        subdomain: User's chosen subdomain

    Returns:
        Sanitized subdomain

    Raises:
        HTTPException: If subdomain is invalid
    """
    import re

    # Strip whitespace and convert to lowercase
    subdomain = subdomain.strip().lower()

    # Remove .aedify.ai if user included it
    if subdomain.endswith(".aedify.ai"):
        subdomain = subdomain.replace(".aedify.ai", "")

    # Check if empty after cleaning
    if not subdomain:
        raise HTTPException(status_code=400, detail="Subdomain cannot be empty")

    # Validate format: only letters, numbers, and hyphens
    if not re.match(r'^[a-z0-9-]+$', subdomain):
        raise HTTPException(
            status_code=400,
            detail="Subdomain can only contain letters, numbers, and hyphens (no spaces or special characters)"
        )

    # Cannot start or end with hyphen
    if subdomain.startswith('-') or subdomain.endswith('-'):
        raise HTTPException(status_code=400, detail="Subdomain cannot start or end with a hyphen")

    return subdomain

def validate_project_name(project_name: str) -> str:
    """
    Validate and sanitize project name.

    Rules:
    - Only letters and numbers
    - No special characters or spaces
    - Strip whitespace

    Args:
        project_name: User's chosen project name

    Returns:
        Sanitized project name

    Raises:
        HTTPException: If project name is invalid
    """
    import re

    # Strip whitespace
    project_name = project_name.strip()

    # Check if empty
    if not project_name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty")

    # Validate format: only letters and numbers
    if not re.match(r'^[a-zA-Z0-9]+$', project_name):
        raise HTTPException(
            status_code=400,
            detail="Project name can only contain letters and numbers (no spaces or special characters)"
        )

    return project_name

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Handles connection pooling and cleanup.
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def initialize_port_counter():
    """
    Initialize the port counter table in PostgreSQL if it doesn't exist.
    Creates a table with a single row containing the current port number.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create table if not exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS port_counter (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        current_port INTEGER NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT single_row CHECK (id = 1)
                    )
                """)

                # Insert initial value if table is empty
                cur.execute("""
                    INSERT INTO port_counter (id, current_port)
                    VALUES (1, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (INITIAL_HOST_PORT,))

                conn.commit()
                print(f"✅ Port counter table initialized")
    except Exception as e:
        print(f"⚠️  Port counter initialization error: {e}")
        # If DATABASE_URL is not set, we'll handle it gracefully
        pass

def get_next_port() -> int:
    """
    Atomically get the next available host port and increment the counter.

    Uses PostgreSQL transaction with row-level locking (SELECT FOR UPDATE)
    to ensure thread-safety and prevent race conditions.

    Returns:
        int: The next available host port
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Lock the row and get current port
                cur.execute("""
                    SELECT current_port
                    FROM port_counter
                    WHERE id = 1
                    FOR UPDATE
                """)

                result = cur.fetchone()
                if not result:
                    raise HTTPException(
                        status_code=500,
                        detail="Port counter not initialized. Please contact admin."
                    )

                current_port = result[0]

                # Increment for next use
                next_port = current_port + 1

                cur.execute("""
                    UPDATE port_counter
                    SET current_port = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (next_port,))

                conn.commit()
                print(f"🔢 Assigned port: {current_port} (next will be {next_port})")

                return current_port

    except psycopg2.Error as e:
        print(f"❌ Database error in get_next_port: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to allocate port: Database error"
        )
    except Exception as e:
        print(f"❌ Error in get_next_port: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to allocate port: {str(e)}"
        )

# === ENDPOINTS ===

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Coolify Deployment API",
        "version": "1.0.0",
        "endpoints": {
            "create_project": "POST /api/projects",
            "get_environment": "GET /api/projects/{uuid}/environment",
            "get_all_applications": "GET /api/applications",
            "create_application": "POST /api/applications",
            "set_env_var": "POST /api/applications/{uuid}/envs",
            "deploy": "POST /api/applications/{uuid}/deploy",
            "deployment_status": "GET /api/applications/{uuid}/status",
            "full_deployment": "POST /api/deploy"
        }
    }

@app.post("/api/projects", response_model=ProjectCreateResponse)
def create_project(request: ProjectCreateRequest):
    """Step 1: Create a new project"""
    payload = {
        "name": request.name,
        "description": request.description or f"Auto-created project: {request.name}"
    }
    result = coolify_post("/api/v1/projects", payload)

    # Handle Coolify API returning a list of all projects instead of just the created one
    if isinstance(result, list):
        # Find the project by name (most recently created with this name)
        matching_projects = [p for p in result if p.get("name") == request.name]
        if matching_projects:
            # Get the last one (most recent)
            result = matching_projects[-1]
        else:
            # Fallback: assume the last project in the list is the newly created one
            result = result[-1]

    return ProjectCreateResponse(
        uuid=result["uuid"],
        name=result.get("name", request.name)
    )

@app.get("/api/projects/{project_uuid}/environment")
def get_environment(project_uuid: str):
    """Step 2: Get environment UUID for a project"""
    proj_info = coolify_get(f"/api/v1/projects/{project_uuid}")
    if not proj_info.get("environments") or len(proj_info["environments"]) == 0:
        raise HTTPException(status_code=404, detail="No environments found for project")

    env = proj_info["environments"][0]
    return {
        "environment_uuid": env["uuid"],
        "environment_name": env["name"],
        "project_uuid": project_uuid
    }

@app.get("/api/applications")
def get_all_applications():
    """Get all applications from Coolify"""
    return coolify_get("/api/v1/applications")

@app.post("/api/applications", response_model=ApplicationCreateResponse)
def create_application(request: ApplicationCreateRequest):
    """Step 3: Create a new application"""
    # Validate GitHub URL
    git_repo = validate_github_url(request.git_repository)

    payload = {
        "project_uuid": request.project_uuid,
        "server_uuid": DEPLOY_SERVER_UUID,
        "environment_name": request.environment_name,
        "destination_uuid": DEPLOY_SERVER_UUID,
        "git_repository": git_repo,
        "git_branch": request.git_branch,
        "build_pack": request.build_pack,
        "name": request.name,
        "ports_exposes": str(request.container_port),
        "ports_mappings": f"{request.host_port}:{request.container_port}",
        "docker_registry_image_name": DOCKERHUB_IMAGE,
        "instant_deploy": False
    }

    result = coolify_post("/api/v1/applications/public", payload)
    app_uuid = result["uuid"]

    # Wait for app to be provisioned
    time.sleep(3)

    # If domain is provided, inject system env vars
    if request.domain:
        system_env_vars = generate_system_env_vars(request.domain)
        for key, value in system_env_vars.items():
            env_payload = {
                "key": key,
                "value": value,
                "is_preview": False,
                "is_literal": True
            }
            try:
                coolify_post(f"/api/v1/applications/{app_uuid}/envs", env_payload)
                print(f"✅ System env var set: {key} = {value}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to set system env var {key}: {str(e)}")

    return ApplicationCreateResponse(
        uuid=app_uuid,
        name=result.get("name", request.name)
    )

@app.post("/api/applications/{app_uuid}/envs", response_model=EnvVarResponse)
def set_environment_variable(app_uuid: str, request: EnvVarRequest):
    """Step 4: Set an environment variable for an application"""
    payload = {
        "key": request.key,
        "value": request.value,
        "is_preview": request.is_preview,
        "is_literal": request.is_literal
    }

    result = coolify_post(f"/api/v1/applications/{app_uuid}/envs", payload)
    return EnvVarResponse(
        uuid=result.get("uuid"),
        message=f"Environment variable '{request.key}' set successfully"
    )

@app.post("/api/applications/{app_uuid}/deploy", response_model=DeployResponse)
def trigger_deployment(app_uuid: str):
    """Step 5: Trigger manual deployment"""
    payload = {"uuid": app_uuid}
    coolify_post("/api/v1/deploy", payload)
    return DeployResponse(
        uuid=app_uuid,
        message="Deployment triggered successfully"
    )

@app.get("/api/applications/{app_uuid}/status", response_model=DeploymentStatusResponse)
def get_deployment_status(app_uuid: str):
    """Step 6: Get deployment status"""
    try:
        deployments = coolify_get(f"/api/v1/applications/{app_uuid}/deployments")

        if not deployments or len(deployments) == 0:
            return DeploymentStatusResponse(
                status="no_deployments",
                message="No deployments found for this application"
            )

        latest = deployments[0]
        status = latest.get("status", "unknown")

        status_messages = {
            "finished": "Deployment completed successfully",
            "failed": "Deployment failed",
            "in_progress": "Deployment in progress",
            "queued": "Deployment queued"
        }

        return DeploymentStatusResponse(
            status=status,
            message=status_messages.get(status, f"Deployment status: {status}")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment status: {str(e)}")

@app.post("/api/deploy", response_model=FullDeploymentResponse)
def full_deployment(request: FullDeploymentRequest):
    """
    Complete deployment flow: Creates project, app, sets env vars, and deploys

    Matches frontend flow:
    - Project name (letters and numbers)
    - Aedify subdomain (no special characters or spaces)
    - GitHub repo URL
    - Base directory and branch (if needed)
    - ENV variables (optional key-value pairs)
    """
    try:
        # Validate and sanitize inputs
        project_name = validate_project_name(request.project_name)
        subdomain = validate_subdomain(request.subdomain)
        git_repo = validate_github_url(request.git_repository)

        # Generate app name from repo if not provided
        app_name = git_repo.split('/')[-1].replace('.git', '')

        # Get next available port (auto-increment)
        host_port = get_next_port()

        # Step 1: Create project
        project_payload = {
            "name": project_name,
            "description": f"Auto-created for {app_name}"
        }
        project = coolify_post("/api/v1/projects", project_payload)

        # Handle Coolify API returning a list of all projects instead of just the created one
        if isinstance(project, list):
            # Find the project by name (most recently created with this name)
            matching_projects = [p for p in project if p.get("name") == project_name]
            if matching_projects:
                # Get the last one (most recent)
                project = matching_projects[-1]
            else:
                # Fallback: assume the last project in the list is the newly created one
                project = project[-1]

        project_uuid = project["uuid"]

        # Step 2: Get environment
        proj_info = coolify_get(f"/api/v1/projects/{project_uuid}")
        env = proj_info["environments"][0]
        env_uuid = env["uuid"]
        env_name = env["name"]

        # Step 3: Create application
        app_payload = {
            "project_uuid": project_uuid,
            "server_uuid": DEPLOY_SERVER_UUID,
            "environment_name": env_name,
            "destination_uuid": DEPLOY_SERVER_UUID,
            "git_repository": git_repo,
            "git_branch": request.git_branch,
            "build_pack": "nixpacks",
            "name": app_name,
            "ports_exposes": str(CONTAINER_PORT),
            "ports_mappings": f"{host_port}:{CONTAINER_PORT}",
            "docker_registry_image_name": DOCKERHUB_IMAGE,
            "instant_deploy": False
        }

        # Add base_directory if provided
        if request.base_directory:
            app_payload["base_directory"] = request.base_directory

        app = coolify_post("/api/v1/applications/public", app_payload)
        app_uuid = app["uuid"]

        # Wait for app to be provisioned
        time.sleep(3)

        # Step 4: Set environment variables
        # First, inject system-level env vars (COOLIFY_FQDN and URL)
        system_env_vars = generate_system_env_vars(subdomain)

        for key, value in system_env_vars.items():
            env_payload = {
                "key": key,
                "value": value,
                "is_preview": False,
                "is_literal": True
            }
            try:
                coolify_post(f"/api/v1/applications/{app_uuid}/envs", env_payload)
                print(f"✅ System env var set: {key} = {value}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to set system env var {key}: {str(e)}")

        # Then, inject user-provided env vars
        if request.env_vars:
            for key, value in request.env_vars.items():
                env_payload = {
                    "key": key,
                    "value": value,
                    "is_preview": False,
                    "is_literal": True
                }
                try:
                    coolify_post(f"/api/v1/applications/{app_uuid}/envs", env_payload)
                    print(f"✅ User env var set: {key}")
                except Exception as e:
                    # Log but continue if env var fails
                    print(f"⚠️  Warning: Failed to set user env var {key}: {str(e)}")

        # Step 5: Trigger deployment
        deploy_payload = {"uuid": app_uuid}
        coolify_post("/api/v1/deploy", deploy_payload)

        # Step 6: Check initial deployment status
        time.sleep(2)
        try:
            deployments = coolify_get(f"/api/v1/applications/{app_uuid}/deployments")
            status = deployments[0].get("status", "unknown") if deployments else "queued"
        except:
            status = "unknown"

        # Get the generated system env vars for response
        system_env_vars = generate_system_env_vars(subdomain)

        return FullDeploymentResponse(
            project_uuid=project_uuid,
            environment_uuid=env_uuid,
            app_uuid=app_uuid,
            app_name=app_name,
            deployment_status=status,
            coolify_url=f"{COOLIFY_URL}/applications/{app_uuid}",
            fqdn=system_env_vars["COOLIFY_FQDN"],
            url=system_env_vars["URL"],
            message="Full deployment initiated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

# === HEALTH CHECK ===

@app.get("/health")
def health_check():
    """Health check endpoint"""
    config_status = {
        "coolify_url": bool(COOLIFY_URL),
        "api_token": bool(API_TOKEN),
        "deploy_server_uuid": bool(DEPLOY_SERVER_UUID),
        "dockerhub_image": bool(DOCKERHUB_IMAGE)
    }

    all_configured = all(config_status.values())

    return {
        "status": "healthy" if all_configured else "misconfigured",
        "config": config_status
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Railway provides PORT env variable
    uvicorn.run(app, host="0.0.0.0", port=port)
