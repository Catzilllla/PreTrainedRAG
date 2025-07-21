#!/bin/bash
set -e

# Ожидаем доступности chromadb (например, на http://chromadb:8000)
echo "Ожидание запуска chromadb на $CHROMA_HOST..."
until curl -s "$CHROMA_HOST" >/dev/null; do
  sleep 1
done

echo "chromadb доступен, запускаем скрипты..."

python3 vector_base_init.py
python3 chroma_utils.py
