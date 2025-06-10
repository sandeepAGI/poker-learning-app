# backend/utils/performance.py
import time
import functools
import asyncio
from typing import Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

# Simple cache implementation if cachetools is not available
try:
    import cachetools
    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False
    # Simple fallback cache implementations
    class TTLCache:
        def __init__(self, maxsize, ttl):
            self.maxsize = maxsize
            self.ttl = ttl
            self._cache = {}
            self.currsize = 0
        
        def __contains__(self, key):
            if key in self._cache:
                timestamp, value = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    return True
                else:
                    del self._cache[key]
                    self.currsize -= 1
            return False
        
        def __getitem__(self, key):
            if key in self:
                return self._cache[key][1]
            raise KeyError(key)
        
        def __setitem__(self, key, value):
            if len(self._cache) >= self.maxsize and key not in self._cache:
                # Remove oldest item
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
                del self._cache[oldest_key]
                self.currsize -= 1
            
            self._cache[key] = (time.time(), value)
            if key not in self._cache:
                self.currsize += 1
        
        def clear(self):
            self._cache.clear()
            self.currsize = 0
        
        def __len__(self):
            return len(self._cache)
    
    class LRUCache:
        def __init__(self, maxsize):
            self.maxsize = maxsize
            self._cache = {}
            self._order = []
            self.currsize = 0
        
        def __contains__(self, key):
            return key in self._cache
        
        def __getitem__(self, key):
            if key in self._cache:
                # Move to end (most recently used)
                self._order.remove(key)
                self._order.append(key)
                return self._cache[key]
            raise KeyError(key)
        
        def __setitem__(self, key, value):
            if key in self._cache:
                self._order.remove(key)
            elif len(self._cache) >= self.maxsize:
                # Remove least recently used
                oldest = self._order.pop(0)
                del self._cache[oldest]
                self.currsize -= 1
            
            self._cache[key] = value
            self._order.append(key)
            if key not in self._cache:
                self.currsize += 1
        
        def clear(self):
            self._cache.clear()
            self._order.clear()
            self.currsize = 0
        
        def __len__(self):
            return len(self._cache)
    
    cachetools = type('cachetools', (), {
        'TTLCache': TTLCache,
        'LRUCache': LRUCache
    })()

from utils.logger import get_logger

logger = get_logger("performance")

# Global thread pool for CPU-intensive tasks
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="poker_cpu")

# Caching decorators and managers
class PerformanceManager:
    """Manages performance optimizations across the application"""
    
    def __init__(self):
        # TTL cache for hand evaluations (cache for 30 seconds)
        self.hand_evaluation_cache = cachetools.TTLCache(maxsize=1000, ttl=30)
        
        # TTL cache for AI decisions (cache for 10 seconds)
        self.ai_decision_cache = cachetools.TTLCache(maxsize=500, ttl=10)
        
        # Cache for static computations
        self.static_cache = cachetools.LRUCache(maxsize=2000)
        
    def cache_hand_evaluation(self, func):
        """Decorator to cache hand evaluation results"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from hole cards, community cards, and deck size
            cache_key = self._create_hand_cache_key(args, kwargs)
            
            if cache_key in self.hand_evaluation_cache:
                logger.debug(f"Hand evaluation cache hit for key: {cache_key[:20]}...")
                return self.hand_evaluation_cache[cache_key]
            
            result = func(*args, **kwargs)
            self.hand_evaluation_cache[cache_key] = result
            logger.debug(f"Hand evaluation cached for key: {cache_key[:20]}...")
            return result
        return wrapper
    
    def cache_ai_decision(self, func):
        """Decorator to cache AI decision results"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from relevant game state
            cache_key = self._create_ai_cache_key(args, kwargs)
            
            if cache_key in self.ai_decision_cache:
                logger.debug(f"AI decision cache hit for key: {cache_key[:20]}...")
                return self.ai_decision_cache[cache_key]
            
            result = func(*args, **kwargs)
            self.ai_decision_cache[cache_key] = result
            logger.debug(f"AI decision cached for key: {cache_key[:20]}...")
            return result
        return wrapper
    
    def cache_static(self, func):
        """Decorator to cache static computations"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = str(args) + str(sorted(kwargs.items()))
            
            if cache_key in self.static_cache:
                return self.static_cache[cache_key]
            
            result = func(*args, **kwargs)
            self.static_cache[cache_key] = result
            return result
        return wrapper
    
    def async_cpu_task(self, func):
        """Decorator to run CPU-intensive tasks asynchronously"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(thread_pool, func, *args, **kwargs)
        return wrapper
    
    def _create_hand_cache_key(self, args, kwargs) -> str:
        """Create cache key for hand evaluations"""
        try:
            # Extract relevant parameters for hand evaluation
            hole_cards = args[1] if len(args) > 1 else kwargs.get('hole_cards', [])
            community_cards = args[2] if len(args) > 2 else kwargs.get('community_cards', [])
            deck_size = len(args[3]) if len(args) > 3 else len(kwargs.get('deck', []))
            
            return f"hand_{sorted(hole_cards)}_{sorted(community_cards)}_{deck_size}"
        except (IndexError, TypeError):
            # Fallback to string representation
            return str(args) + str(sorted(kwargs.items()))
    
    def _create_ai_cache_key(self, args, kwargs) -> str:
        """Create cache key for AI decisions"""
        try:
            # Extract relevant parameters for AI decisions
            hole_cards = args[1] if len(args) > 1 else kwargs.get('hole_cards', [])
            pot_size = args[4] if len(args) > 4 else kwargs.get('pot_size', 0)
            spr = args[5] if len(args) > 5 else kwargs.get('spr', 0)
            
            return f"ai_{sorted(hole_cards)}_{pot_size}_{spr}"
        except (IndexError, TypeError):
            # Fallback to string representation
            return str(args) + str(sorted(kwargs.items()))
    
    def clear_caches(self):
        """Clear all caches"""
        self.hand_evaluation_cache.clear()
        self.ai_decision_cache.clear()
        self.static_cache.clear()
        logger.info("All performance caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "hand_evaluation_cache": {
                "size": len(self.hand_evaluation_cache),
                "maxsize": self.hand_evaluation_cache.maxsize,
                "currsize": self.hand_evaluation_cache.currsize
            },
            "ai_decision_cache": {
                "size": len(self.ai_decision_cache),
                "maxsize": self.ai_decision_cache.maxsize,
                "currsize": self.ai_decision_cache.currsize
            },
            "static_cache": {
                "size": len(self.static_cache),
                "maxsize": self.static_cache.maxsize,
                "currsize": self.static_cache.currsize
            }
        }

