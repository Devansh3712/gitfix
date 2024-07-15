import argparse
import os

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.text import Text

from gitfix.rag import VectorDatabase

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


def get_llm_response(log: str, context: str | None):
    db = VectorDatabase()
    documentation = db.get_related_documentation(log)

    with open(os.path.join(current_directory, "system_prompt.txt")) as infile:
        system_prompt = infile.read()

    with open(os.path.join(current_directory, "user_prompt.txt")) as infile:
        user_prompt = infile.read()
    user_prompt = user_prompt.format(log=log, documentation=documentation[0][0])

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
        },
    )
    if response.status_code != 200:
        raise
    data = response.json()
    return data["choices"][0]["message"]["content"]


def main():
    update_config()
    VectorDatabase().initialize_collection()

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
        "Fetching commands",
        spinner="dots",
        spinner_style="white",
    ):
        result = get_llm_response(log, args.context)
    print(result)
