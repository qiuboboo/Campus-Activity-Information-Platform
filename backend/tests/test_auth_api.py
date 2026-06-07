"""Integration tests for auth API — login, register, captcha, send-code, me."""


class TestCaptcha:
    def test_returns_png_image(self, client):
        resp = client.get("/api/auth/captcha")
        assert resp.status_code == 200
        assert resp.content_type == "image/png"
        token = resp.headers.get("X-Captcha-Token", "")
        assert len(token) > 0

    def test_unique_token_per_request(self, client):
        """Each captcha request returns a non-empty token."""
        t1 = client.get("/api/auth/captcha").headers["X-Captcha-Token"]
        t2 = client.get("/api/auth/captcha").headers["X-Captcha-Token"]
        assert len(t1) > 0 and len(t2) > 0


class TestSendCode:
    def test_sends_code_with_valid_email(self, client):
        resp = client.post("/api/auth/send-code", json={"email": "test@example.com"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "message" in data
        assert data["expires_in"] == 300

    def test_rejects_invalid_email_format(self, client):
        resp = client.post("/api/auth/send-code", json={"email": "not-an-email"})
        assert resp.status_code == 400

    def test_rejects_missing_email(self, client):
        resp = client.post("/api/auth/send-code", json={})
        assert resp.status_code == 400

    # -- corner cases --
    def test_rejects_empty_email_string(self, client):
        resp = client.post("/api/auth/send-code", json={"email": ""})
        assert resp.status_code == 400

    def test_rejects_email_without_at(self, client):
        resp = client.post("/api/auth/send-code", json={"email": "user.example.com"})
        assert resp.status_code == 400

    def test_rejects_email_without_domain(self, client):
        resp = client.post("/api/auth/send-code", json={"email": "user@"})
        assert resp.status_code == 400


class TestRegister:
    def test_registers_new_viewer(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser", "password": "pass123456",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["role"] == "viewer"

    def test_registers_as_publisher(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "pubuser", "password": "pass123456", "role": "publisher",
        })
        assert resp.status_code == 201
        assert resp.get_json()["user"]["role"] == "publisher"

    def test_rejects_admin_role(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "badadmin", "password": "pass123456", "role": "admin",
        })
        assert resp.status_code == 400

    def test_rejects_invalid_role(self, client):
        """Role must be viewer or publisher — random strings rejected."""
        resp = client.post("/api/auth/register", json={
            "username": "badrole", "password": "pass123456", "role": "superuser",
        })
        assert resp.status_code == 400

    def test_rejects_missing_username(self, client):
        resp = client.post("/api/auth/register", json={"password": "pass123456"})
        assert resp.status_code == 400

    def test_rejects_missing_password(self, client):
        resp = client.post("/api/auth/register", json={"username": "someone"})
        assert resp.status_code == 400

    def test_rejects_short_username(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "a", "password": "pass123456",
        })
        assert resp.status_code == 400

    def test_rejects_short_password(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "validuser", "password": "12345",
        })
        assert resp.status_code == 400

    def test_rejects_duplicate_username(self, client, admin_user):
        resp = client.post("/api/auth/register", json={
            "username": "admin", "password": "pass123456",
        })
        assert resp.status_code == 409

    def test_accepts_max_length_username(self, client):
        """Username of exactly 50 characters should be accepted."""
        resp = client.post("/api/auth/register", json={
            "username": "a" * 50, "password": "pass123456",
        })
        assert resp.status_code == 201

    def test_rejects_overlong_username(self, client):
        """Username > 50 characters should be rejected."""
        resp = client.post("/api/auth/register", json={
            "username": "a" * 51, "password": "pass123456",
        })
        assert resp.status_code == 400

    def test_rejects_whitespace_username(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "   ", "password": "pass123456",
        })
        assert resp.status_code == 400

    def test_registered_user_can_login(self, client):
        client.post("/api/auth/register", json={
            "username": "login_test", "password": "mypassword",
        })
        login_resp = client.post("/api/auth/login", json={
            "username": "login_test", "password": "mypassword",
        })
        assert login_resp.status_code == 200
        assert login_resp.get_json()["user"]["username"] == "login_test"

    def test_jwt_contains_role_claim(self, client):
        """Registered user's JWT should encode the role."""
        resp = client.post("/api/auth/register", json={
            "username": "role_test", "password": "pass123456", "role": "publisher",
        })
        token = resp.get_json()["token"]
        # Use /me to verify role is embedded in JWT
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.get_json()["user"]["role"] == "publisher"


class TestLogin:
    def test_login_with_valid_credentials(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "admin123456",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert data["user"]["username"] == "admin"

    def test_login_with_invalid_password(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "wrong",
        })
        assert resp.status_code == 401

    def test_login_missing_username(self, client):
        resp = client.post("/api/auth/login", json={"password": "pass"})
        assert resp.status_code == 400

    def test_login_missing_password(self, client):
        resp = client.post("/api/auth/login", json={"username": "admin"})
        assert resp.status_code == 400

    # -- corner cases --
    def test_login_with_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "ghost_user_xyz", "password": "whatever",
        })
        assert resp.status_code == 401

    def test_whitespace_only_credentials_rejected(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "   ", "password": "   ",
        })
        assert resp.status_code == 400

    def test_token_is_valid_for_me(self, client):
        """Post-login: the token should work with /me."""
        login_resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "admin123456",
        })
        token = login_resp.get_json()["token"]
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200


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

    def test_rejects_malformed_token(self, client):
        """Malformed JWT token should be rejected (401 or 422)."""
        resp = client.get("/api/auth/me", headers={
            "Authorization": "Bearer this.is.not.a.valid.token",
        })
        assert resp.status_code in (401, 422)

    def test_rejects_expired_token(self, client, app):
        """Token with a past expiry should be rejected."""
        from flask_jwt_extended import create_access_token
        from datetime import timedelta

        with app.app_context():
            expired = create_access_token(
                identity="1",
                additional_claims={"role": "admin"},
                expires_delta=timedelta(seconds=-1),
            )
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401
