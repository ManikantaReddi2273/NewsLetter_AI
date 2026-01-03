"""Serper API service for fetching news articles."""
import requests
from typing import List, Dict, Optional
from loguru import logger
from app.config import get_settings

settings = get_settings()


class SerperService:
    """Service for fetching news using Serper API."""
    
    def __init__(self):
        """Initialize Serper service."""
        self.api_key = settings.SERPER_API_KEY
        self.base_url = "https://google.serper.dev/news"
    
    def fetch_news(
        self, 
        query: str, 
        num_results: int = 10,
        country: str = "us"
    ) -> List[Dict]:
        """
        Fetch news articles from Serper API.
        
        Args:
            query: Search query (e.g., "AI technology")
            num_results: Number of results to fetch
            country: Country code for news (default: "us")
            
        Returns:
            List of article dictionaries
        """
        try:
            if not self.api_key:
                logger.warning("SERPER_API_KEY not set. Using mock data.")
                return self._get_mock_articles(query, num_results)
            
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": num_results,
                "gl": country
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse Serper response
            articles = []
            for item in data.get("news", []):
                article = {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("snippet", ""),
                    "source": item.get("source", "Unknown"),
                    "date": item.get("date", "")
                }
                articles.append(article)
            
            logger.info(f"Fetched {len(articles)} articles for query: {query}")
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch news from Serper: {e}")
            return self._get_mock_articles(query, num_results)
        except Exception as e:
            logger.error(f"Unexpected error in Serper service: {e}")
            return []
    
    def fetch_news_by_interests(
        self, 
        interests: List[str], 
        articles_per_interest: int = 5
    ) -> List[Dict]:
        """
        Fetch news articles for multiple interests.
        
        Args:
            interests: List of interest topics
            articles_per_interest: Number of articles per interest
            
        Returns:
            Combined list of articles
        """
        all_articles = []
        
        for interest in interests:
            articles = self.fetch_news(interest, articles_per_interest)
            all_articles.extend(articles)
        
        # Remove duplicates based on URL
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article["url"] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article["url"])
        
        logger.info(f"Fetched {len(unique_articles)} unique articles for interests: {interests}")
        return unique_articles
    
    def _get_mock_articles(self, query: str, num_results: int) -> List[Dict]:
        """
        Get mock articles when Serper API is not available.
        
        Args:
            query: Search query
            num_results: Number of mock articles
            
        Returns:
            List of mock articles
        """
        mock_articles = [
            {
                "title": f"Latest Developments in {query}: What You Need to Know",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-1",
                "content": f"Recent advances in {query} are transforming the industry. Experts discuss the implications and future outlook for this rapidly evolving field.",
                "source": "TechNews",
                "date": "2026-01-03"
            },
            {
                "title": f"Breaking: New Research in {query} Shows Promise",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-2",
                "content": f"Scientists announce breakthrough findings related to {query}. The research could have significant real-world applications.",
                "source": "Science Daily",
                "date": "2026-01-02"
            },
            {
                "title": f"How {query} is Changing the Future",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-3",
                "content": f"Industry leaders weigh in on the transformative potential of {query} and what it means for businesses and consumers.",
                "source": "Business Insider",
                "date": "2026-01-01"
            },
            {
                "title": f"Understanding {query}: A Comprehensive Guide",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-4",
                "content": f"An in-depth look at {query}, covering the basics, current trends, and expert predictions for the future.",
                "source": "Tech Review",
                "date": "2025-12-31"
            },
            {
                "title": f"The Impact of {query} on Modern Society",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-5",
                "content": f"Researchers examine how {query} is influencing various aspects of society, from education to healthcare.",
                "source": "The Guardian",
                "date": "2025-12-30"
            }
        ]
        
        return mock_articles[:num_results]


# Global Serper service instance
serper_service = SerperService()
