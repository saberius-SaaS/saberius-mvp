import os
import subprocess
import sys
import time

port = os.environ.get("PORT", "8501")

print("🦁 [RENDER] Iniciando Diagnóstico...")

# 1. Tenta ligar a API e joga o erro na tela (stderr=sys.stdout)
print("🦁 [RENDER] Ligando API (main:app)...")
api_process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=sys.stdout,
    stderr=sys.stdout  # <--- O Segredo: Mostra o erro na tela do Render
)

# Espera 8 segundos (dá tempo do erro aparecer se tiver)
time.sleep(8)

# Verifica se a API morreu na largada
if api_process.poll() is not None:
    print("❌ [ERRO CRÍTICO] A API morreu logo após iniciar! Veja o erro acima.")
    # Não vamos matar o script, vamos deixar o streamlit subir para você ver o erro,
    # mas sabemos que vai falhar.
else:
    print("✅ [RENDER] A API parece estar viva!")

print(f"🎨 [RENDER] Iniciando Streamlit na porta {port}...")
subprocess.run([
    sys.executable, "-m", "streamlit", "run", "app_visual.py",
    "--server.port", port,
    "--server.address", "0.0.0.0"
])