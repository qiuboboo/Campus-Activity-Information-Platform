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

### Server GitHub SSH Key

The server has generated an SSH key for the `workspace` user and the public key has been added to GitHub with the title `campus-platform-server`.

Public key:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKdyA2pgOY1gGo8SRVR19nhLVZ5yJI00b3iIwi9luw+l workspace@campus-platform
```

After confirming GitHub accepts the key, the server repository should use the SSH remote:

```bash
cd /home/workspace/Campus-Activity-Information-Platform
git remote set-url origin git@github.com:qiuboboo/Campus-Activity-Information-Platform.git
ssh -T git@github.com
git pull --ff-only
```

Expected SSH test output:

```text
Hi qiuboboo! You've successfully authenticated, but GitHub does not provide shell access.
```

If `ssh -T git@github.com` waits forever, check outbound access from the server to GitHub port `22`. As a fallback, test GitHub's SSH-over-HTTPS endpoint:

```bash
ssh -T -p 443 git@ssh.github.com
```

If port `443` works but port `22` does not, add this to `/home/workspace/.ssh/config`:

```sshconfig
Host github.com
    HostName ssh.github.com
    User git
    Port 443
```

## 2026-05-06 (Round 2 — Server Hardening & Nginx)

### Pulled Commit

- From: `31b06e7` → To: `47fe627`
- Pulled changes: Docker port lockdown, new TODO list, DeploymentRecord.md

### Docker Port Convergence

- Applied updated `docker-compose.yml`:
  - `api` port mapping: `127.0.0.1:5000:5000` (localhost only)
  - `postgres`: removed host port mapping (internal only)
  - `redis`: removed host port mapping (internal only)
- Restarted with `docker-compose down && docker-compose up -d --build`
- All 3 containers running successfully
- Port check: only `127.0.0.1:5000` listening on host

### Nginx Reverse Proxy

- Installed nginx 1.18.0 via apt
- Deployed config from `deploy/nginx/campus-activity.conf`
- Verified: `curl http://127.0.0.1/api/health` returns `{"status":"ok"}`

### Next Steps

- Evaluate domain name and HTTPS setup
- Begin frontend-backend integration

## 2026-05-06 (Round 3 - Backend Knowledge Graph)

### Scope

- HTTPS, domain binding, OpenClaw, and vector search are intentionally deferred.
- This round focuses on backend knowledge graph features from `docs/后端技术文档.md`.

### Implemented Locally

- Added knowledge node, poster-node, and poster-link models.
- Added rule-based knowledge node generation from poster fields.
- Added rule-based poster relation generation.
- Added `GET /api/posters/{id}/related`.
- Added knowledge node query endpoints under `/api/knowledge`.
- Added keyword internal search under `/api/search/internal`.
- Updated demo seed data for related poster scenarios.
- Added `docs/APIExamples.md`.
- Local verification: `python -m compileall backend` passed.
- Runtime API verification is left for the server Docker environment because local Flask dependencies are not installed.

### Server Verification

- Pulled `289aebb` and restarted Docker (`docker-compose down && up -d --build`)
- Health check: `{"status":"ok"}`
- Login: JWT token returned
- Demo data seeded: 3 posters + 12 knowledge nodes generated
- `GET /api/posters/1/related`: Poster 1 linked to Poster 2 (same_day, same_place, same_topic), Poster 3 (same_org)
- `GET /api/knowledge/nodes`: 12 nodes returned (time, place, organization, topic, source)
- `GET /api/knowledge/nodes/1`: Node detail with 2 linked posters
- `GET /api/search/internal?q=校园`: 2 poster hits returned

### Fix Applied During Deployment

- Gunicorn multi-worker `db.create_all()` race condition caused `UniqueViolation` on PostgreSQL internal `pg_type` catalog.
- Moved database initialization from `create_app()` into gunicorn `on_starting` hook with `preload_app=True`.
- `wsgi.py` still calls `init_database()` for single-process direct-run compatibility.
