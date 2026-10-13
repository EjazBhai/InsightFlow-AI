# Deployment

Local Docker Compose is the supported deployment path. Run `docker compose up --build`, then visit ports 8501 (dashboard) and 8000 (API). The compose configuration does not start Ollama so a dashboard remains usable on modest hardware. A hosted model endpoint requires separate credentials supplied through environment variables; no hosted deployment has been verified.
