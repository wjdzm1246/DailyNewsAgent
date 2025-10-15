import os
import re

from crewai.tools import tool
from crewai_tools import SerperDevTool
from firecrawl import Firecrawl
from datetime import datetime, timedelta, timezone
import textwrap

search_tool = SerperDevTool(
    n_results=10,
)


@tool
def web_search_tool(url: str):
    """
    Web Search Tool.
    Args:
        url: str
            The url for scrapping.
    Returns
        A list of search results with the website content in Markdown format.
    """

    print("------#########################################  URL  ############################################-----")
    print(url)

    # --- 허브/토픽 URL 필터링 ---
    hub_patterns = ["/tag/", "/topic/", "/hub/",
                    "/section/", "/category/", "/us-news$"]
    if any(p in url for p in hub_patterns):
        return {"error": "Filtered out hub/index URL", "url": url}

    app = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))

    doc = app.scrape(url, formats=["markdown"])

    # if doc.metadata.error:
    #     return f"Error using tool. Status code: {doc.metadata.status_code}"

    # --- Firecrawl 메타데이터 확인 ---
    error = getattr(doc.metadata, "error", None)
    status_code = getattr(doc.metadata, "status_code", None)
    title = getattr(doc.metadata, "title", "Untitled")
    published_time = getattr(doc.metadata, "published_time", None)

    if error:
        return {
            "error": f"Scraping failed. Status code: {status_code}",
            "url": url
        }

    markdown = getattr(doc, "markdown", "")

    if doc.metadata.published_time is None:
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", markdown)
        date_str = date_match.group() if date_match else None
    else:
        date_str = doc.metadata.published_time

    # 날짜 유효성 체크 (48시간 이내만 허용)
    if date_str:
        try:
            published_date = datetime.fromisoformat(
                date_str.replace("Z", "+00:00"))
            # ✅ utcnow() 대신 now(timezone.utc) 사용
            if datetime.now(timezone.utc) - published_date > timedelta(hours=48):
                return {"error": f"Article older than 48h: {date_str}"}
        except Exception:
            pass  # 날짜 파싱 실패 → 그냥 넘어감

    # 4. 본문 정리
    cleaned = re.sub(r"\\+|\n+", "", markdown).strip()
    cleaned = re.sub(r"\[[^\]]+\]\([^\)]+\)|https?://[^\s]+", "", cleaned)

    # 5. 길이 체크 (100 단어 미만 reject)
    word_count = len(cleaned.split())
    if word_count < 100:
        return {"error": f"Article too short (<200 words). Word count: {word_count}"}

    # cleaned 텍스트를 100자 단위로 잘라서 줄바꿈
    # wrapped = "  \n".join(textwrap.wrap(cleaned, width=100))
    # wrapped = textwrap.fill(cleaned, width=80)

    return cleaned
