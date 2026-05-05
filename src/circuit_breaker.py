"""
ATLAS v3.0 - Circuit Breaker pattern para resiliencia
"""
import asyncio
import logging
from typing import Callable, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,  # seconds
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.lock = asyncio.Lock()
    
    async def call(self, func: Callable) -> Any:
        """Execute function with circuit breaker protection"""
        
        async with self.lock:
            if self.state == CircuitState.OPEN:
                if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker [{self.name}] transitioning to HALF_OPEN state")
                else:
                    raise Exception(f"Circuit breaker [{self.name}] is OPEN")
        
        try:
            result = await func()
            
            # Éxito - resetear contador
            async with self.lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    logger.info(f"Circuit breaker [{self.name}] recovered to CLOSED state")
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            async with self.lock:
                self.failure_count += 1
                self.last_failure_time = datetime.utcnow()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.error(f"Circuit breaker [{self.name}] OPEN after {self.failure_count} failures")
                else:
                    logger.warning(f"Circuit breaker [{self.name}] failure {self.failure_count}/{self.failure_threshold}")
            
            raise e
