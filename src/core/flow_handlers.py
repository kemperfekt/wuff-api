# src/core/flow_handlers.py

"""
Compatibility shim for FlowHandlers.

The original FlowHandlers functionality has been integrated into EnhancedFlowHandlers.
This file provides backward compatibility for tests and any other code that imports FlowHandlers.
"""

from src.core.enhanced_flow_handlers import EnhancedFlowHandlers

# Re-export EnhancedFlowHandlers as FlowHandlers for backward compatibility
FlowHandlers = EnhancedFlowHandlers