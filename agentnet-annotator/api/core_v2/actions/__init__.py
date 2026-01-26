"""Action system for processing user interactions."""

from .action import Action, ActionType, ActionFactory
from .processor import ActionProcessor, ActionPipeline
from .reducer import ActionReducer, ReductionStrategy

__all__ = [
    'Action',
    'ActionType', 
    'ActionFactory',
    'ActionProcessor',
    'ActionPipeline',
    'ActionReducer',
    'ReductionStrategy',
]