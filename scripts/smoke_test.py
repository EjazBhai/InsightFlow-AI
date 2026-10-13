"""Run after the API starts: python scripts/smoke_test.py"""
import urllib.request

for endpoint in ("http://localhost:8000/health/live", "http://localhost:8000/health/ready"):
    with urllib.request.urlopen(endpoint, timeout=5) as response:  # nosec B310 - fixed localhost URLs
        print(endpoint, response.status, response.read().decode())
