"""
Global Rate Limiter for All API Calls
Prevents 429 errors by enforcing strict rate limits
"""
import time
from functools import wraps

# Global rate limiting state
_api_call_timestamps = []
_last_api_call = 0
_min_call_interval = 10  # 10 seconds between calls
_max_calls_per_minute = 5  # Maximum 5 calls per minute

def rate_limit(func):
    """Decorator to enforce rate limiting on any function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _api_call_timestamps, _last_api_call
        current_time = time.time()
        
        # Remove timestamps older than 60 seconds (sliding window)
        _api_call_timestamps = [t for t in _api_call_timestamps if current_time - t < 60]
        
        # Check if we've hit the per-minute limit
        if len(_api_call_timestamps) >= _max_calls_per_minute:
            oldest_call = min(_api_call_timestamps)
            wait_time = 60 - (current_time - oldest_call) + 1
            if wait_time > 0:
                print(f"⏳ Rate limit: {_max_calls_per_minute} calls/minute reached. Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                _api_call_timestamps = []
        
        # Check minimum interval between calls
        time_since_last = current_time - _last_api_call
        if time_since_last < _min_call_interval:
            sleep_time = _min_call_interval - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        # Update timestamps
        _last_api_call = time.time()
        _api_call_timestamps.append(time.time())
        
        # Call the original function
        return func(*args, **kwargs)
    
    return wrapper


def reset_rate_limit():
    """Reset rate limiting state (useful for testing)"""
    global _api_call_timestamps, _last_api_call
    _api_call_timestamps = []
    _last_api_call = 0


# Cache decorator
_cache = {}
_cache_max_size = 1000

def cached(func):
    """Decorator to cache function results"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and args
        cache_key = f"{func.__name__}:{str(args)[:100]}:{str(kwargs)[:100]}"
        cache_key_hash = hash(cache_key)
        
        # Check cache
        if cache_key_hash in _cache:
            print(f"✅ Using cached result for {func.__name__}")
            return _cache[cache_key_hash]
        
        # Call function
        result = func(*args, **kwargs)
        
        # Store in cache
        if len(_cache) >= _cache_max_size:
            # Remove oldest entry
            _cache.pop(next(iter(_cache)))
        _cache[cache_key_hash] = result
        
        return result
    
    return wrapper