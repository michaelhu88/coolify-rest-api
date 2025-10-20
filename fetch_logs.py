#!/usr/bin/env python3
"""
Fetch deployment logs by subdomain
"""
import requests
import json
import sys
import argparse

# Deployed API server URL
API_BASE_URL = "http://10.131.1.76:8000"

def fetch_logs(subdomain):
    """Fetch logs for a given subdomain"""
    try:
        url = f"{API_BASE_URL}/api/logs/{subdomain}"
        print(f"Fetching logs for subdomain: {subdomain}")
        print(f"URL: {url}")
        print()

        response = requests.get(url)
        response.raise_for_status()

        result = response.json()

        print("=" * 80)
        print(f"DEPLOYMENT LOGS FOR: {subdomain}.aedify.ai")
        print("=" * 80)
        print(f"App UUID: {result.get('app_uuid')}")
        print()
        print("📋 Logs:")
        print("-" * 80)

        logs = result.get('logs', {})
        if logs:
            print(json.dumps(logs, indent=2))
        else:
            print("No logs available yet.")

        print("-" * 80)

    except requests.HTTPError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"Details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Details: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch deployment logs by subdomain')
    parser.add_argument('subdomain', type=str, help='Subdomain name (e.g., myapp123)')
    args = parser.parse_args()

    fetch_logs(args.subdomain)
