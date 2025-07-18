# import os
# import pandas as pd
# import chromadb
# from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

# # ✅ Загрузка данных из CSV
# csv_path = "rag_services.csv"
# df = pd.read_csv(csv_path)

# if df.empty:
#     print("❌ CSV пустой.")
#     exit()

# services = df["Услуга"].tolist()
# print(f"📦 Загружено {len(services)} услуг из CSV.")

# # ✅ Настройка Chroma (новый формат)
# client = chromadb.PersistentClient(path="./chroma_db")

# # ✅ Получаем или создаем коллекцию
# collection_name = "services"
# try:
#     collection = client.get_collection(collection_name)
#     print(f"🔁 Коллекция '{collection_name}' уже существует.")
# except:
#     print(f"🆕 Создаём коллекцию '{collection_name}'...")
#     embedding_fn = OllamaEmbeddingFunction(model_name="mxbai-embed-large:latest", url="http://localhost:11434")
#     collection = client.create_collection(name=collection_name, embedding_function=embedding_fn)

# # ✅ Формируем записи
# documents = services
# ids = [f"service_{i}" for i in range(len(documents))]
# metadatas = [{"price": int(row["Стоимость (руб.)"])} for _, row in df.iterrows()]

# # ✅ Добавление в базу
# print(f"💾 Добавляем {len(documents)} документов в Chroma...")
# collection.add(documents=documents, ids=ids, metadatas=metadatas)
# print("✅ Готово.")


import logging
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Загрузка CSV с услугами
CSV_PATH = "rag_services.csv"
try:
    df = pd.read_csv(CSV_PATH)
except Exception as e:
    logging.error(f"Ошибка при чтении {CSV_PATH}: {e}")
    exit(1)

services = df["Услуга"].tolist()
prices = df["Стоимость (руб.)"].astype(str).tolist()
ids = [f"id_{i}" for i in range(len(services))]

# Подключение к ChromaDB
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(
    name="auto_services",
    embedding_function=OllamaEmbeddingFunction(model_name="mxbai-embed-large", url="http://localhost:11434")
)

# Очистка перед новой загрузкой
existing = collection.get(include=[])
if existing["ids"]:
    logging.info("Очищаем старые данные в коллекции...")
    collection.delete(ids=existing["ids"])

# Добавление новых данных
logging.info("Создание эмбеддингов и добавление услуг в базу...")
collection.add(
    ids=ids,
    documents=services,
    metadatas=[{"price": price} for price in prices]
)

logging.info("✅ Загрузка завершена. Услуги сохранены в ChromaDB.")
