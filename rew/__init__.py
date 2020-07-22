"""Interface for this package."""
from .rew import (  # noqa
    checkpoint,
    rewind,
    checkpoint_each_line,
    checkpoint_each_function,
    checkpoint_deco,
    Checkpoint,
    named_checkpoint,
    named_rewind,
)

all = [
    "checkpoint",
    "rewind",
    "checkpoint_each_line",
    "checkpoint_each_function",
    "checkpoint_deco",
    "Checkpoint",
    "named_checkpoint",
    "named_rewind",
]

__author__ = """Antonio Piccolboni"""
__email__ = "autosig@piccolboni.info"
__version__ = "__version__ = '0.1.0'"
