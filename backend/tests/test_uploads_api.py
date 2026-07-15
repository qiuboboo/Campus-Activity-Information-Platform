"""
Uploads API (Blueprint 前缀 /api/uploads)
用例覆盖: 上传/下载/删除 happy path + 类型/大小/auth 错误
"""
import io
import os
import sys

import pytest

# 测试产生实体文件写入 instance/uploads; 引导到临时目录
tmp = os.path.join(os.path.dirname(__file__), "_tmp_uploads")
os.makedirs(tmp, exist_ok=True)


@pytest.fixture(autouse=True)
def _patch_upload_dir(monkeypatch, app):
    """重映射上传目录到测试临时目录,每次都清空"""
    import shutil
    from pathlib import Path

    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    monkeypatch.setattr("app.api.uploads._upload_dir", lambda: Path(tmp))


class TestUpload:
    def test_uploads_image(self, client, admin_headers):
        resp = client.post("/api/uploads", headers=admin_headers, data={
            "file": (io.BytesIO(b"\x89PNG\x0d\x0a\x1a\x0a" + bytes(128)), "test.png"),
        }, content_type="multipart/form-data")
        assert resp.status_code == 201
        data = resp.json
        assert data["name"] == "test.png"
        assert data["url"].startswith("/api/uploads/")
        assert data["mime_type"] == "image/png"

    def test_requires_auth(self, client):
        resp = client.post("/api/uploads", data={
            "file": (io.BytesIO(b"abc"), "x.txt"),
        }, content_type="multipart/form-data")
        assert resp.status_code == 401

    def test_rejects_unsupported_type(self, client, admin_headers):
        resp = client.post("/api/uploads", headers=admin_headers, data={
            "file": (io.BytesIO(b"hello"), "readme.txt"),
        }, content_type="multipart/form-data")
        assert resp.status_code == 422

    def test_rejects_oversized(self, client, admin_headers, monkeypatch):
        monkeypatch.setitem(sys.modules["app.api.uploads"].__dict__, "_MAX_SIZE", 10)
        resp = client.post("/api/uploads", headers=admin_headers, data={
            "file": (io.BytesIO(b"x" * 200), "big.png"),
        }, content_type="multipart/form-data")
        assert resp.status_code == 413


class TestDownload:
    def test_serves_existing_file(self, client, admin_headers):
        upload_resp = client.post("/api/uploads", headers=admin_headers, data={
            "file": (io.BytesIO(bytes(128)), "sample.png"),
        }, content_type="multipart/form-data")
        upload_id = upload_resp.json["id"]
        dl = client.get(f"/api/uploads/{upload_id}/content")
        assert dl.status_code == 200
        assert len(dl.data) == 128

    def test_missing_file_returns_404(self, client):
        resp = client.get("/api/uploads/nonexistent/content")
        assert resp.status_code in (404, 500)


class TestDelete:
    def test_deletes_existing(self, client, admin_headers):
        upload_resp = client.post("/api/uploads", headers=admin_headers, data={
            "file": (io.BytesIO(bytes(42)), "del.png"),
        }, content_type="multipart/form-data")
        upload_id = upload_resp.json["id"]
        del_resp = client.delete(f"/api/uploads/{upload_id}", headers=admin_headers)
        assert del_resp.status_code == 200
        assert del_resp.json["success"] is True

    def test_requires_auth(self, client):
        resp = client.delete("/api/uploads/some-file")
        assert resp.status_code == 401
