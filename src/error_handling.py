"""
Manejo centralizado de errores para ATLAS v3.0
Proporciona excepción base y decorador para agents asíncronos/síncronos.
"""

import functools
import inspect
import logging
from typing import Any, Callable, Dict, Optional, Type
import asyncio

logger = logging.getLogger(__name__)

class BaseAgentError(Exception):
    """Excepción base para todos los errores de agents en ATLAS."""

    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        self.agent_id = agent_id
        self.original_error = original_error
        self.context = context or {}

        # Construir mensaje completo
        full_message = f"[{agent_id}] {message}" if agent_id else message
        if original_error:
            full_message += f" | Original: {str(original_error)}"

        super().__init__(full_message)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el error a diccionario para logs/trazas."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "agent_id": self.agent_id,
            "context": self.context,
            "original_error": str(self.original_error) if self.original_error else None    
        }


def handle_errors(
    agent_id: Optional[str] = None,
    reraise: bool = True,
    log_context: bool = True
) -> Callable:
    """
    Decorador para manejo unificado de errores en agents.
    """

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                agent_id_value = agent_id
                if not agent_id_value and args:
                    instance = args[0]
                    if hasattr(instance, 'agent_id'):
                        agent_id_value = instance.agent_id

                try:
                    return await func(*args, **kwargs)
                except BaseAgentError:
                    raise
                except Exception as e:
                    error = BaseAgentError(
                        message=f"Error en {func.__name__}",
                        agent_id=agent_id_value,
                        original_error=e,
                        context={"function": func.__name__}
                    )
                    if log_context:
                        logger.error(f"ERROR: {error.to_dict()}")
                    if reraise:
                        raise error
                    return None
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                agent_id_value = agent_id
                if not agent_id_value and args:
                    instance = args[0]
                    if hasattr(instance, 'agent_id'):
                        agent_id_value = instance.agent_id

                try:
                    return func(*args, **kwargs)
                except BaseAgentError:
                    raise
                except Exception as e:
                    error = BaseAgentError(
                        message=f"Error en {func.__name__}",
                        agent_id=agent_id_value,
                        original_error=e,
                        context={"function": func.__name__}
                    )
                    if log_context:
                        logger.error(f"ERROR: {error.to_dict()}")
                    if reraise:
                        raise error
                    return None
            return sync_wrapper
    return decorator
