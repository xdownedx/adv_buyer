import re

def is_channel_public(identifier: str) -> bool:
    """Check if the provided Telegram identifier is public."""
    # Pattern for public channels and posts
    public_pattern = re.compile(r"(https?://)?t\.me/[a-zA-Z0-9_]+(/[\d]+)?$|@[a-zA-Z0-9_]+$")
    # Pattern for private channels and posts
    private_pattern = re.compile(r"(https?://)?t\.me/c/[\d]+/[\d]+$|(https?://)?t\.me/\+[a-zA-Z0-9_]+$")

    # Check the identifier against the patterns
    if public_pattern.match(identifier):
        return True
    elif private_pattern.match(identifier):
        return False
    else:
        # If the identifier doesn't match any known patterns, return False as a default
        return False
