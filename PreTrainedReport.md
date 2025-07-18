**DeepSeek локально для семантического поиска и дообучения**

## 🚀 Шаг 1: Подготовка окружения

### ✅ Установи необходимые инструменты:

    1. **Python 3.10+**
    2. **`pip` зависимости:**

    ```bash
    pip install pandas sentence-transformers chromadb torch transformers peft accelerate datasets colorama
    ```

    3. **Установи [Ollama](https://ollama.com):**

    [👉 Сайт](https://ollama.com/download) (для Linux, macOS, Windows)

    curl -fsSL https://ollama.com/install.sh | sh

    ```bash
    # Убедись, что запущен ollama
    curl http://localhost:11434
    ```
    если нет то:
    ```
    ollama --version
    ollama serve
    ```

    ```
    sudo systemctl stop ollama
    sudo systemctl disable ollama

    ```
    поменять PORT

    ```
    OLLAMA_PORT=12345 ollama serve

    ```

---

## 🔄 Шаг 2: Скачать модель DeepSeek

    Модель которая поддерживает ЧАТ:

    ```bash
    ollama pull deepseek-r1:latest
    ollama pull deepseek-r1:8b
    ```

    Модель которая поддерживает EMBEDDING:

    ```bash
    ollama pull mxbai-embed-large
    ```


    > Это скачает базовую LLM-модель. Мы её будем использовать **для эмбеддингов** и (позже) дообучения.

---

## 🧠 Шаг 3: Настроить ChromaDB с DeepSeek-эмбеддингами

### Тестирование ollama:

    ChromaDB требует Python-библиотеку ollama, чтобы взаимодействовать с локальным Ollama-сервером:

    ```bash
    pip install ollama
    ```

    Тест ollama клиента:

    ```python
    from ollama import Client

    client = Client()
    print(client.list())
    ```

### Создай файл `vector_db_setup.py`:

    ChromaDB требует Python-библиотеку ollama, чтобы взаимодействовать с локальным Ollama-сервером:

    ```bash
    pip install ollama
    ```

    Тест ollama клиента:

    ```python
    import pandas as pd
    import chromadb
    from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
    from colorama import Fore, Style

    # Загрузка CSV
    df = pd.read_csv("rag_services.csv")
    texts = df["Услуга"].tolist()

    print(texts)

    # Подключение к ChromaDB + DeepSeek через Ollama
    client = chromadb.Client()
    embedding_fn = OllamaEmbeddingFunction(model_name="deepseek-r1:8b", url="http://localhost:11434")
    collection = client.get_or_create_collection("services", embedding_function=embedding_fn)

    # Очистка (если уже существует)
    # Удаляем старую коллекцию, если есть
    try:
        client.delete_collection("services")
    except:
        pass

    # 🔁 Сразу пересоздаём
    collection = client.get_or_create_collection(
        name="services",
        embedding_function=embedding_fn
    )

    print(Fore.GREEN + f"✅ Загружено {len(texts)} услуг в векторную базу данных." + Style.RESET_ALL)

    ```

    Запусти:

    ```bash
    python vector_db_setup.py
    ```

---

## 🔍 Шаг 4: Запрос и поиск ближайшей услуги

Создай файл `semantic_search.py`:

```python
import chromadb
import pandas as pd
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

df = pd.read_csv("rag_services.csv")

client = chromadb.Client()
embedding_fn = OllamaEmbeddingFunction(model_name="deepseek-r1:8b", url="http://localhost:11434")
collection = client.get_or_create_collection("services", embedding_function=embedding_fn)

def search_service(query, threshold=0.4):
    results = collection.query(query_texts=[query], n_results=1)
    score = results["distances"][0][0]
    doc_id = results["ids"][0][0]
    
    if score <= threshold:
        service = df.iloc[int(doc_id)]["Услуга"]
        price = df.iloc[int(doc_id)]["Стоимость (руб.)"]
        return f"✅ Найдена услуга: {service} — {price} руб. (score: {score:.2f})"
    else:
        return "⚠️ Ничего точно не найдено. Вот все доступные услуги:\n" + df.to_string(index=False)

# Пример
if __name__ == "__main__":
    while True:
        user_input = input("🔎 Введите запрос (или 'выход'): ")
        if user_input.lower() in ["выход", "exit", "quit"]:
            break
        print(search_service(user_input))
```

Запусти и протестируй:

```bash
python semantic_search.py
```

---

## 🎓 Шаг 5 (по желанию): Дообучение модели DeepSeek (LoRA)

Если поиск работает, и ты хочешь сделать его **ещё точнее на своих данных**, тогда:

* Создай датасет: `["Запрос пользователя", "Целевая услуга/ответ"]`
* Я помогу тебе дообучить DeepSeek через [LoRA](https://github.com/huggingface/peft)

Готов адаптировать под твою задачу.

---

## 📦 Результат:

| Компонент            | Назначение                              |
| -------------------- | --------------------------------------- |
| `Ollama + DeepSeek`  | Генерация эмбеддингов и (в будущем) LLM |
| `ChromaDB`           | Векторная база для поиска               |
| `pandas`             | Работа с CSV                            |
| `semantic_search.py` | Терминальный интерфейс для общения      |

---

Хочешь, я помогу тебе:

* собрать датасет для дообучения?
* встроить это всё в Telegram-бота?
* или сделать локальный веб-интерфейс?

С чего продолжим?
