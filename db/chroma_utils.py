import chromadb
from chromadb.config import Settings
import pandas as pd
import httpx
from typing import List, Callable

collection_name = "services"
OLLAMA_URL = "http://localhost:12000"

class OllamaEmbeddingFunction:
    def __init__(self, model_name="mxbai-embed-large", url="http://localhost:12000"):
        self.model = model_name
        self.url = url

    def __call__(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            payload = {
                "model": self.model,
                "prompt": text,
                "stream": False
            }
            response = httpx.post(f"{self.url}/api/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])
        return embeddings


# embedding_fn = OllamaEmbeddingFunction(model_name="mxbai-embed-large:latest", url=OLLAMA_URL)
# client = chromadb.HttpClient(host="http://localhost", port=8000)

embedding_fn = OllamaEmbeddingFunction(
    model_name="mxbai-embed-large",
    url="http://localhost:12000"
)

client = chromadb.HttpClient(host="host.docker.internal", port=8000)

collection = client.get_or_create_collection(
    name="services",
    embedding_function=embedding_fn
)

# Получаем коллекцию с эмбеддингами
def get_collection():
    try:
        return client.get_collection(name=collection_name, embedding_function=embedding_fn)
    except Exception:
        return client.create_collection(name=collection_name, embedding_function=embedding_fn)

# Поиск по запросу
def search_service(query: str, threshold: float = 0.45):
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=1)

    if results["distances"] and results["distances"][0][0] < threshold:
        doc = results["documents"][0][0]
        meta = results["metadatas"][0][0]
        score = results["distances"][0][0]
        return f"✅ Найдено:\n🛠️ Услуга: {doc}\n💰 Цена: {meta.get('price', 'Не указана')} руб.\n📏 Сходство: {score:.2f}"
    else:
        all_data = collection.get()
        output = "⚠️ Ничего похожего не найдено. Вот все доступные услуги:\n\n"
        for doc, meta in zip(all_data["documents"], all_data["metadatas"]):
            output += f" - {doc}: {meta.get('price', 'Не указана')} руб.\n"
        return output