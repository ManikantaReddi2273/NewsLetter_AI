"""Groq API service for article summarization."""
import requests
from bs4 import BeautifulSoup
from groq import Groq
from typing import List, Optional
from loguru import logger
from app.config import get_settings

settings = get_settings()


class GroqService:
    """Service for article summarization using Groq API."""
    
    def __init__(self):
        """Initialize Groq service."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Groq client."""
        try:
            if not settings.GROQ_API_KEY:
                logger.warning("GROQ_API_KEY not set. Summarization will not work.")
                return
            
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            logger.info("Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise
    
    def fetch_article_text(self, url: str) -> Optional[str]:
        """
        Fetch article text from URL using BeautifulSoup.
        
        Args:
            url: Article URL
            
        Returns:
            Extracted article text or None if failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Try to find main content
            article_content = soup.find('article') or soup.find('main') or soup.find('body')
            
            if article_content:
                # Get text from paragraphs
                paragraphs = article_content.find_all('p')
                text = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                
                if text:
                    logger.info(f"Extracted {len(text)} characters from {url}")
                    return text[:10000]  # Limit to 10k characters
            
            logger.warning(f"Could not extract article text from {url}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch article from {url}: {e}")
            return None
    
    def summarize(
        self, 
        article_text: str, 
        reading_level: str = "intermediate",
        num_points: int = 3
    ) -> dict:
        """
        Summarize article using Groq API.
        
        Args:
            article_text: Full article text
            reading_level: Target reading level (beginner/intermediate/expert)
            num_points: Number of bullet points to generate
            
        Returns:
            Dictionary with summary and metadata
        """
        try:
            if not self.client:
                raise ValueError("Groq client not initialized. Check GROQ_API_KEY.")
            
            # Create prompt based on reading level
            level_instructions = {
                "beginner": "Use simple language, short sentences, and avoid jargon. Explain concepts clearly.",
                "intermediate": "Use clear language with some technical terms. Balance detail with accessibility.",
                "expert": "Use technical language and industry terminology. Include nuanced analysis."
            }
            
            instruction = level_instructions.get(reading_level, level_instructions["intermediate"])
            
            prompt = f"""Summarize the following article in exactly {num_points} concise bullet points.

Reading level: {reading_level}
Instructions: {instruction}

Article:
{article_text[:8000]}

Provide ONLY the {num_points} bullet points, one per line, starting with a dash (-).
"""
            
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional news summarizer. Provide clear, factual summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # Updated to a currently supported Groq model
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=500
            )
            
            # Extract summary
            summary_text = chat_completion.choices[0].message.content.strip()
            
            # Parse bullet points
            lines = [line.strip() for line in summary_text.split('\n') if line.strip()]
            bullet_points = []
            
            for line in lines:
                # Remove leading dash, asterisk, or number
                cleaned = line.lstrip('-*•').strip()
                if cleaned and not cleaned.startswith('#'):
                    bullet_points.append(cleaned)
            
            # Ensure we have the requested number of points
            if len(bullet_points) < num_points:
                logger.warning(f"Generated only {len(bullet_points)} points instead of {num_points}")
            
            summary = bullet_points[:num_points] if bullet_points else [summary_text]
            
            # Calculate word count
            word_count = sum(len(point.split()) for point in summary)
            
            logger.info(f"Generated summary with {len(summary)} points and {word_count} words")
            
            return {
                "summary": summary,
                "word_count": word_count,
                "reading_level": reading_level
            }
            
        except Exception as e:
            logger.error(f"Failed to summarize article: {e}")
            raise
    
    def summarize_from_url(
        self, 
        url: str, 
        reading_level: str = "intermediate"
    ) -> dict:
        """
        Fetch and summarize article from URL.
        
        Args:
            url: Article URL
            reading_level: Target reading level
            
        Returns:
            Dictionary with summary and metadata
        """
        try:
            # Fetch article text
            article_text = self.fetch_article_text(url)
            
            if not article_text:
                raise ValueError(f"Could not extract article text from {url}")
            
            # Summarize
            return self.summarize(article_text, reading_level)
            
        except Exception as e:
            logger.error(f"Failed to summarize article from URL: {e}")
            raise


# Global Groq service instance
groq_service = GroqService()
