import requests
import subprocess
import sys

def testar_sistema():
    print("🔍 Testando DeluxAI...")
    
    # Teste 1: Verificar se Flask está rodando
    try:
        response = requests.get("http://127.0.0.1:5001", timeout=5)
        print("✅ Flask rodando na porta 5001")
    except:
        try:
            response = requests.get("http://127.0.0.1:5000", timeout=5)
            print("✅ Flask rodando na porta 5000")
        except:
            print("❌ Flask não está rodando")
            return False
    
    # Teste 2: Verificar Ollama
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "gemma3:1b" in result.stdout:
            print("✅ Gemma3:1b encontrado")
        else:
            print("❌ Gemma3:1b não encontrado")
    except:
        print("❌ Ollama não encontrado")
    
    return True

if __name__ == "__main__":
    testar_sistema()