import json
import os
from uuid import uuid4

import chromadb

from gitfix.schemas import Response


home_directory = os.path.expanduser("~")


class VectorDB:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=os.path.join(home_directory, ".gitfix")
        )
        self.cache = self.client.get_or_create_collection("gitfix_cache")

    def _generate_id(self) -> str:
        return uuid4().hex

    def add_cache(self, log: str, response: Response) -> None:
        dump = response.model_dump_json()
        self.cache.upsert(
            documents=[log],
            metadatas=[{"response": dump}],
            ids=[self._generate_id()],
        )

    def get_cache(self, log: str) -> Response | None:
        query = self.cache.query(query_texts=log, n_results=1)
        if not query["ids"][0] or query["distances"][0][0] > 0.1:
            return None
        result = json.loads(query["metadatas"][0][0]["response"])
        return Response(**result)
