"""Integration tests for calendar API (ICS download + personal calendar)."""


class TestIcsDownload:
    def test_returns_404_for_unpublished(self, client, sample_poster):
        """Only published posters can be downloaded as ICS."""
        resp = client.get(f"/api/posters/{sample_poster.id}/ics")
        # sample_poster has status='draft'
        assert resp.status_code == 404

    def test_returns_ics_for_published(self, client, sample_published_poster):
        resp = client.get(f"/api/posters/{sample_published_poster.id}/ics")
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/calendar")
        assert b"BEGIN:VCALENDAR" in resp.data
        assert b"BEGIN:VEVENT" in resp.data
        assert b"SUMMARY" in resp.data
        assert resp.headers["Content-Disposition"].startswith("attachment")

    def test_returns_404_for_missing_poster(self, client):
        resp = client.get("/api/posters/99999/ics")
        assert resp.status_code == 404


class TestAddCalendarEvent:
    def test_adds_event_successfully(self, client, admin_headers, sample_published_poster):
        resp = client.post(
            "/api/calendar/events",
            json={"poster_id": sample_published_poster.id},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "item" in data
        assert data["item"]["poster_id"] == sample_published_poster.id

    def test_returns_404_for_unpublished(self, client, admin_headers, sample_poster):
        resp = client.post(
            "/api/calendar/events",
            json={"poster_id": sample_poster.id},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_idempotent_add(self, client, admin_headers, sample_published_poster):
        """Adding same poster twice returns the existing event (200)."""
        resp1 = client.post(
            "/api/calendar/events",
            json={"poster_id": sample_published_poster.id},
            headers=admin_headers,
        )
        assert resp1.status_code == 201
        resp2 = client.post(
            "/api/calendar/events",
            json={"poster_id": sample_published_poster.id},
            headers=admin_headers,
        )
        assert resp2.status_code == 200

    def test_requires_auth(self, client, sample_published_poster):
        resp = client.post(
            "/api/calendar/events",
            json={"poster_id": sample_published_poster.id},
        )
        assert resp.status_code == 401


class TestListCalendarEvents:
    def test_returns_empty_for_new_user(self, client, admin_headers):
        resp = client.get("/api/calendar/events", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_added_events(self, client, admin_headers, sample_published_poster):
        client.post(
            "/api/calendar/events",
            json={"poster_id": sample_published_poster.id},
            headers=admin_headers,
        )
        resp = client.get("/api/calendar/events", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["poster_id"] == sample_published_poster.id

    def test_requires_auth(self, client):
        resp = client.get("/api/calendar/events")
        assert resp.status_code == 401


class TestRemoveCalendarEvent:
    def test_removes_added_event(self, client, admin_headers, sample_published_poster):
        client.post(
            "/api/calendar/events",
            json={"poster_id": sample_published_poster.id},
            headers=admin_headers,
        )
        resp = client.delete(
            f"/api/calendar/events/{sample_published_poster.id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        # Verify removed
        resp2 = client.get("/api/calendar/events", headers=admin_headers)
        assert resp2.get_json()["total"] == 0

    def test_returns_404_for_nonexistent(self, client, admin_headers):
        resp = client.delete("/api/calendar/events/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_requires_auth(self, client, sample_published_poster):
        resp = client.delete(f"/api/calendar/events/{sample_published_poster.id}")
        assert resp.status_code == 401


# =============================================================================
# Corner-case / edge-condition tests
# =============================================================================


class TestCalendarUserIsolation:
    def test_admin_events_not_visible_to_viewer(self, client, admin_headers, viewer_headers,
                                                  sample_published_poster):
        """Calendar events are per-user — one user's events don't leak to another."""
        # Admin adds event
        client.post("/api/calendar/events",
                    json={"poster_id": sample_published_poster.id},
                    headers=admin_headers)
        # Viewer sees empty list
        r = client.get("/api/calendar/events", headers=viewer_headers)
        assert r.status_code == 200
        assert r.get_json()["total"] == 0

    def test_cannot_remove_others_event(self, client, admin_headers, viewer_headers,
                                         sample_published_poster):
        """User cannot remove another user's calendar event."""
        client.post("/api/calendar/events",
                    json={"poster_id": sample_published_poster.id},
                    headers=admin_headers)
        r = client.delete(f"/api/calendar/events/{sample_published_poster.id}",
                          headers=viewer_headers)
        assert r.status_code == 404


class TestCalendarAddEdgeCases:
    def test_missing_poster_id(self, client, admin_headers):
        r = client.post("/api/calendar/events", json={}, headers=admin_headers)
        assert r.status_code == 400

    def test_nonexistent_poster(self, client, admin_headers):
        r = client.post("/api/calendar/events",
                        json={"poster_id": 99999}, headers=admin_headers)
        assert r.status_code == 404

    def test_publisher_can_add_event(self, client, publisher_headers, sample_published_poster):
        r = client.post("/api/calendar/events",
                        json={"poster_id": sample_published_poster.id},
                        headers=publisher_headers)
        assert r.status_code == 201


class TestIcsContent:
    def test_ics_contains_poster_title(self, client, sample_published_poster):
        """The generated .ics file should embed the poster title in SUMMARY."""
        r = client.get(f"/api/posters/{sample_published_poster.id}/ics")
        assert r.status_code == 200
        # ICS SUMMARY should contain the poster title
        assert sample_published_poster.title.encode() in r.data

    def test_ics_has_correct_filename_header(self, client, sample_published_poster):
        r = client.get(f"/api/posters/{sample_published_poster.id}/ics")
        expected = f'attachment; filename="activity-{sample_published_poster.id}.ics"'
        assert r.headers["Content-Disposition"] == expected
