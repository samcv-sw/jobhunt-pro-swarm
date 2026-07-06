import pytest
from backend.main import rate_limiter

@pytest.fixture(autouse=True)
def reset_rate_limiter_global(request):
    is_rate_limit_test = (
        "rate_limiting" in request.node.name 
        or "rate_limit" in request.node.name 
        or "rate_limiter" in request.node.name
    )
    
    if not is_rate_limit_test:
        old_limit = rate_limiter.requests_limit
        rate_limiter.requests_limit = 100000
        
    rate_limiter.reset()
    yield
    rate_limiter.reset()
    
    if not is_rate_limit_test:
        rate_limiter.requests_limit = old_limit
