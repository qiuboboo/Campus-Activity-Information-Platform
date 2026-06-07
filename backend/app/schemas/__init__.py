"""Response envelope helpers.

All API responses should use these functions to ensure a uniform structure:

- ``ok()`` — success without data
- ``created(data)`` — 201 with data
- ``data(item)`` — single item
- ``paginated(items, page, per_page, total)`` — paginated list
"""

from flask import jsonify


def ok(message: str = "ok") -> tuple:
    return jsonify({"ok": True, "message": message}), 200


def created(data: dict | None = None) -> tuple:
    body = {"ok": True}
    if data is not None:
        body["item"] = data
    return jsonify(body), 201


def data(item: dict | None) -> tuple:
    return jsonify({"item": item}), 200


def paginated(items: list[dict], *, page: int, per_page: int, total: int) -> tuple:
    return jsonify({
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
    }), 200
