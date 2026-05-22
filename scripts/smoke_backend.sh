#!/usr/bin/env bash
# ============================================================
# smoke_backend.sh — Smoke test for Campus Platform Backend
# ============================================================
# Usage:
#   ./scripts/smoke_backend.sh [api_base_url] [admin_user] [admin_pass]
#
# Defaults:
#   API_BASE=http://127.0.0.1:5000
#   ADMIN_USER=admin
#   ADMIN_PASS=admin123456
#
# Exit code: 0 if all tests pass, 1 if any fail.

set -euo pipefail

API_BASE="${1:-http://127.0.0.1:5000}"
ADMIN_USER="${2:-admin}"
ADMIN_PASS="${3:-admin123456}"

PASS=0
FAIL=0

pass() {
    PASS=$((PASS + 1))
}

fail() {
    local msg="$1"
    FAIL=$((FAIL + 1))
    echo "  FAIL: $msg"
}

test_endpoint() {
    local method="$1"
    local path="$2"
    local desc="$3"
    local expected_code="${4:-200}"
    local token="${5:-}"
    local body="${6:-}"

    local full_url="${API_BASE}${path}"
    local headers=(-H "Content-Type: application/json")
    local curl_args=(-s -o /tmp/smoke_response.json -w "%{http_code}")

    if [ -n "$token" ]; then
        headers+=(-H "Authorization: Bearer $token")
    fi

    local http_code
    if [ -n "$body" ]; then
        http_code=$(curl "${curl_args[@]}" -X "$method" "${headers[@]}" -d "$body" "$full_url" 2>/dev/null || echo "000")
    else
        http_code=$(curl "${curl_args[@]}" -X "$method" "${headers[@]}" "$full_url" 2>/dev/null || echo "000")
    fi

    if [ "$http_code" = "$expected_code" ]; then
        echo "  PASS [$http_code] $desc"
        pass
    else
        echo "  FAIL [$http_code] $desc (expected $expected_code)"
        cat /tmp/smoke_response.json 2>/dev/null | head -c 200
        echo ""
        fail "$desc returned $http_code"
    fi
}

echo "============================================"
echo "Smoke Test: Campus Activity Backend"
echo "============================================"
echo "API:    $API_BASE"
echo "User:   $ADMIN_USER"
echo "Date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================"
echo ""

# 1. Health check (no auth)
echo "[01] Health Check"
test_endpoint GET /api/health "Health endpoint"

# 2. Login
echo "[02] Login"
LOGIN_RESP=$(curl -s -X POST "${API_BASE}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}")
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || echo "")
if [ -n "$TOKEN" ]; then
    echo "  PASS Login successful (token obtained)"
    pass
else
    echo "  FAIL Login failed"
    echo "  Response: $LOGIN_RESP"
    fail "Login"
fi

# 3. Demo summary
echo "[03] Demo Summary"
test_endpoint GET /api/demo/summary "Demo summary" 200 "$TOKEN"

# 4. Data sources list
echo "[04] Data Sources List"
test_endpoint GET /api/data-sources "Data sources list" 200 "$TOKEN"

# 5. Review queue
echo "[05] Review Queue"
test_endpoint GET "/api/posters/review-queue?per_page=1" "Review queue" 200 "$TOKEN"

# 6. Search
echo "[06] Search"
test_endpoint GET "/api/search/internal?q=test" "Internal search" 200 "$TOKEN"

# 7. Export posters
echo "[07] Export Posters"
test_endpoint GET /api/export/posters.json "Export posters" 200 "$TOKEN"

# 8. Export knowledge
echo "[08] Export Knowledge"
test_endpoint GET /api/export/knowledge.json "Export knowledge" 200 "$TOKEN"

# 9. Export crawl report
echo "[09] Export Crawl Report"
test_endpoint GET /api/export/crawl-report.json "Export crawl report" 200 "$TOKEN"

# 10. Audit logs
echo "[10] Audit Logs"
test_endpoint GET /api/audit-logs "Audit logs" 200 "$TOKEN"

# 11. Knowledge nodes
echo "[11] Knowledge Nodes"
test_endpoint GET /api/knowledge/nodes "Knowledge nodes" 200 "$TOKEN"

# 12. Auth required (no token should fail)
echo "[12] Auth Required (no token)"
test_endpoint GET /api/demo/summary "No-token rejection" 401 ""

echo ""
echo "============================================"
echo "Results: $PASS passed, $FAIL failed"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
