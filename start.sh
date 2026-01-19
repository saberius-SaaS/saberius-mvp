#!/bin/bash

# 1. Inicia a API na porta 8000 em segundo plano (&)
echo "🦁 Ligando Cérebro (API)..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 2. Espera 5 segundos para garantir que a API acordou
sleep 5

# 3. Inicia o Streamlit na porta que o Render mandar ($PORT)
echo "🎨 Ligando Visual (Streamlit)..."
streamlit run app_visual.py --server.port $PORT --server.address 0.0.0.0