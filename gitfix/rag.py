import os
from concurrent.futures import as_completed, Future, ThreadPoolExecutor

import chromadb
import httpx
from bs4 import BeautifulSoup
from rich.console import Console

home_directory = os.path.expanduser("~")


class VectorDatabase:
    def __init__(self):
        self.base_url = "https://git-scm.com"
        self.client = chromadb.PersistentClient(
            path=os.path.join(home_directory, ".gitfix")
        )
        self.collection = self.client.get_or_create_collection("gitfix")

    def scrape_git_command_urls(self) -> list[str]:
        response = httpx.get(f"{self.base_url}/docs/git")
        if response.status_code != 200:
            raise

        soup = BeautifulSoup(response.text, "lxml")
        git_commands = soup.find_all("div", class_="sect1")[5]

        urls: list[str] = []
        for command in git_commands.find_all("a"):
            url: str = command.get("href")
            if not url.startswith("#"):
                urls.append(url)

        return urls

    # TODO: exclude irrelevant documentation to reduce token count
    def scrape_git_command(self, command_url: str) -> str:
        response = httpx.get(self.base_url + command_url)
        if response.status_code != 200:
            raise

        soup = BeautifulSoup(response.text, "lxml")
        documentation: str = soup.find("div", id="main").text
        return documentation

    def initialize_collection(self):
        # Vector database has to be populated once with git documentation
        if self.collection.count() == 0:
            console = Console()
            with console.status(
                "Populating vector database for RAG",
                spinner="dots",
                spinner_style="white",
            ):
                self.populate_collection()

    def populate_collection(self) -> None:
        command_urls = self.scrape_git_command_urls()

        futures: list[Future] = []
        with ThreadPoolExecutor() as executor:
            for url in command_urls:
                future = executor.submit(self.scrape_git_command, url)
                futures.append(future)

        for id, future in enumerate(as_completed(futures)):
            documentation = future.result()
            self.collection.upsert(documents=documentation, ids=[str(id)])

    def get_related_documentation(self, query: str, limit: int = 1):
        result = self.collection.query(
            query_texts=query, include=["documents"], n_results=limit
        )
        return result["documents"]