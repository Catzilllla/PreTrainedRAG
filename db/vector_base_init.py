import chromadb

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


load_services()
print("Данные успешно загружены в ChromaDB.")
