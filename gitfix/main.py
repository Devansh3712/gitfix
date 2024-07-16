import argparse
import json
import os
import subprocess
import webbrowser

import httpx
from dotenv import load_dotenv
from pygments import highlight
from pygments.lexers import BashLexer
from pygments.formatters import TerminalFormatter
from rich.console import Console
from rich.text import Text
from simple_term_menu import TerminalMenu

from gitfix.schemas import Response, Type

home_directory = os.path.expanduser("~")
current_directory = os.path.dirname(os.path.realpath(__file__))
console = Console()

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def update_config() -> None:
    with open("scripts/output.sh") as infile:
        config = infile.read()

    with open(os.path.join(home_directory, ".bashrc"), mode="r+") as file:
        if config not in file.read():
            file.write(config)
            text = Text()
            text.append("[+]", style="green")
            text.append(
                " .bashrc updated, please execute 'source ~/.bashrc' for changes to take effect"
            )
            console.print(text)
            exit(0)


def get_llm_response(log: str, context: str | None) -> Response:
    with open(os.path.join(current_directory, "system_prompt.txt")) as infile:
        system_prompt = infile.read()

    user_prompt = f"[COMMAND OUTPUT]\n{log}\n"

    if context is not None:
        user_prompt += f"\n[USER CONTEXT]\n{context}"

    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "model": "llama3-70b-8192",
            "response_format": {"type": "json_object"},
        },
    )
    if response.status_code != 200:
        raise

    data = response.json()
    result = data["choices"][0]["message"]["content"]
    suggestions = json.loads(result)
    return Response(**suggestions)


def main():
    update_config()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--context",
        type=str,
        help="additional user context",
        required=False,
    )
    args = parser.parse_args()

    with open(os.path.join(home_directory, ".gitfix", "git.log")) as infile:
        log = infile.read()

    with console.status(
        "Fetching suggestions",
        spinner="dots",
        spinner_style="white",
    ):
        result = get_llm_response(log, args.context)

    def get_preview(selected: str) -> str | None:
        if selected == "Exit":
            return None

        suggestion = result.suggestions[selected]
        explanation = suggestion.explanation

        match suggestion.type_:
            case Type.COMMAND:
                command = highlight(
                    suggestion.command, BashLexer(), TerminalFormatter()
                )
                return f"{command}\n{explanation}"
            case _:
                return explanation

    console.print(f"[bold] {result.error}\n")

    while True:
        suggestions = list(result.suggestions.keys()) + ["Exit"]
        terminal_menu = TerminalMenu(
            menu_entries=suggestions,
            preview_command=get_preview,
            preview_title="Explanation",
            preview_size=0.75,
            menu_cursor="➤ ",
            menu_cursor_style=("fg_purple",),
        )
        terminal_menu.show()

        entry = terminal_menu.chosen_menu_entry
        if entry == "Exit":
            exit(0)

        suggestion = result.suggestions[entry]
        match suggestion.type_:
            case Type.COMMAND:
                command_args = suggestion.command.split(" ")
                subprocess.run(command_args)
                result.suggestions.pop(entry)
            case Type.DOCUMENTATION:
                webbrowser.open_new_tab(suggestion.url)
            case _:
                pass
