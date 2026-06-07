"""Crawl demo — scrape real university websites into draft posters.

Usage:  cd backend && python ../scripts/crawl_demo.py
"""
import json
import sys

sys.path.insert(0, ".")
from app import create_app
from app.config import Config


class CrawlConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "crawl-demo"
    AUTO_CREATE_TABLES = True
    REDIS_URL = ""


app = create_app(CrawlConfig)

with app.app_context():
    from app.extensions import db
    from app.models import User, DataSource, Poster, CrawlLog
    from app.services.crawler_service import crawl_data_source
    from app.services.bootstrap import ensure_default_admin

    db.create_all()
    ensure_default_admin()
    admin = User.query.filter_by(username="admin").first()

    # ── Data source: SYSU news ──────────────────────────────────────────
    sources = [
        {
            "name": "中山大学新闻网-一线动态",
            "base_url": "https://www.sysu.edu.cn/news/yxdt.htm",
            "list_selector": "a",
            "content_selector": "div.article-content",
            "allowed_domains": "sysu.edu.cn,www.sysu.edu.cn",
        },
        {
            "name": "中山大学药学院-学术讲座",
            "base_url": "https://sps.sysu.edu.cn/event",
            "list_selector": "a",
            "content_selector": "article",
            "allowed_domains": "sysu.edu.cn,sps.sysu.edu.cn",
        },
        {
            "name": "中山大学计算机学院",
            "base_url": "https://cse.sysu.edu.cn/",
            "list_selector": "a",
            "content_selector": "div.article-content,article,div.content",
            "allowed_domains": "sysu.edu.cn,cse.sysu.edu.cn",
        },
    ]

    for spec in sources:
        ds = DataSource(
            name=spec["name"],
            base_url=spec["base_url"],
            list_selector=spec["list_selector"],
            content_selector=spec["content_selector"],
            enabled=True,
            crawl_mode="basic",
            source_level="official",
            allowed_domains=spec["allowed_domains"],
            request_interval=2,
        )
        db.session.add(ds)
        db.session.commit()

        print(f"\n{'='*60}")
        print(f"Crawling: {ds.name}")
        print(f"URL: {ds.base_url}")
        print(f"{'='*60}")

        try:
            result = crawl_data_source(ds.id, admin.id)
            print(f"Result: {json.dumps(result, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")

    # ── Summary ─────────────────────────────────────────────────────────
    drafts = Poster.query.filter_by(source_type="crawl").all()
    print(f"\n{'='*60}")
    print(f"TOTAL DRAFTS CREATED: {len(drafts)}")
    print(f"{'='*60}")

    for p in drafts:
        print(f"\n  [{p.id}] {p.title}")
        print(f"       Summary: {(p.summary or '')[:100]}")
        print(f"       Location: {p.location}")
        print(f"       Organizer: {p.organizer}")
        print(f"       URL: {p.source_url}")
        print(f"       Quality: {p.quality_score}")

    # Save to JSON
    output = [
        {
            "id": p.id,
            "title": p.title,
            "summary": p.summary,
            "location": p.location,
            "organizer": p.organizer,
            "source_url": p.source_url,
            "quality_score": p.quality_score,
        }
        for p in drafts
    ]
    with open("crawl_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(output)} drafts to crawl_output.json")
