# API Overview — Campus Activity Platform (Backend Basic Version)

Base URL: `http://127.0.0.1:5000` (development) / `http://<host>/api` (via nginx proxy)

All endpoints return JSON. Endpoints marked `🔒` require authentication (JWT token).  
Endpoints marked `🛡️` require admin role.

## Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | — | Login with `username` + `password`, returns JWT token |
| GET | `/api/auth/me` | 🔒 | Get current user info |

## Posters

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/posters` | 🔒 | List posters; supports `q`, `status`, `page`, `per_page` |
| POST | `/api/posters` | 🔒 | Create poster; `status=published` triggers knowledge graph |
| GET | `/api/posters/{id}` | 🔒 | Get poster detail |
| PUT | `/api/posters/{id}` | 🔒 | Update poster |
| GET | `/api/posters/{id}/related` | 🔒 | Get related posters via knowledge graph |
| GET | `/api/posters/review-queue` | 🛡️ | Review queue; filters: `status`, `source_type`, `duplicate_group_key`; sort: `quality_score` |
| POST | `/api/posters/bulk-review` | 🛡️ | Bulk approve/reject; supports `review_comment` |
| POST | `/api/posters/{id}/review` | 🛡️ | Single poster approve/reject; writes audit log |
| GET | `/api/posters/{id}/duplicates` | 🛡️ | Find duplicates by `source_fingerprint` / `duplicate_group_key` |
| POST | `/api/posters/{id}/merge-source` | 🛡️ | Merge source poster into target |
| POST | `/api/posters/{id}/rebuild-knowledge` | 🛡️ | Rebuild knowledge graph for one poster |

## Knowledge Graph

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/knowledge/nodes` | 🔒 | List knowledge nodes; filters: `q`, `node_type` |
| GET | `/api/knowledge/nodes/{id}` | 🔒 | Node detail with linked posters |
| POST | `/api/knowledge/rebuild` | 🛡️ | Rebuild knowledge for all posters; filters: `status`, `source_type` |

## Search

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/search/internal` | 🔒 | Full-text search across posters and knowledge nodes |

## Data Sources & Crawler

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/data-sources` | 🔒 | List all data sources |
| POST | `/api/data-sources` | 🛡️ | Create data source; fields: `name`, `base_url`, `list_selector`, `content_selector`, `source_level`, `owner`, `notes` |
| GET | `/api/data-sources/{id}` | 🔒 | Get data source detail |
| PUT | `/api/data-sources/{id}` | 🛡️ | Update data source |
| POST | `/api/data-sources/{id}/crawl` | 🛡️ | Trigger crawl (async by default; use `{"sync":true}` for sync) |
| GET | `/api/data-sources/{id}/logs` | 🔒 | Get crawl logs for a data source |

## Async Tasks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/tasks/{task_id}` | 🔒 | Query async task status and result |

## Audit Logs

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/audit-logs` | 🛡️ | List audit logs; filters: `actor_id`, `action`, `target_type`; paginated |

## Export & Demo

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/export/posters.json` | 🛡️ | Export all posters (no raw_text, no secrets) |
| GET | `/api/export/knowledge.json` | 🛡️ | Export all knowledge nodes |
| GET | `/api/export/crawl-report.json` | 🛡️ | Export recent 100 crawl logs |
| GET | `/api/demo/summary` | 🛡️ | Aggregated platform statistics |

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | — | Health check (DB, service status) |

## Quick Start

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://127.0.0.1/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123456"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 2. Health check
curl http://127.0.0.1/api/health

# 3. Demo summary (overview)
curl http://127.0.0.1/api/demo/summary -H "Authorization: Bearer $TOKEN"

# 4. Create a data source
curl -X POST http://127.0.0.1/api/data-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"CSE Activities",
    "base_url":"https://cse.sysu.edu.cn/research/activity",
    "list_selector":".eventitems a[href^=\"/event/\"]",
    "source_level":"official"
  }'

# 5. Async crawl (note the task_id)
curl -X POST http://127.0.0.1/api/data-sources/1/crawl \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{}'

# 6. Check task status (use task_id from step 5)
curl http://127.0.0.1/api/tasks/<task_id> -H "Authorization: Bearer $TOKEN"

# 7. Review queue
curl http://127.0.0.1/api/posters/review-queue?status=draft \
  -H "Authorization: Bearer $TOKEN"

# 8. Bulk review
curl -X POST http://127.0.0.1/api/posters/bulk-review \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"poster_ids":[1,2],"action":"approve"}'

# 9. Search
curl "http://127.0.0.1/api/search/internal?q=讲座" \
  -H "Authorization: Bearer $TOKEN"

# 10. Export
curl http://127.0.0.1/api/demo/summary -H "Authorization: Bearer $TOKEN"
```

## Notable Design Decisions

- **Deduplication**: Two-tier — exact source URL match (skips), content fingerprint match (marks as suspected duplicate with `duplicate_group_key`)
- **Quality Scoring**: 0–100 scale with penalties for missing fields and suspected duplicates; bonus for official sources
- **Audit Trail**: Review, bulk-review, merge, and knowledge rebuild operations are all logged with actor, summary, and metadata
- **Crawl Modes**: Default async (Celery task), sync via `{"sync": true}` for debugging
- **Scheduled Crawl**: Built-in Celery Beat with 12h interval, gated by `ENABLE_SCHEDULED_CRAWL` (default disabled)

## Out of Scope (Basic Version)

- HTTPS / TLS certificates / domain binding
- Frontend pages (beyond API integration)
- OpenClaw / AI-powered extraction
- Multi-tenant / complex role management
- Production monitoring and alerting
- High-concurrency load balancing
