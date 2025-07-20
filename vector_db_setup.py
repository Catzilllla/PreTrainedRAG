import os
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

# ✅ Загрузка данных из CSV
csv_path = "rag_services.csv"
df = pd.read_csv(csv_path)

if df.empty:
    print("❌ CSV пустой.")
    exit()

services = df["Услуга"].tolist()
print(f"📦 Загружено {len(services)} услуг из CSV.")

# ✅ Настройка Chroma (новый формат)
client = chromadb.PersistentClient(path="./chroma_db")

# ✅ Получаем или создаем коллекцию
collection_name = "services"
try:
    collection = client.get_collection(collection_name)
    print(f"🔁 Коллекция '{collection_name}' уже существует.")
except:
    print(f"🆕 Создаём коллекцию '{collection_name}'...")
    embedding_fn = OllamaEmbeddingFunction(model_name="mxbai-embed-large:latest", url="http://localhost:12000")
    collection = client.create_collection(name=collection_name, embedding_function=embedding_fn)

# ✅ Формируем записи
documents = services
ids = [f"service_{i}" for i in range(len(documents))]
metadatas = [{"price": int(row["Стоимость (руб.)"])} for _, row in df.iterrows()]

# ✅ Добавление в базу
print(f"💾 Добавляем {len(documents)} документов в Chroma...")
collection.add(documents=documents, ids=ids, metadatas=metadatas)
print("✅ Готово.")
