"""Regression coverage for activity-facing frontend contracts."""


def test_guest_draft_list_is_forbidden(client, sample_poster):
    response = client.get("/api/activities?status=draft")
    assert response.status_code == 403


def test_registration_csv_and_calendar_are_kept_in_sync(client, viewer_headers, admin_headers, sample_published_poster):
    activity_id = sample_published_poster.id
    form = {"name": "测试用户", "student_id": "20260001", "college": "计算机学院", "email": "viewer@example.com"}
    registered = client.post(f"/api/activities/{activity_id}/register", json=form, headers=viewer_headers)
    assert registered.status_code == 200
    assert registered.get_json()["already_registered"] is False

    calendar = client.get("/api/calendar/events", headers=viewer_headers).get_json()
    assert any(event["activity_id"] == activity_id for event in calendar["events"])
    csv_file = client.get(f"/api/activities/{activity_id}/registrations.csv", headers=admin_headers)
    assert csv_file.status_code == 200
    assert b"viewer@example.com" in csv_file.data

    cancelled = client.delete(f"/api/activities/{activity_id}/register", headers=viewer_headers)
    assert cancelled.status_code == 200
    calendar = client.get("/api/calendar/events", headers=viewer_headers).get_json()
    assert all(event["activity_id"] != activity_id for event in calendar["events"])
