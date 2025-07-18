import chromadb

# Создаем клиент (на диске)
client = chromadb.PersistentClient(path="./chroma_db")

# Подключаем коллекцию
collection = client.get_collection("services")

# Получаем и выводим все записи
data = collection.get()

for i in range(len(data["ids"])):
    print(f"\033[92mID:\033[0m {data['ids'][i]}")
    print(f"\033[94mДокумент:\033[0m {data['documents'][i]}")
    print(f"\033[93mМетаданные:\033[0m {data['metadatas'][i]}")
    print("-" * 50)
