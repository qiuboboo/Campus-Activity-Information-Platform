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
