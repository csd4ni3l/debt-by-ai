Debt by AI is a game where you have to convince an AI to get into debt, or to get you out of it.

The 2 modes are:
- Offensive: You have to convince it to get into debt.
- Defensive: You have to convince ai with a solution to get out of debt.

The game was inspired by Death by AI, a game on Discord, but this game has no affiliation with Discord or any subsidiaries.

# How to run:

## Manual
- Download the code
- install the modules into a venv using `pip install -r requirements.txt` or use `uv sync` to automatically do it for you
- run `app.py`.

## Docker Compose
- Download the code, or just the compose file
- Run `docker compose up -d` in this directory

## Docker CLI
- Run using `docker run --name debt-by-ai -p 8080:8080 -e HOST=0.0.0.0 -e PORT=8080 -e DEBUG_MODE=false -e USE_HACKCLUB_AI=false -e GEMINI_API_KEY=changeme -e FLASK_SECRET_KEY=changeme -e DB_FILE=/app/data.db -v ./data.db:/app/data.db --restart unless-stopped csd4ni3lofficial/debt-by-ai:latest`