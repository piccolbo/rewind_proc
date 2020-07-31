"""Interface for this package."""
from .rew import (  # noqa
    Retry,
    NamedRetry,
    checkpoint,
    retry,
    checkpoint_each_function,
    checkpoint_each_line,
    named_checkpoint,
    named_rewind,
    rewind,
    rewind_all,
)

__all__ = [
    "Retry",
    "NamedRetry",
    "checkpoint",
    "retry",
    "checkpoint_each_function",
    "checkpoint_each_line",
    "named_checkpoint",
    "named_rewind",
    "rewind",
    "rewind_all",
]

__author__ = """Antonio Piccolboni"""
__email__ = "rew@piccolboni.info"
__version__ = "__version__ = '0.1.0'"
