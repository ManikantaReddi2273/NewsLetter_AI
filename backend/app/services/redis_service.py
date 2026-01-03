"""Redis caching service for search results and recommendations."""
import redis
import json
from typing import Optional, Any
from loguru import logger
from app.config import get_settings

settings = get_settings()


class RedisService:
    """Service for Redis caching."""
    
    def __init__(self):
        """Initialize Redis service."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Redis client."""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Test connection
            self.client.ping()
            logger.info("Redis client initialized successfully")
            
        except redis.ConnectionError as e:
            logger.warning(f"Could not connect to Redis: {e}. Caching will be disabled.")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if not self.client:
                return None
            
            value = self.client.get(key)
            
            if value:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            
            logger.debug(f"Cache miss for key: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """
        Set value in Redis cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: settings.CACHE_TTL)
        """
        try:
            if not self.client:
                return
            
            ttl = ttl or settings.CACHE_TTL
            serialized_value = json.dumps(value)
            
            self.client.setex(key, ttl, serialized_value)
            logger.debug(f"Cached key: {key} with TTL: {ttl}s")
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
    
    def delete(self, key: str):
        """
        Delete key from Redis cache.
        
        Args:
            key: Cache key to delete
        """
        try:
            if not self.client:
                return
            
            self.client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
    
    def clear_pattern(self, pattern: str):
        """
        Clear all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "search:*")
        """
        try:
            if not self.client:
                return
            
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"Deleted {len(keys)} keys matching pattern: {pattern}")
            
        except Exception as e:
            logger.error(f"Failed to clear pattern {pattern}: {e}")
    
    def get_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate cache key from prefix and parameters.
        
        Args:
            prefix: Key prefix (e.g., "search", "recommend")
            **kwargs: Key-value pairs to include in key
            
        Returns:
            Generated cache key
        """
        parts = [prefix]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        
        return ":".join(parts)


# Global Redis service instance
redis_service = RedisService()
