# Archived TODO: Backend Basic Version Finalization

Archived after all backend stabilization tasks were completed and verified.

## Result

- **Celery Beat**: Added beat service, 12h crawl schedule, `ENABLE_SCHEDULED_CRAWL` toggle (default off)
- **Backup/Restore**: `scripts/backup_db.sh` (pg_dump, auto-prune 14), `scripts/restore_db.sh` (confirmation guard)
- **Security**: JWT secret non-default, .env not in Git, ports locked down, no hardcoded secrets
- **API Docs**: `docs/APIOverview.md` with all endpoints, auth markers, curl examples
- **Smoke Test**: `scripts/smoke_backend.sh` — 12/12 passing
- **Restart Recovery**: docker-compose down/up — data persisted, all services recovered

For the detailed checked list, see repository history at the finalization commit.
