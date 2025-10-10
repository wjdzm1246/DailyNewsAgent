import sys
from datetime import datetime

import dotenv
from crewai import Crew, Agent, Task
from crewai.project import CrewBase, agent, task, crew

from tools import search_tool, web_search_tool

# Load environment variables
dotenv.load_dotenv()


@CrewBase
class NewsReaderAgent:
    """Agent for fetching and processing news articles."""

    @agent
    def news_hunter_agent(self):
        """Agent that searches for breaking news."""
        return Agent(
            config=self.agents_config["news_hunter_agent"],
            tools=[search_tool, web_search_tool],
        )

    @task
    def content_harvesting_task(self):
        """Task to collect raw news content."""
        return Task(
            config=self.tasks_config["content_harvesting_task"],
        )

    @crew
    def crew(self):
        """Crew orchestrating the agents and tasks."""
        return Crew(
            tasks=self.tasks,
            agents=self.agents,
            verbose=True,
        )

def redirect_logs(filename: str = "crew_run.log"):
    """Redirect stdout and stderr to a log file."""
    log_file = open(filename, "w", encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file
    return log_file


def build_news_query(mode: str = "us") -> str:
    """Builds a search query string for today's top news based on mode."""
    today = datetime.today()
    today_str_full = today.strftime("%B %d, %Y")
    today_dash = today.strftime("%Y/%m/%d")
    today_bar = today.strftime("%Y-%m-%d")

    if mode == "ko":
        sites = ["yna.co.kr", "hani.co.kr", "khan.co.kr"]
        query = (
            f"{today_str_full} 오늘의 주요 뉴스 "
            f"site:{' OR site:'.join(sites)}"
        )
    else:
        sites = ["reuters.com", "npr.org"]
        query = (
            f"Top breaking US news {today_str_full} "
            f"site:{sites[0]} inurl:/{today_bar}/ OR "
            f"site:{sites[1]} inurl:/{today_dash}/"
        )
    return query

def main():
    """Main execution entry point."""
    log_file = redirect_logs()

    # Get mode (default: 'us')
    news_type = sys.argv[1] if len(sys.argv) > 1 else "us"

    # Build query based on selected mode
    query = build_news_query(news_type)

    # Prepare inputs for the crew
    inputs = {
        "topic": query,
        "language": "us" if news_type == "us" else "ko"
    }

    # Run the Crew
    crew_instance = NewsReaderAgent().crew()
    result = crew_instance.kickoff(inputs=inputs)

    log_file.close()
    return result


if __name__ == "__main__":
    main()

