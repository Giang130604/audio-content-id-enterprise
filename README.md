# Audio Content ID Enterprise MVP

Enterprise-style audio copyright detection MVP using a three-stage
Filter -> Embed -> Verify pipeline.

## What This Repo Contains

- FastAPI ingestion and review API under `apps/api`
- Worker entrypoints under `apps/workers`
- Shared audio matching package under `packages/audio_id`
- Docker Compose infrastructure under `infra`
- Architecture notes under `docs`
- Unit and integration-style tests under `tests`

## Local Development

```powershell
cd "D:\Copyright Strike Tool"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev,api]
python -m unittest discover -s tests
```

Docker is optional for code tests. Install Docker Desktop before running:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

## Score Policy

- `>= 0.90`: high-confidence match
- `0.70 - 0.89`: human review
- `< 0.70`: no action

## GitHub Remote

Target repository:

```text
https://github.com/Giang130604/audio-content-id-enterprise.git
```
