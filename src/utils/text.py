"""
Text utilities - Parser for <mode>text</mode> tags.
"""
import re
from typing import List, Tuple, Set


def parse_annotated_text(text: str, valid_modes: Set[str] = None) -> List[Tuple[str, str]]:
    """
    Parse text with <mode>text</mode> tags.

    Args:
        text: Text with tags, e.g. "Hello <whisper>secret</whisper> world"
        valid_modes: Set of valid mode names. If None, accepts any tag name.

    Returns:
        List of (text, mode) tuples

    Examples:
        >>> parse_annotated_text("Hello <whisper>secret</whisper> world", {"whisper", "normal"})
        [("Hello ", "normal"), ("secret", "whisper"), (" world", "normal")]
    """
    pattern = r'<(\w+)>(.*?)</\1>'
    
    segments = []
    last_end = 0
    
    for match in re.finditer(pattern, text):
        mode = match.group(1).lower()
        content = match.group(2)
        
        if match.start() > last_end:
            before_text = text[last_end:match.start()]
            if before_text.strip():
                segments.append((before_text, "normal"))
        
        if valid_modes is not None and mode not in valid_modes:
            mode = "normal"
        segments.append((content, mode))
        
        last_end = match.end()
    
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining.strip():
            segments.append((remaining, "normal"))
    
    segments = [(text, mode) for text, mode in segments if len(text.strip()) > 1]
    
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
