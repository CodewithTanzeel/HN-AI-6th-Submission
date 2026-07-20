import pytest
from fastapi import HTTPException
from starlette.responses import JSONResponse
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.cache import CacheMiddleware


@pytest.mark.asyncio
async def test_rate_limit_allows_requests_within_limit():
    """Rate limiter should allow requests under the limit."""
    app = type("MockApp", (), {})()
    middleware = RateLimitMiddleware(app, requests_per_minute=5)
    request = type("MockRequest", (), {"client": type("MockClient", (), {"host": "127.0.0.1"})()})()

    async def mock_call_next(req):
        return JSONResponse(content={})

    # Should not raise for first 5 requests
    for _ in range(5):
        await middleware.dispatch(request, mock_call_next)


@pytest.mark.asyncio
async def test_rate_limit_blocks_excess_requests():
    """Rate limiter should block requests over the limit."""
    app = type("MockApp", (), {})()
    middleware = RateLimitMiddleware(app, requests_per_minute=2)
    request = type("MockRequest", (), {"client": type("MockClient", (), {"host": "127.0.0.1"})()})()

    async def mock_call_next(req):
        return JSONResponse(content={})

    # First 2 should pass
    await middleware.dispatch(request, mock_call_next)
    await middleware.dispatch(request, mock_call_next)

    # Third should fail
    with pytest.raises(HTTPException) as exc_info:
        await middleware.dispatch(request, mock_call_next)
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_cache_returns_cached_response():
    """Cache should return cached response for repeated GET requests."""
    app = type("MockApp", (), {})()
    middleware = CacheMiddleware(app, ttl_seconds=60)
    request = type("MockRequest", (), {
        "method": "GET",
        "url": type("MockURL", (), {"path": "/test", "query": ""})(),
    })()

    call_count = 0
    async def mock_call_next(req):
        nonlocal call_count
        call_count += 1
        return JSONResponse(content={"data": "test"})

    # First request
    response1 = await middleware.dispatch(request, mock_call_next)
    assert call_count == 1
    assert response1.status_code == 200

    # Second request should use cache
    response2 = await middleware.dispatch(request, mock_call_next)
    assert call_count == 1  # Should not increment
