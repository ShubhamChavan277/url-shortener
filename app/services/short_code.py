import secrets
import string


SHORT_CODE_LENGTH = 8
SHORT_CODE_ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    """Generate a random URL-safe short code."""
    return "".join(
        secrets.choice(SHORT_CODE_ALPHABET)
        for _ in range(length)
    )