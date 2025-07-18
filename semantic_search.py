# import chromadb
# import pandas as pd
# from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

# df = pd.read_csv("rag_services.csv")

# client = chromadb.Client()
# embedding_fn = OllamaEmbeddingFunction(model_name="mxbai-embed-large", url="http://localhost:11434")
# collection = client.get_or_create_collection("services", embedding_function=embedding_fn)

# def search_service(query: str, threshold: float = 0.45):
#     results = collection.query(query_texts=[query], n_results=1)

#     if not results["documents"] or not results["documents"][0]:
#         # Нет результатов — возвращаем все доступные услуги
#         all_docs = collection.get()["documents"]
#         return "🚫 Ничего не найдено. Вот весь список услуг:\n" + "\n".join([doc for doc in all_docs])

#     # Есть хотя бы один результат
#     matched_doc = results["documents"][0][0]
#     score = results["distances"][0][0]
    
#     if score > threshold:
#         return f"✅ Найдена услуга:\n{matched_doc}\n(similarity: {score:.2f})"
#     else:
#         all_docs = collection.get()["documents"]
#         return f"❗ Похожих услуг не найдено (score={score:.2f}). Вот весь список:\n" + "\n".join([doc for doc in all_docs])


# # Пример
# if __name__ == "__main__":
#     while True:
#         user_input = input("🔎 Введите запрос (или 'выход'): ")
#         if user_input.lower() in ["выход", "exit", "quit"]:
#             break
#         print(search_service(user_input))


import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from termcolor import colored

# Настройки подключения к постоянной базе
client = chromadb.PersistentClient(path="./chroma_db")

# Подключение к коллекции
collection_name = "services"
embedding_fn = OllamaEmbeddingFunction(model_name="mxbai-embed-large:latest", url="http://localhost:11434")

try:
    collection = client.get_collection(name=collection_name, embedding_function=embedding_fn)
except Exception as e:
    print(colored(f"❌ Ошибка подключения к коллекции: {e}", "red"))
    exit(1)

# Семантический поиск
def search_service(query: str, threshold: float = 0.45):
    results = collection.query(query_texts=[query], n_results=1)

    if results["distances"] and results["distances"][0] and results["distances"][0][0] < threshold:
        doc = results["documents"][0][0]
        meta = results["metadatas"][0][0]
        score = results["distances"][0][0]
        return colored(f"✅ Найдено: {doc}\nЦена: {meta.get('price', 'Не указана')}\nСходство: {score:.2f}", "green")
    else:
        all_data = collection.get()
        output = colored("⚠️ Ничего похожего не найдено. Вот все доступные услуги:\n", "yellow")
        for doc, meta in zip(all_data["documents"], all_data["metadatas"]):
            output += f" - {doc}: {meta.get('price', 'Не указана')} руб.\n"
        return output

# CLI
print(colored("🔎 Введите запрос (или 'выход'):", "cyan"))
while True:
    user_input = input(" > ").strip()
    if user_input.lower() in ("выход", "exit", "quit"):
        break
    print(search_service(user_input))
