from app.extensions import db
from app.models import Poster


def test_admin_can_delete_another_publishers_activity(client, admin_headers, publisher_user):
    poster = Poster(title="待删除活动", raw_text="管理员应能删除此活动", summary="测试", status="draft", source_type="manual", created_by=publisher_user.id)
    db.session.add(poster)
    db.session.commit()
    response = client.delete(f"/api/activities/{poster.id}", headers=admin_headers)
    assert response.status_code == 200
    assert Poster.query.get(poster.id) is None
