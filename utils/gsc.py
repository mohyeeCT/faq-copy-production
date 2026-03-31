from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def get_gsc_client(sa_info: dict):
    creds = Credentials.from_service_account_info(sa_info, scopes=GSC_SCOPES)
    return build("searchconsole", "v1", credentials=creds)


def get_top_queries_for_url(gsc_client, site_url: str, page_url: str, top_n: int = 10) -> list:
    """Pull top N queries for a given URL from GSC (90-day window).
    Returns list of dicts: query, clicks, impressions, ctr, position.
    Returns [{"_error": "..."}] on failure so callers can surface errors.
    """
    end_date = datetime.today() - timedelta(days=3)
    start_date = end_date - timedelta(days=90)

    try:
        response = gsc_client.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "dimensions": ["query"],
                "dimensionFilterGroups": [{
                    "filters": [{
                        "dimension": "page",
                        "operator": "equals",
                        "expression": page_url
                    }]
                }],
                "rowLimit": top_n,
                "orderBy": [{"fieldName": "impressions", "sortOrder": "DESCENDING"}]
            }
        ).execute()

        rows = response.get("rows", [])
        return [
            {
                "query": r["keys"][0],
                "clicks": r.get("clicks", 0),
                "impressions": r.get("impressions", 0),
                "ctr": r.get("ctr", 0.0),
                "position": r.get("position", 99.0)
            }
            for r in rows
        ]
    except Exception as e:
        return [{"_error": str(e)}]
