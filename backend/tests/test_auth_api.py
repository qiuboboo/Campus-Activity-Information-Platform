"""Integration tests for auth API."""


class TestLogin:
    def test_login_with_valid_credentials(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123456"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert data["user"]["username"] == "admin"

    def test_login_with_invalid_password(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_missing_username(self, client):
        resp = client.post("/api/auth/login", json={"password": "pass"})
        assert resp.status_code == 400

    def test_login_missing_password(self, client):
        resp = client.post("/api/auth/login", json={"username": "admin"})
        assert resp.status_code == 400


class TestMe:
    def test_returns_user_info(self, client, admin_headers):
        resp = client.get("/api/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    def test_returns_401_without_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401
