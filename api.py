#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === CONFIG ===
COOLIFY_URL = os.getenv("COOLIFY_URL")
API_TOKEN = os.getenv("API_TOKEN")
DEPLOY_SERVER_UUID = os.getenv("DEPLOY_SERVER_UUID")
DOCKERHUB_IMAGE = os.getenv("DOCKERHUB_IMAGE")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

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
    project_name: str
    git_repository: str
    git_branch: str = "main"
    app_name: Optional[str] = None
    container_port: int = 3000
    host_port: int = 3001
    env_vars: Optional[Dict[str, str]] = None

class FullDeploymentResponse(BaseModel):
    project_uuid: str
    environment_uuid: str
    app_uuid: str
    app_name: str
    deployment_status: str
    coolify_url: str
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

    # Wait for app to be provisioned
    time.sleep(3)

    return ApplicationCreateResponse(
        uuid=result["uuid"],
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
    """
    try:
        # Step 1: Create project
        project_payload = {
            "name": request.project_name,
            "description": f"Auto-created for {request.app_name or 'application'}"
        }
        project = coolify_post("/api/v1/projects", project_payload)
        project_uuid = project["uuid"]

        # Step 2: Get environment
        proj_info = coolify_get(f"/api/v1/projects/{project_uuid}")
        env = proj_info["environments"][0]
        env_uuid = env["uuid"]
        env_name = env["name"]

        # Step 3: Create application
        git_repo = validate_github_url(request.git_repository)
        app_name = request.app_name or git_repo.split('/')[-1].replace('.git', '')

        app_payload = {
            "project_uuid": project_uuid,
            "server_uuid": DEPLOY_SERVER_UUID,
            "environment_name": env_name,
            "destination_uuid": DEPLOY_SERVER_UUID,
            "git_repository": git_repo,
            "git_branch": request.git_branch,
            "build_pack": "nixpacks",
            "name": app_name,
            "ports_exposes": str(request.container_port),
            "ports_mappings": f"{request.host_port}:{request.container_port}",
            "docker_registry_image_name": DOCKERHUB_IMAGE,
            "instant_deploy": False
        }

        app = coolify_post("/api/v1/applications/public", app_payload)
        app_uuid = app["uuid"]

        # Wait for app to be provisioned
        time.sleep(3)

        # Step 4: Set environment variables
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
                except Exception as e:
                    # Log but continue if env var fails
                    print(f"Warning: Failed to set env var {key}: {str(e)}")

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

        return FullDeploymentResponse(
            project_uuid=project_uuid,
            environment_uuid=env_uuid,
            app_uuid=app_uuid,
            app_name=app_name,
            deployment_status=status,
            coolify_url=f"{COOLIFY_URL}/applications/{app_uuid}",
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
