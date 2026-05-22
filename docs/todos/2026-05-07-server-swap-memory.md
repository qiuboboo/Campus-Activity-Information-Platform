# Archived TODO: Server Memory Stabilization and Swap Setup

Archived after server swap and memory stabilization were completed.

## Result

- Created a persistent 2GiB swap file at `/swapfile`.
- Persisted swap in `/etc/fstab`.
- Set `vm.swappiness=10`.
- Added Docker Compose `restart: unless-stopped` for API, PostgreSQL, and Redis.
- Rebooted the server and verified swap auto-mounted.
- Verified backend containers recovered and `/api/health` returned OK.
- Triggered the real SYSU CSE crawler after stabilization.
- Observed stable memory usage after crawl:
  - API around `127MiB`
  - PostgreSQL around `51MiB`
  - Redis around `9MiB`
  - Swap remained unused under normal load
- Kept Gunicorn workers at `2` because memory usage was acceptable.
- Did not add Compose memory limits because current usage was low and Docker Compose v1.29 compatibility was a constraint.

For the detailed checked list, see repository history at commit `7d81649`.

```bash
git show 7d81649:docs/TODOList.md
```

