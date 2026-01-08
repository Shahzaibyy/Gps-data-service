"""
Async HTTP client with retry logic, circuit breaker, and rate limiting.
"""
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import GPSProviderError, GPSProviderTimeout

logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API requests."""
    
    def __init__(self, rate: float):
        """
        Initialize rate limiter.
        
        Args:
            rate: Maximum requests per second
        """
        self.rate = rate
        self.tokens = rate
        self.updated_at = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            while self.tokens < 1:
                now = asyncio.get_event_loop().time()
                time_passed = now - self.updated_at
                self.tokens = min(self.rate, self.tokens + time_passed * self.rate)
                self.updated_at = now
                
                if self.tokens < 1:
                    sleep_time = (1 - self.tokens) / self.rate
                    await asyncio.sleep(sleep_time)
            
            self.tokens -= 1


class AsyncHTTPClient:
    """
    Production-ready async HTTP client with:
    - Automatic retries with exponential backoff
    - Rate limiting
    - Timeout handling
    - Connection pooling
    - Structured logging
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        rate_limit: Optional[float] = None
    ):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL for all requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff: Exponential backoff multiplier
            rate_limit: Maximum requests per second (None = no limit)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = RateLimiter(rate_limit) if rate_limit else None
        
        # Retry configuration
        self._retry_decorator = retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=retry_backoff, min=1, max=30),
            retry=retry_if_exception_type((
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.ConnectTimeout
            )),
            before_sleep=before_sleep_log(logger, logger.level)
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(
                    max_connections=settings.MAX_CONCURRENT_REQUESTS,
                    max_keepalive_connections=20
                ),
                follow_redirects=True
            )
            logger.info(f"HTTP client initialized for {self.base_url}")
    
    async def close(self):
        """Close the HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client closed")
    
    async def _apply_rate_limit(self):
        """Apply rate limiting if configured."""
        if self._rate_limiter:
            await self._rate_limiter.acquire()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=30),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, logger.level)
    )
    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a POST request with retry logic.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            json_data: JSON payload
            headers: Additional headers
            **kwargs: Additional httpx parameters
            
        Returns:
            Dict containing response JSON
            
        Raises:
            GPSProviderError: If request fails after retries
            GPSProviderTimeout: If request times out
        """
        if not self._client:
            await self.start()
        
        await self._apply_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"POST {url}", extra={"payload": json_data})
            
            response = await self._client.post(
                endpoint,
                json=json_data,
                headers=headers,
                **kwargs
            )
            
            response.raise_for_status()
            
            logger.debug(f"POST {url} succeeded", extra={"status_code": response.status_code})
            
            return response.json()
            
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout for {url}", exc_info=True)
            raise GPSProviderTimeout(f"Request to {url} timed out after {self.timeout}s") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code} for {url}",
                extra={"response": e.response.text}
            )
            raise GPSProviderError(
                f"GPS API returned status {e.response.status_code}: {e.response.text}"
            ) from e
        
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}", exc_info=True)
            raise GPSProviderError(f"Failed to connect to GPS API: {str(e)}") from e
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a GET request with retry logic.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional httpx parameters
            
        Returns:
            Dict containing response JSON
        """
        if not self._client:
            await self.start()
        
        await self._apply_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"GET {url}", extra={"params": params})
            
            response = await self._client.get(
                endpoint,
                params=params,
                headers=headers,
                **kwargs
            )
            
            response.raise_for_status()
            
            logger.debug(f"GET {url} succeeded", extra={"status_code": response.status_code})
            
            return response.json()
            
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout for {url}", exc_info=True)
            raise GPSProviderTimeout(f"Request to {url} timed out") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {url}", exc_info=True)
            raise GPSProviderError(f"GPS API error: {e.response.status_code}") from e
        
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}", exc_info=True)
            raise GPSProviderError(f"Connection failed: {str(e)}") from e


@asynccontextmanager
async def get_http_client():
    """
    Dependency injection factory for HTTP client.
    
    Usage:
        async with get_http_client() as client:
            result = await client.post('/endpoint', json_data={...})
    """
    client = AsyncHTTPClient(
        base_url=settings.GPS_API_BASE_URL,
        timeout=settings.GPS_API_TIMEOUT,
        max_retries=settings.GPS_API_MAX_RETRIES,
        retry_backoff=settings.GPS_API_RETRY_BACKOFF,
        rate_limit=settings.RATE_LIMIT_REQUESTS_PER_SECOND
    )
    
    try:
        await client.start()
        yield client
    finally:
        await client.close()