# src/tools/base_tool.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import logging
from src.models.agentic_models import ToolResult

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Base exception for tool execution errors"""
    
    def __init__(self, tool_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.tool_name = tool_name
        self.message = message
        self.details = details or {}
        super().__init__(f"Tool '{tool_name}' error: {message}")


class BaseTool(ABC):
    """Base class for all agentic tools"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool and return a structured result"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"Executing tool '{self.name}' with args: {kwargs}")
            result = await self._execute(**kwargs)
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            self.logger.debug(f"Tool '{self.name}' completed in {execution_time:.2f}ms")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                result=result,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            self.logger.error(f"Tool '{self.name}' failed: {error_msg}", exc_info=True)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        """Implement the actual tool logic"""
        pass
    
    def get_description(self) -> str:
        """Get tool description for LLM planning"""
        return f"Tool: {self.name}"