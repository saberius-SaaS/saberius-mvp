import os
import subprocess
import sys
import time

# Pega a porta do Render
port = os.environ.get("PORT", "8501")

print("🦁 [RENDER] Modo Raiz Ativado.")
print(f"📂 Arquivos na pasta: {os.listdir('.')}")

# 1. Inicia a API (main.py solto na raiz)
print("🦁 [RENDER] Iniciando API (main:app) na porta 8000...")
subprocess.Popen([
    sys.executable, "-m", "uvicorn", "main:app", 
    "--host", "0.0.0.0", 
    "--port", "8000"
])

# Espera 5 segundos honestos
time.sleep(5)

# 2. Inicia o Streamlit
print(f"🎨 [RENDER] Iniciando Streamlit na porta {port}...")
subprocess.run([
    sys.executable, "-m", "streamlit", "run", "app_visual.py",
    "--server.port", port,
    "--server.address", "0.0.0.0"
])