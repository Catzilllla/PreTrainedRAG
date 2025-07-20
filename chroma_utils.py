import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
import pandas as pd

collection_name = "services"
DB_PATH = "./chroma_db"
OLLAMA_URL = "http://localhost:12000"

embedding_fn = OllamaEmbeddingFunction(model_name="mxbai-embed-large:latest", url=OLLAMA_URL)
client = chromadb.PersistentClient(path=DB_PATH)

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

# Загрузка данных из CSV
def load_services(csv_path="rag_services.csv"):
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError("CSV пуст.")
    
    services = df["Услуга"].tolist()
    metadatas = [{"price": int(row["Стоимость (руб.)"])} for _, row in df.iterrows()]
    ids = [f"service_{i}" for i in range(len(services))]

    collection = get_collection()
    collection.add(documents=services, ids=ids, metadatas=metadatas)