"""@file voice_call.py
@brief Project entrypoint for the Voice Call CLI application.

This file keeps backward compatibility with the original single-file startup
command while delegating the actual command parsing logic to the packaged CLI
module.
"""

from voice_call_cli.cli import main


if __name__ == "__main__":
    main()
