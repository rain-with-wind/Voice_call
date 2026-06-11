"""Small terminal formatting helpers."""


class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def colored(text: str, color: str) -> str:
    return f"{color}{text}{Colors.RESET}"


def banner(title: str) -> None:
    line = "=" * 60
    print(colored(line, Colors.CYAN))
    print(colored(title, Colors.BOLD))
    print(colored(line, Colors.CYAN))


def info(text: str) -> str:
    return colored(text, Colors.BLUE)


def success(text: str) -> str:
    return colored(text, Colors.GREEN)


def warning(text: str) -> str:
    return colored(text, Colors.YELLOW)


def error(text: str) -> str:
    return colored(text, Colors.RED)
