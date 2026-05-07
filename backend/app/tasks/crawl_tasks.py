from ..celery_app import celery
from ..config import Config
from ..services.crawler_service import crawl_data_source as _sync_crawl


@celery.task(bind=True, max_retries=0)
def crawl_data_source_task(self, data_source_id: int, user_id: int) -> dict:
    from .. import create_app

    app = create_app(Config)
    with app.app_context():
        try:
            return _sync_crawl(data_source_id, user_id)
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery.task(bind=True, max_retries=0)
def crawl_all_enabled_sources(self) -> list[dict]:
    """Scheduled task: crawl every enabled data source.

    Respects ENABLE_SCHEDULED_CRAWL env var — returns early if disabled.
    """
    from .. import create_app
    from ..models import DataSource, User

    app = create_app(Config)
    with app.app_context():
        if not app.config.get("ENABLE_SCHEDULED_CRAWL", False):
            return [{"info": "scheduled crawl is disabled (ENABLE_SCHEDULED_CRAWL=false)"}]

        sources = DataSource.query.filter_by(enabled=True).all()
        if not sources:
            return [{"info": "no enabled data sources found"}]

        admin = User.query.filter_by(role="admin").order_by(User.id).first()
        if admin is None:
            return [{"error": "no admin user found for scheduled crawl"}]

        user_id = admin.id
        results = []
        for ds in sources:
            try:
                result = _sync_crawl(ds.id, user_id)
                result["data_source_id"] = ds.id
                result["data_source_name"] = ds.name
                results.append(result)
            except Exception as e:
                results.append({
                    "data_source_id": ds.id,
                    "data_source_name": ds.name,
                    "success": False,
                    "error": str(e),
                })
        return results
