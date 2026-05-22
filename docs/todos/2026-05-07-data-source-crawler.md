# Archived TODO: Data Sources and Basic Crawler Feature Round

Archived after the data source crawler feature and real SYSU CSE crawler verification were completed.

## Result

- Added `DataSource` and `CrawlLog` models.
- Added data source CRUD APIs.
- Added manual crawl API and crawl log API.
- Added basic `requests + BeautifulSoup` crawler.
- Added draft poster generation from crawled pages.
- Added structured field extraction for title, event time, location, and speaker.
- Verified `https://example.com` basic crawl.
- Verified real SYSU CSE activity crawl from `https://cse.sysu.edu.cn/research/activity`.
- Crawled 12 SYSU CSE events successfully.
- Approved one crawled poster and verified knowledge graph generation.
- Verified internal search against crawled activity content.

For the detailed checked list, see repository history at commit `9b41584`.

```bash
git show 9b41584:docs/TODOList.md
```

