"""
Text utilities - Parser for <mode>text</mode> tags.
"""
import re
from typing import List, Tuple

VALID_MODES = {"whisper", "breathy", "normal", "emphatic", "processed", "radio"}


def parse_annotated_text(text: str) -> List[Tuple[str, str]]:
    """
    Parse text with <mode>text</mode> tags.

    Args:
        text: Text with tags, e.g. "Hello <whisper>secret</whisper> world"

    Returns:
        List of (text, mode) tuples

    Examples:
        >>> parse_annotated_text("Hello <whisper>secret</whisper> world")
        [("Hello ", "normal"), ("secret", "whisper"), (" world", "normal")]
    """
    # Pattern to find <mode>text</mode> tags
    pattern = r'<(\w+)>(.*?)</\1>'
    
    segments = []
    last_end = 0
    
    for match in re.finditer(pattern, text):
        mode = match.group(1).lower()
        content = match.group(2)
        
        # Add text before the tag (normal mode by default)
        if match.start() > last_end:
            before_text = text[last_end:match.start()]
            if before_text.strip():
                segments.append((before_text, "normal"))
        
        # Add tagged content
        if mode not in VALID_MODES:
            mode = "normal"
        segments.append((content, mode))
        
        last_end = match.end()
    
    # Add remaining text after the last tag
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining.strip():
            segments.append((remaining, "normal"))
    
    # Filter out empty or punctuation-only segments
    segments = [(text, mode) for text, mode in segments if len(text.strip()) > 1]
    
    # If no valid segments remain, return original text without tags
    if not segments:
        clean_text = strip_tags(text)
        return [(clean_text, "normal")] if clean_text.strip() else [(text, "normal")]
    
    return segments


def is_annotated(text: str) -> bool:
    """Check if text contains mode tags."""
    return bool(re.search(r'<\w+>.*?</\w+>', text))


def strip_tags(text: str) -> str:
    """Remove all tags from text."""
    return re.sub(r'<\w+>.*?</\w+>', lambda m: m.group(2), text)