# Global performance manager instance
performance_manager = PerformanceManager()

def profile_time(func):
    """Decorator to profile function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 0.1:  # Log if takes more than 100ms
            logger.warning(f"Slow execution: {func.__name__} took {execution_time:.3f}s")
        else:
            logger.debug(f"Function {func.__name__} took {execution_time:.3f}s")
        
        return result
    return wrapper

def async_profile_time(func):
    """Decorator to profile async function execution time"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 0.1:  # Log if takes more than 100ms
            logger.warning(f"Slow async execution: {func.__name__} took {execution_time:.3f}s")
        else:
            logger.debug(f"Async function {func.__name__} took {execution_time:.3f}s")
        
        return result
    return wrapper

# Connection pooling for database-like operations
class ConnectionPool:
    """Simple connection pool for file-based operations"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pool = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
    
    async def get_connection(self):
        """Get a connection from the pool"""
        if self.active_connections < self.max_connections:
            self.active_connections += 1
            return FileConnection()
        else:
            return await self.pool.get()
    
    async def return_connection(self, connection):
        """Return a connection to the pool"""
        if self.pool.full():
            # Pool is full, close the connection
            await connection.close()
            self.active_connections -= 1
        else:
            await self.pool.put(connection)

class FileConnection:
    """Mock connection for file operations with pooling"""
    
    def __init__(self):
        self.created_at = time.time()
    
    async def close(self):
        """Close the connection"""
        pass

# Global connection pool
file_pool = ConnectionPool(max_connections=5)

# Optimized Monte Carlo simulation
class OptimizedMonteCarloSimulator:
    """Optimized Monte Carlo simulator for poker hand evaluation"""
    
    def __init__(self, cache_manager: Optional[PerformanceManager] = None):
        self.cache_manager = cache_manager or performance_manager
        
    @profile_time
    def run_simulation(self, hole_cards, community_cards, deck, simulations=50):
        """Run optimized Monte Carlo simulation"""
        # Reduce default simulations from 100 to 50 for better performance
        
        # Use caching to avoid repeated simulations
        cache_key = f"monte_carlo_{sorted(hole_cards)}_{sorted(community_cards)}_{len(deck)}_{simulations}"
        
        if hasattr(self.cache_manager, 'static_cache') and cache_key in self.cache_manager.static_cache:
            return self.cache_manager.static_cache[cache_key]
        
        # Run the actual simulation
        from ai.hand_evaluator import HandEvaluator
        evaluator = HandEvaluator()
        result = evaluator.evaluate_hand(hole_cards, community_cards, deck)
        
        # Cache the result
        if hasattr(self.cache_manager, 'static_cache'):
            self.cache_manager.static_cache[cache_key] = result
        
        return result

# Export key components
__all__ = [
    'performance_manager',
    'profile_time', 
    'async_profile_time',
    'file_pool',
    'thread_pool',
    'OptimizedMonteCarloSimulator'
]