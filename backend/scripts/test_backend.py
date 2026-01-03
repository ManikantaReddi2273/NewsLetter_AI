"""Test script for Phase 1 backend implementation."""
import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from loguru import logger

# Base URL for API
BASE_URL = "http://localhost:8000/api/v1"

def print_test_header(test_name):
    """Print test section header."""
    print("\n" + "="*70)
    print(f"🧪 TEST: {test_name}")
    print("="*70)

def print_result(success, message):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}\n")

def test_health_check():
    """Test health check endpoint."""
    print_test_header("Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"FAISS Index: {json.dumps(data.get('faiss_index'), indent=2)}")
            print_result(True, "Health check successful")
            return True
        else:
            print_result(False, f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Health check error: {e}")
        return False

def test_user_signup():
    """Test user signup endpoint."""
    print_test_header("User Signup")
    
    try:
        user_data = {
            "email": "test@example.com",
            "interests": ["AI", "Technology", "Science"],
            "reading_level": "intermediate"
        }
        
        response = requests.post(f"{BASE_URL}/signup", json=user_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"Created User ID: {data.get('id')}")
            print(f"Email: {data.get('email')}")
            print(f"Interests: {data.get('interests')}")
            print(f"Reading Level: {data.get('reading_level')}")
            print(f"Subscription: {data.get('subscription_status')}")
            print_result(True, "User signup successful")
            return data.get('id')
        elif response.status_code == 400:
            print_result(True, "User already exists (expected behavior)")
            # Try to get user ID by searching
            return 1  # Assume first user for testing
        else:
            print_result(False, f"Signup failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Signup error: {e}")
        return None

def test_fetch_news(user_id=None):
    """Test news fetching endpoint."""
    print_test_header("Fetch News")
    
    try:
        params = {"limit": 5}
        if user_id:
            params["user_id"] = user_id
        
        response = requests.get(f"{BASE_URL}/fetch_news", params=params)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"Fetched {len(articles)} articles")
            
            for i, article in enumerate(articles[:3], 1):
                print(f"\n  Article {i}:")
                print(f"    Title: {article.get('title')}")
                print(f"    Source: {article.get('source')}")
                print(f"    ID: {article.get('id')}")
            
            print_result(True, f"Fetched {len(articles)} articles successfully")
            return [a.get('id') for a in articles]
        else:
            print_result(False, f"Fetch news failed: {response.status_code}")
            return []
    except Exception as e:
        print_result(False, f"Fetch news error: {e}")
        return []

def test_generate_embeddings(article_ids=None):
    """Test embedding generation endpoint."""
    print_test_header("Generate Embeddings")
    
    try:
        data = {}
        if article_ids:
            data["article_ids"] = article_ids[:5]  # Limit to 5 for testing
        
        response = requests.post(f"{BASE_URL}/generate_embeddings", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            print(f"Embeddings Generated: {result.get('embeddings_generated')}")
            
            if result.get('faiss_stats'):
                print(f"FAISS Stats: {json.dumps(result.get('faiss_stats'), indent=2)}")
            
            print_result(True, "Embeddings generated successfully")
            return True
        else:
            print_result(False, f"Generate embeddings failed: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Generate embeddings error: {e}")
        return False

def test_semantic_search(user_id):
    """Test semantic search endpoint."""
    print_test_header("Semantic Search")
    
    try:
        search_data = {
            "query": "artificial intelligence",
            "user_id": user_id,
            "top_k": 5
        }
        
        response = requests.post(f"{BASE_URL}/search_articles", json=search_data)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"Query: {data.get('query')}")
            print(f"Found {data.get('total_results')} results\n")
            
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article.get('title')}")
                print(f"     Source: {article.get('source')}")
                print(f"     ID: {article.get('id')}\n")
            
            print_result(True, f"Search returned {len(articles)} results")
            return articles
        else:
            print_result(False, f"Search failed: {response.status_code}")
            return []
    except Exception as e:
        print_result(False, f"Search error: {e}")
        return []

