from typing import List, Dict, Any


FEED_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "google_news_in",
        "name": "Google News India Equities",
        "type": "rss",
        "url_template": "https://news.google.com/rss/search?q={query}+share+price+NSE&hl=en-IN&gl=IN&ceid=IN:en",
        "licensing": "Publicly syndicated RSS headlines and excerpts for financial research indexing.",
        "max_items": 15,
    },
    {
        "id": "economic_times_rss",
        "name": "Economic Times Markets",
        "type": "rss",
        "url_template": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "licensing": "Permitted public RSS feed.",
        "max_items": 20,
    },
    {
        "id": "moneycontrol_rss",
        "name": "Moneycontrol Markets",
        "type": "rss",
        "url_template": "https://www.moneycontrol.com/rss/marketreports.xml",
        "licensing": "Permitted public RSS feed.",
        "max_items": 20,
    }
]

