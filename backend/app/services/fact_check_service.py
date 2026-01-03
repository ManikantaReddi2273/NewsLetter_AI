"""Fact-checking service using Google Fact Check API and heuristics."""
import requests
from typing import List, Dict, Optional
from loguru import logger
from app.config import get_settings

settings = get_settings()


class FactCheckService:
    """Service for fact-checking articles."""
    
    GOOGLE_FACT_CHECK_API = "https://factchecktools.googleapis.com/v1alpha1/checkClaim"
    
    @staticmethod
    def extract_claims(text: str, max_claims: int = 3) -> List[str]:
        """
        Extract potential claims from article text (simple heuristic).
        
        Args:
            text: Article text
            max_claims: Max claims to extract
            
        Returns:
            List of potential claims
        """
        if not text or len(text) < 50:
            return []
        
        # Split into sentences and pick first few as potential claims
        sentences = text.split('.')
        claims = []
        for sent in sentences[:max_claims * 2]:
            sent = sent.strip()
            if 50 < len(sent) < 500 and not sent.startswith(('http', 'The', 'A ', 'An ')):
                claims.append(sent)
        
        return claims[:max_claims]
    
    @staticmethod
    def fact_check_claim(claim: str, api_key: Optional[str] = None) -> Dict:
        """
        Fact-check a single claim using Google Fact Check API.
        
        Args:
            claim: Claim to fact-check
            api_key: Google API key (uses settings if not provided)
            
        Returns:
            Dict with fact-check status, confidence, and sources
        """
        try:
            if not api_key:
                api_key = settings.GOOGLE_FACT_CHECK_API_KEY
            
            if not api_key:
                # Fallback to heuristic if no API key
                return FactCheckService._heuristic_check(claim)
            
            params = {
                "query": claim[:500],
                "key": api_key
            }
            
            response = requests.get(
                FactCheckService.GOOGLE_FACT_CHECK_API,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("claims"):
                    # Get most relevant claim
                    claim_obj = data["claims"][0]
                    
                    # Extract verdict
                    verdict = "unknown"
                    if claim_obj.get("claimReview"):
                        for review in claim_obj["claimReview"]:
                            if review.get("textualRating"):
                                verdict = review["textualRating"].lower()
                                break
                    
                    return {
                        "status": "verified" if "true" in verdict else "flagged",
                        "verdict": verdict,
                        "sources": [r.get("publisher", {}).get("name", "Unknown") 
                                   for r in claim_obj.get("claimReview", [])][:2],
                        "method": "google_api"
                    }
                else:
                    return {
                        "status": "unknown",
                        "verdict": "No fact-check data available",
                        "sources": [],
                        "method": "google_api"
                    }
            else:
                logger.warning(f"Google Fact Check API error: {response.status_code}")
                return FactCheckService._heuristic_check(claim)
                
        except Exception as e:
            logger.warning(f"Fact-check API failed, using heuristic: {e}")
            return FactCheckService._heuristic_check(claim)
    
    @staticmethod
    def _heuristic_check(claim: str) -> Dict:
        """Fallback heuristic fact-check."""
        lowered = claim.lower()
        risky_words = ["rumor", "fake", "unverified", "conspiracy", "allegedly", "possibly"]
        
        if any(word in lowered for word in risky_words):
            return {
                "status": "flagged",
                "verdict": "Contains uncertainty markers",
                "sources": [],
                "method": "heuristic"
            }
        
        return {
            "status": "verified",
            "verdict": "Passes basic checks",
            "sources": [],
            "method": "heuristic"
        }
    
    @staticmethod
    def check_article(article_text: str) -> Dict:
        """
        Fact-check an entire article by extracting and checking claims.
        
        Args:
            article_text: Article text
            
        Returns:
            Dict with overall status and claim details
        """
        try:
            claims = FactCheckService.extract_claims(article_text, max_claims=2)
            
            if not claims:
                return {
                    "overall_status": "verified",
                    "claims_checked": 0,
                    "flagged_count": 0,
                    "verified_count": 0,
                    "details": []
                }
            
            results = []
            flagged_count = 0
            verified_count = 0
            
            for claim in claims:
                result = FactCheckService.fact_check_claim(claim)
                results.append(result)
                
                if result["status"] == "flagged":
                    flagged_count += 1
                elif result["status"] == "verified":
                    verified_count += 1
            
            # Overall status: flagged if any claim is flagged
            overall = "flagged" if flagged_count > 0 else "verified"
            
            return {
                "overall_status": overall,
                "claims_checked": len(claims),
                "flagged_count": flagged_count,
                "verified_count": verified_count,
                "details": results
            }
            
        except Exception as e:
            logger.error(f"Article fact-check failed: {e}")
            return {
                "overall_status": "unknown",
                "claims_checked": 0,
                "flagged_count": 0,
                "verified_count": 0,
                "details": []
            }


# Global instance
fact_check_service = FactCheckService()
