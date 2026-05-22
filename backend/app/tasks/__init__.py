"""Celery task modules.

All task modules are imported here so that Celery discovers the
``@celery.task``-decorated functions when ``from . import tasks`` is used.
"""

# Import all task modules to register them with Celery
from . import ai_tasks  # noqa: F401 — ai queue: LLM extraction, enrichment
from . import crawl_tasks  # noqa: F401 — crawl queue: web scraping
from . import index_tasks  # noqa: F401 — index queue: embedding generation
