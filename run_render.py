import os
import subprocess
import sys
import time

# Pega a porta que o Render quer usar (ou 8501 se for local)
port = os.environ.get("PORT", "8501")

print("🦁 [RENDER] Iniciando API na porta 8000...")

# 1. Inicia a API em Segundo Plano (subprocesso)
# Usamos sys.executable para garantir que é o mesmo Python
api_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "app.main:app", 
    "--host", "0.0.0.0", 
    "--port", "8000"
])

# Espera um pouco a API acordar
time.sleep(5)

print(f"🎨 [RENDER] Iniciando Streamlit na porta {port}...")

# 2. Inicia o Streamlit (Bloqueia o script aqui para o Render não achar que acabou)
subprocess.run([
    sys.executable, "-m", "streamlit", "run", "app_visual.py",
    "--server.port", port,
    "--server.address", "0.0.0.0"
])