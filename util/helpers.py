# normalize_strings
def normalize_strings(input_string):
    """Normalize a string by stripping whitespace and converting to lowercase one space between words."""
    return ' '.join(input_string.strip().lower().split()) if input_string else None
