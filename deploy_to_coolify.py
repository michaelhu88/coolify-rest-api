#!/usr/bin/env python3
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === CONFIG ===
COOLIFY_URL = os.getenv("COOLIFY_URL")
API_TOKEN = os.getenv("API_TOKEN")

BUILD_SERVER_UUID = os.getenv("BUILD_SERVER_UUID")
DEPLOY_SERVER_UUID = os.getenv("DEPLOY_SERVER_UUID")

DOCKERHUB_IMAGE = os.getenv("DOCKERHUB_IMAGE")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def coolify_post(endpoint, payload):
    r = requests.post(f"{COOLIFY_URL}{endpoint}", headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()

def coolify_get(endpoint):
    r = requests.get(f"{COOLIFY_URL}{endpoint}", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def validate_github_url(url):
    """Validate GitHub URL format"""
    if not url.startswith("https://github.com/") and not url.startswith("http://github.com/"):
        raise ValueError("URL must be a GitHub repository (https://github.com/...)")
    if not url.endswith(".git"):
        print("⚠️  Warning: URL doesn't end with .git - adding it automatically")
        return url if url.endswith(".git") else f"{url}.git"
    return url

def poll_deployment_status(app_uuid, timeout=600, poll_interval=5):
    """Poll deployment status until complete or timeout"""
    print("⏳ Monitoring deployment status...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            deployments = coolify_get(f"/api/v1/applications/{app_uuid}/deployments")

            if deployments and len(deployments) > 0:
                latest = deployments[0]
                status = latest.get("status", "unknown")

                if status == "finished":
                    print(f"✅ Deployment completed successfully!")
                    return True
                elif status == "failed":
                    print(f"❌ Deployment failed!")
                    return False
                else:
                    print(f"⏳ Status: {status}... (checking again in {poll_interval}s)")

            time.sleep(poll_interval)
        except Exception as e:
            print(f"⚠️  Error checking status: {e}")
            time.sleep(poll_interval)

    print(f"⏱️  Timeout reached after {timeout}s")
    return False

def main():
    # Validate required environment variables
    required_vars = ["COOLIFY_URL", "API_TOKEN", "BUILD_SERVER_UUID", "DEPLOY_SERVER_UUID", "DOCKERHUB_IMAGE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return

    print("=== Coolify Deployment Script ===")
    repo = input("Enter GitHub repo URL (e.g. https://github.com/user/repo.git): ").strip()
    repo = validate_github_url(repo)

    branch = input("Branch name [default: main]: ").strip() or "main"
    project_name = input("Project name [default: AutoDeploy]: ").strip() or "AutoDeploy"
    app_name = repo.split('/')[-1].replace('.git', '')

    # Get port configuration
    container_port_input = input("Container port [default: 3000]: ").strip()
    container_port = int(container_port_input) if container_port_input else 3000

    host_port_input = input(f"Host port [default: 3001]: ").strip()
    host_port = int(host_port_input) if host_port_input else 3001

    # Get environment variables
    print("\n💡 Add environment variables (press Enter with empty key to finish)")
    env_vars = {}
    while True:
        key = input("  Variable name (or Enter to skip): ").strip()
        if not key:
            break
        value = input(f"  Value for {key}: ").strip()
        env_vars[key] = value

    # 1️⃣ Create project
    print("\n[1] Creating new project...")
    project = coolify_post("/api/v1/projects", {
        "name": project_name,
        "description": f"Auto-created for {app_name}"
    })
    project_uuid = project["uuid"]
    print(f"✅ Project created: {project_name} ({project_uuid})")

    # 2️⃣ Get environment UUID
    print("[2] Fetching environment...")
    proj_info = coolify_get(f"/api/v1/projects/{project_uuid}")
    env_uuid = proj_info["environments"][0]["uuid"]
    print(f"✅ Environment: {env_uuid}")

    # 3️⃣ Create application
    print("[3] Creating application...")
    payload = {
        "project_uuid": project_uuid,
        "server_uuid": DEPLOY_SERVER_UUID,
        "environment_name": proj_info["environments"][0]["name"],
        "destination_uuid": DEPLOY_SERVER_UUID,
        "git_repository": repo,
        "git_branch": branch,
        "build_pack": "nixpacks",
        "name": app_name,
        "ports_exposes": str(container_port),
        "ports_mappings": f"{host_port}:{container_port}",
        "docker_registry_image_name": DOCKERHUB_IMAGE,
        "instant_deploy": False
    }

    app = coolify_post("/api/v1/applications/public", payload)
    app_uuid = app["uuid"]
    print(f"✅ Application created: {app_name} ({app_uuid})")

    # Wait for app to be fully provisioned before setting env vars
    print("⏳ Waiting for application to be fully provisioned...")
    time.sleep(3)

    # 4️⃣ Set environment variables (if provided)
    if env_vars:
        print("[4] Setting environment variables...")
        for key, value in env_vars.items():
            try:
                env_payload = {
                    "key": key,
                    "value": value,
                    "is_preview": False,
                    "is_literal": True
                }
                coolify_post(f"/api/v1/applications/{app_uuid}/envs", env_payload)
                print(f"  ✅ Set {key}")
            except requests.HTTPError as e:
                print(f"  ❌ Failed to set {key}: {e.response.status_code}")
                try:
                    error_detail = e.response.json()
                    print(f"     Details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"     Details: {e.response.text}")
            except Exception as e:
                print(f"  ⚠️  Failed to set {key}: {e}")

    # 5️⃣ Trigger manual deployment
    print("\n[5] Triggering deployment...")
    coolify_post("/api/v1/deploy", {"uuid": app_uuid})
    print("✅ Deployment job enqueued")

    # 6️⃣ Monitor deployment status
    print("\n[6] Monitoring deployment status...")
    poll_deployment_status(app_uuid)

    print(f"\n🎉 View your application in Coolify: {COOLIFY_URL}/applications/{app_uuid}")

if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"❌ API Error: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"Details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Details: {e.response.text}")
    except ValueError as e:
        print(f"❌ Validation Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
