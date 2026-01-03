"""Resend email service for sending newsletters."""
import requests
from typing import List, Dict
from loguru import logger
from app.config import get_settings

settings = get_settings()


class ResendService:
    """Service for sending emails using Resend API."""
    
    def __init__(self):
        """Initialize Resend service."""
        self.api_key = settings.RESEND_API_KEY
        self.base_url = "https://api.resend.com/emails"
        self.from_email = "newsletter@yourdomain.com"  # Configure in production
    
    def send_newsletter(
        self, 
        to_email: str,
        subject: str,
        html_content: str,
        articles: List[Dict] = None
    ) -> bool:
        """
        Send newsletter email to user.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            articles: List of article dictionaries
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.api_key:
                logger.warning("RESEND_API_KEY not set. Email not sent (mock mode).")
                logger.info(f"Mock email sent to {to_email} with subject: {subject}")
                return True
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # If articles provided but no html_content, generate it
            if not html_content and articles:
                html_content = self._generate_newsletter_html(articles)
            
            payload = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Email sent successfully to {to_email}. ID: {data.get('id')}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to send email via Resend: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Resend service: {e}")
            return False
    
    def _generate_newsletter_html(self, articles: List[Dict]) -> str:
        """
        Generate HTML newsletter from articles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            HTML string
        """
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px;
                }
                .article {
                    background-color: #f9f9f9;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                    border-left: 4px solid #4CAF50;
                }
                .article-title {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #2c3e50;
                }
                .article-source {
                    color: #7f8c8d;
                    font-size: 12px;
                    margin-bottom: 8px;
                }
                .article-content {
                    color: #555;
                    margin-bottom: 10px;
                }
                .article-link {
                    color: #4CAF50;
                    text-decoration: none;
                    font-weight: bold;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #999;
                    font-size: 12px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Your AI-Curated Newsletter</h1>
                <p>Personalized news just for you</p>
            </div>
        """
        
        for article in articles:
            html += f"""
            <div class="article">
                <div class="article-title">{article.get('title', 'Untitled')}</div>
                <div class="article-source">Source: {article.get('source', 'Unknown')}</div>
                <div class="article-content">{article.get('content', '')}</div>
                <a href="{article.get('url', '#')}" class="article-link">Read More →</a>
            </div>
            """
        
        html += """
            <div class="footer">
                <p>You received this email because you subscribed to our AI Newsletter.</p>
                <p>© 2026 AI Newsletter. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return html


# Global Resend service instance
resend_service = ResendService()
