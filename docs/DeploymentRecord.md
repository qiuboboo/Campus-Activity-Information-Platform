# Deployment Record

This document records repository synchronization and server deployment progress.

## 2026-05-06

### Repository Pull

- Local repository path: `C:\Users\HP\Desktop\软件工程\Campus-Activity-Information-Platform`
- Remote repository: `https://github.com/qiuboboo/Campus-Activity-Information-Platform.git`
- Pull mode: `git pull --ff-only`
- Result: success
- Updated from `34cb269` to `31b06e7`
- Pulled commit: `31b06e7 Complete server deployment and update TODO list`
- Changed files:
  - `backend/Dockerfile`
  - `backend/app/services/bootstrap.py`
  - `docs/TODOList.md`

### Server Deployment Status From TODOList

- Server initial backend deployment is complete.
- Project directory on server: `/home/workspace/Campus-Activity-Information-Platform`
- Python direct run: success
- Docker Compose run: success
- Health check endpoint: success
- Login endpoint: success
- Docker mode database: PostgreSQL
- Python direct-run mode database: SQLite
- Containers confirmed: `api`, `postgres`, `redis`

### Follow-Up Action

`docs/TODOList.md` noted that PostgreSQL and Redis were exposed externally through Docker port mappings. The next local change limits service exposure:

- API is bound to `127.0.0.1:5000` for Nginx reverse proxy access.
- PostgreSQL no longer publishes `5432` to the host.
- Redis no longer publishes `6379` to the host.

After pulling this change on the server, run:

```bash
cd /home/workspace/Campus-Activity-Information-Platform/backend
docker compose down
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:5000/api/health
```

If external access is needed, route requests through Nginx on `80/443` instead of exposing database or cache ports.
