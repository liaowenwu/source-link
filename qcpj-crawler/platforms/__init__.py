DEFAULT_PLATFORM_NAME = "benben"

# 规范化platformname。
def normalize_platform_name(value: str) -> str:
    name = (value or DEFAULT_PLATFORM_NAME).strip().lower()
    return name or DEFAULT_PLATFORM_NAME