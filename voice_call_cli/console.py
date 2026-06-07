class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def colored(text, color):
    return f"{color}{text}{Colors.RESET}"


def print_banner(title):
    print(colored("=" * 60, Colors.CYAN))
    print(colored(title, Colors.BOLD))
    print(colored("=" * 60, Colors.CYAN))


def success(text):
    return colored(text, Colors.GREEN)


def warning(text):
    return colored(text, Colors.YELLOW)


def error(text):
    return colored(text, Colors.RED)


def info(text):
    return colored(text, Colors.BLUE)


def accent(text):
    return colored(text, Colors.CYAN)


def bold(text):
    return colored(text, Colors.BOLD)


def format_volume_bar(volume, length=20):
    filled = int(volume * length)
    bar = "#" * filled + "-" * (length - filled)

    if volume < 0.3:
        color = Colors.GREEN
    elif volume < 0.7:
        color = Colors.YELLOW
    else:
        color = Colors.RED

    return colored(bar, color)
