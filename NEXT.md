Отлично, если ты используешь **ChromaDB в Docker**, вот как **загрузить данные из CSV** в неё пошагово. Это почти то же самое, но с учётом Docker-среды.

---

## ⚙️ Структура (предположим)

```
project/
├── docker-compose.yml
├── rag_services.csv
├── chroma_utils.py
├── init_data.py       ← будем запускать для загрузки
└── botFSM.py
```

---

## ✅ 1. Убедись, что твой контейнер ChromaDB запущен

Проверь:

```bash
docker compose ps
```

И убедись, что `chroma` или `chromadb` контейнер работает и слушает порт `8000`.

---

## ✅ 2. Проверь доступ из Python-клиента

В `chroma_utils.py`, функция подключения должна выглядеть так:

```python
import chromadb

def get_collection():
    client = chromadb.HttpClient(host="localhost", port=8000)  # без http://
    return client.get_or_create_collection("services")  # или другое имя коллекции
```

Если Python-код находится **на хост-машине**, `localhost:8000` работает.
Если Python-код запущен **в другом контейнере** — нужно использовать имя контейнера (`chroma` или `chromadb`), или `host.docker.internal`.

---

## ✅ 3. Убедись, что CSV доступен

Файл `rag_services.csv` должен быть **на стороне хоста**, и если ты запускаешь код в Docker-контейнере, нужно пробросить файл:

```yaml
volumes:
  - ./rag_services.csv:/app/rag_services.csv
```

---

## ✅ 4. Загрузка данных: `init_data.py`

```python
from chroma_utils import get_collection
import pandas as pd

def load_services(csv_path="rag_services.csv"):
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError("CSV пуст.")

    services = df["Услуга"].tolist()
    metadatas = [{"price": int(row["Стоимость (руб.)"])} for _, row in df.iterrows()]
    ids = [f"service_{i}" for i in range(len(services))]

    collection = get_collection()
    collection.delete(where={})  # Очистить, если нужно
    collection.add(documents=services, ids=ids, metadatas=metadatas)

load_services()
print("✅ Данные успешно загружены в ChromaDB.")
```

---

## ✅ 5. Запуск

Если ты запускаешь **на хосте** (не в контейнере):

```bash
python init_data.py
```

Если ты хочешь выполнить это **в контейнере**, добавь сервис в `docker-compose.yml`:

```yaml
services:
  bot:
    build: .
    volumes:
      - .:/app
    depends_on:
      - chromadb
    command: python init_data.py
```

И выполни:

```bash
docker compose up bot
```

---

## ✅ 6. Проверка

После загрузки, можно вручную проверить из Python:

```python
collection = get_collection()
print(collection.count())  # Должно вывести количество записей
```

---

Хочешь — покажи свой `docker-compose.yml`, я помогу адаптировать под твой случай.
