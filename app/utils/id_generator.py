import secrets
import string


def generate_id() -> str:
    """Generate a short, readable ID like 'OxOabtV9GAEyZzmj'"""
    # Use a mix of letters and numbers, avoiding confusing characters
    chars = string.ascii_letters + string.digits
    # Remove confusing characters: 0, O, 1, I, l
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('l', '')
    return ''.join(secrets.choice(chars) for _ in range(15))