def test_summarization():
    """Test article summarization endpoint."""
    print_test_header("Article Summarization")
    
    try:
        summarize_data = {
            "article_url": "https://example.com/ai-healthcare-1",
            "reading_level": "beginner"
        }
        
        response = requests.post(f"{BASE_URL}/summarize", json=summarize_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Reading Level: {data.get('reading_level')}")
            print(f"Word Count: {data.get('word_count')}")
            print(f"\nSummary Points:")
            for i, point in enumerate(data.get('summary', []), 1):
                print(f"  {i}. {point}")
            
            print_result(True, "Summarization successful")
            return True
        else:
            print_result(False, f"Summarization failed: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Summarization error: {e}")
        return False

def test_feedback(user_id, article_id):
    """Test feedback submission endpoint."""
    print_test_header("Submit Feedback")
    
    try:
        feedback_data = {
            "user_id": user_id,
            "article_id": article_id,
            "rating": 5
        }
        
        response = requests.post(f"{BASE_URL}/feedback", json=feedback_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"Feedback ID: {data.get('id')}")
            print(f"User ID: {data.get('user_id')}")
            print(f"Article ID: {data.get('article_id')}")
            print(f"Rating: {data.get('rating')} ⭐")
            print_result(True, "Feedback submitted successfully")
            return True
        else:
            print_result(False, f"Feedback failed: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Feedback error: {e}")
        return False

def test_send_email(user_id, article_ids):
    """Test email sending endpoint."""
    print_test_header("Send Newsletter Email")
    
    try:
        email_data = {
            "user_id": user_id,
            "article_ids": article_ids[:3],
            "subject": "Your Test Newsletter"
        }
        
        response = requests.post(
            f"{BASE_URL}/send_email",
            params=email_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            print(f"Articles Sent: {data.get('articles_sent')}")
            print_result(True, "Email sent successfully")
            return True
        else:
            print_result(False, f"Email sending failed: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Email sending error: {e}")
        return False

def run_all_tests():
    """Run all Phase 1 backend tests."""
    print("\n" + "🚀 "*20)
    print("PHASE 1 BACKEND TESTING")
    print("🚀 "*20)
    
    results = {}
    
    # Test 1: Health Check
    results['health_check'] = test_health_check()
    
    # Test 2: User Signup
    user_id = test_user_signup()
    results['user_signup'] = user_id is not None
    
    if not user_id:
        print("\n❌ Cannot continue tests without user_id")
        return results
    
    # Test 3: Fetch News
    article_ids = test_fetch_news(user_id)
    results['fetch_news'] = len(article_ids) > 0
    
    if not article_ids:
        print("\n⚠️  No articles fetched, using sample articles")
        article_ids = [1, 2, 3]  # Assume sample articles from setup script
    
    # Test 4: Generate Embeddings
    results['generate_embeddings'] = test_generate_embeddings(article_ids)
    
    # Test 5: Semantic Search
    search_results = test_semantic_search(user_id)
    results['semantic_search'] = len(search_results) > 0
    
    # Test 6: Summarization
    results['summarization'] = test_summarization()
    
    # Test 7: Feedback
    if article_ids:
        results['feedback'] = test_feedback(user_id, article_ids[0])
    
    # Test 8: Send Email
    if article_ids:
        results['send_email'] = test_send_email(user_id, article_ids)
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 1 backend is fully functional.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
    
    return results

if __name__ == "__main__":
    print("\n⚡ Starting backend server test suite...")
    print("📌 Make sure the backend server is running on http://localhost:8000")
    
    try:
        # Quick check if server is running
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Server is running!\n")
            run_all_tests()
        else:
            print("❌ Server returned unexpected status")
    except requests.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server")
        print("   Please start the server with: python main.py")
        sys.exit(1)
