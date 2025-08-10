"""LLM-based translation tools for JHipster documentation."""

__version__ = "0.1.0"

from config import config
from file_filters import FileFilters
from git_utils import GitUtils
from line_diff import LineDiffAnalyzer
from llm import GeminiTranslator
from placeholder import PlaceholderManager
from reflow import TextReflower
from segmenter import TextSegmenter

__all__ = [
    "config",
    "FileFilters",
    "GitUtils",
    "GeminiTranslator",
    "PlaceholderManager",
    "TextSegmenter",
    "TextReflower",
    "LineDiffAnalyzer",
]
