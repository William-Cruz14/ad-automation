#!/bin/bash
set -e

echo "🔄 Aguardando o PostgreSQL ficar disponível..."

# Loop de tentativas com limite para não girar infinitamente
for i in {1..30}; do
    if python -c "
import socket
import sys
import os

host = os.environ.get('POSTGRES_HOST', 'postgres')
port = int(os.environ.get('POSTGRES_PORT', 5432))

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect((host, port))
    s.close()
    sys.exit(0)
except Exception as e:
    print(f'❌ Erro ao conectar em {host}:{port} -> {e}', file=sys.stderr)
    sys.exit(1)
"; then
        echo "✅ PostgreSQL disponível!"
        break
    fi

    if [ "$i" -eq 30 ]; then
        echo "🚨 Falha crítica: O PostgreSQL não ficou disponível após 30 tentativas."
        echo "Verifique se o nome do serviço no docker-compose.yml é 'postgres'."
        exit 1
    fi

    echo "⏳ Tentativa $i/30: PostgreSQL ainda não está pronto. Aguardando 2s..."
    sleep 2
done

echo "📦 Aplicando migrações do banco de dados..."
alembic upgrade head

echo "🚀 Iniciando a API..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000