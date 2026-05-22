# API Examples

This document records basic API calls for backend integration and deployment checks.

Set a token first:

```bash
TOKEN="<jwt-token>"
```

## Login

```bash
curl -X POST http://127.0.0.1/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123456"}'
```

## Create Poster

```bash
curl -X POST http://127.0.0.1/api/posters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "校园科技讲座",
    "raw_text": "校园科技讲座将于 2026-05-18 19:00 在图书馆报告厅举行，由计算机学院主办。",
    "summary": "面向全校学生的科技主题讲座。",
    "event_time": "2026-05-18T19:00:00",
    "location": "图书馆报告厅",
    "organizer": "计算机学院",
    "source_type": "manual",
    "source_url": "https://example.edu.cn/events/sample"
  }'
```

## Approve Poster

```bash
curl -X POST http://127.0.0.1/api/posters/1/review \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"approve","comment":"approved for demo"}'
```

## Related Poster Graph

```bash
curl http://127.0.0.1/api/posters/1/related \
  -H "Authorization: Bearer $TOKEN"
```

## Knowledge Nodes

```bash
curl "http://127.0.0.1/api/knowledge/nodes?node_type=place" \
  -H "Authorization: Bearer $TOKEN"
```

```bash
curl http://127.0.0.1/api/knowledge/nodes/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Internal Search

```bash
curl "http://127.0.0.1/api/search/internal?q=校团委" \
  -H "Authorization: Bearer $TOKEN"
```

## Async Crawl (Celery — default)

Default mode submits a Celery task and returns immediately with a `task_id`:

```bash
curl -X POST http://127.0.0.1/api/data-sources/1/crawl \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response:
```json
{
  "task_id": "51b230f7-c188-4ec9-9337-dfa542ccf76b",
  "status_url": "/api/tasks/51b230f7-c188-4ec9-9337-dfa542ccf76b"
}
```

## Query Task Status

```bash
curl http://127.0.0.1/api/tasks/<task_id> \
  -H "Authorization: Bearer $TOKEN"
```

Response when complete:
```json
{
  "task_id": "51b230f7-c188-4ec9-9337-dfa542ccf76b",
  "state": "SUCCESS",
  "result": { "success": true, "posters_created": 5, "pages_found": 12, ... },
  "error": null
}
```

## Sync Crawl (debug mode)

Pass `{"sync": true}` for synchronous execution (blocking call, original behavior):

```bash
curl -X POST http://127.0.0.1/api/data-sources/1/crawl \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sync": true}'
```

> **Note:** The Celery worker runs with `--concurrency=1`. Celery Beat and scheduled tasks are not enabled in this round.
