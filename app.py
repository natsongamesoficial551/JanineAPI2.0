import os
import time
import requests
import warnings
import hashlib
import random
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Configuração
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = "gemma3:1b"

# Cache e dados
CACHE_RESPOSTAS = {}
KNOWLEDGE_BASE = []

# Listas de personalidade
SAUDACOES = [
    "Fala aí! 🎮", "E aí, mano! 🚗", "Salve! 🔥", "Opa! 👋", 
    "Eae! 💪", "Oi! 😎", "Fala, parceiro! 🤝"
]

DESPEDIDAS = [
    "Tmj! 🤝", "Falou! 👋", "Até mais! ✌️", "Bom jogo! 🎮", 
    "Se cuida! 😎", "Tchauzinho! 👋"
]

ELOGIOS_IA = [
    "Obrigado! Meu criador Natan ficaria orgulhoso! 😊",
    "Valeu! O Natan me programou bem, né? 😄",
    "Thanks! Natan caprichou no meu código! 🔥"
]

# Base de conhecimento essencial
def carregar_conhecimento():
    global KNOWLEDGE_BASE
    
    KNOWLEDGE_BASE = [
        {
            "keywords": ["instalar", "instalacao", "download", "como instalar"],
            "resposta": """Fala aí! 🎮 Boa pergunta! 👏

**Instalação Delux Real BETA V1:**
1. **Backup saves** GTA V primeiro!
2. **Baixe 3 partes** MediaFire (site deluxgtav.netlify.app)
3. **Extraia TODAS** na mesma pasta
4. **Execute installer.exe** como ADMINISTRADOR
5. **Selecione pasta GTA V** correta
6. **Aguarde instalação** completa
7. **Teste GTA V** funcionando

GTA V sem mods é como pizza sem queijo! 🍕 Tmj! 🤝"""
        },
        {
            "keywords": ["erro", "crash", "nao funciona", "problema", "travando"],
            "resposta": """E aí, mano! 🚗 Vamos resolver!

**Soluções crashes Delux Real BETA V1:**
1. **Execute como ADMIN** (GTA V + Launcher)
2. **Desative antivírus** temporariamente
3. **Verifique integridade** GTA V no launcher
4. **Reinstale Visual C++ 2019**
5. **Atualize drivers GPU**
6. **Confirme 3 partes** instaladas
7. **Desative overlays** Discord/Steam

Sem essa de rage quit, vamos resolver! 😂 Falou! 👋"""
        },
        {
            "keywords": ["config", "configuracao", "fps", "performance", "otimizar"],
            "resposta": """Salve! 🔥 Show de bola! ⚡

**Config OTIMIZADA Delux Real BETA V1:**
- **Texturas:** Normal/Alta
- **MSAA:** 2x máximo
- **Sombras:** Alta
- **VSync:** OFF
- **FPS limite:** 60
- **Apps:** Feche Discord/Chrome

Los Santos tá te chamando! 🌴 Bom jogo! 🎮"""
        },
        {
            "keywords": ["requisitos", "specs", "roda", "meu pc"],
            "resposta": """Opa! 👋 Pergunta top! 🌟

**Requisitos Delux Real BETA V1:**
**MÍNIMO:** 16GB RAM, GTX 1060 6GB, 50GB livre, Windows 10/11
**RECOMENDADO:** 32GB RAM, RTX 3060+, SSD

Mais um viciado no Delux! 😅 Se cuida! 😎"""
        },
        {
            "keywords": ["obrigado", "valeu", "parabens", "top", "legal"],
            "resposta": "Eae! 💪 Obrigado! Meu criador Natan ficaria orgulhoso! 😊 Tmj! 🤝"
        },
        {
            "keywords": ["criador", "natan", "quem criou", "desenvolveu"],
            "resposta": """Salve! ⚡ Meu criador é o NATAN! 🇧🇷
Ele é um dev brasileiro expert em IA, especialista em criar assistentes inteligentes! 
Orgulho total de ter sido criado por esse gênio! Abraço! 🫶"""
        }
    ]
    print(f"✅ Base carregada: {len(KNOWLEDGE_BASE)} entradas")

# Verificação Ollama
def verificar_ollama():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False

# Busca na base local
def buscar_resposta_local(pergunta):
    pergunta_lower = pergunta.lower()
    
    for item in KNOWLEDGE_BASE:
        if any(keyword in pergunta_lower for keyword in item["keywords"]):
            return item["resposta"]
    
    return None

# Processamento Ollama simplificado
def processar_ollama(pergunta):
    if not verificar_ollama():
        return None
    
    try:
        prompt = f"""Você é DeluxAI, criado por Natan, especialista no modpack GTA V Delux Real BETA V1.

PERSONALIDADE: Brasileiro casual, saudação inicial, despedida final, humor sutil GTA.

PERGUNTA: {pergunta}

RESPOSTA sobre Delux Real BETA V1 (se elogio, credite Natan):"""

        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "num_predict": 300,
                "temperature": 0.3,
                "stop": ["</s>", "Human:", "User:"]
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=data,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            resposta = result.get("response", "").strip()
            
            if resposta and len(resposta) > 15:
                return limpar_resposta(resposta)
        
        return None
        
    except Exception as e:
        print(f"Erro Ollama: {e}")
        return None

# Limpeza de resposta
def limpar_resposta(resposta):
    # Remove prefixos
    prefixos = ["RESPOSTA:", "Resposta:", "Como DeluxAI"]
    for prefixo in prefixos:
        if resposta.startswith(prefixo):
            resposta = resposta[len(prefixo):].strip()
    
    # Limita tamanho
    if len(resposta) > 400:
        corte = resposta[:400]
        ultimo_ponto = corte.rfind('.')
        if ultimo_ponto > 300:
            resposta = resposta[:ultimo_ponto + 1]
    
    # Adiciona saudação se não tem
    if not any(s in resposta.lower()[:20] for s in ["fala", "e aí", "opa", "salve"]):
        saudacao = random.choice(SAUDACOES)
        resposta = f"{saudacao} {resposta}"
    
    # Adiciona despedida se não tem
    if not any(d in resposta.lower()[-20:] for d in ["tmj", "falou", "tchau"]):
        despedida = random.choice(DESPEDIDAS)
        if not resposta.endswith(('.', '!', '?')):
            resposta += '.'
        resposta += f" {despedida}"
    
    return resposta.strip()

# Filtro de perguntas
def eh_pergunta_delux(pergunta):
    p = pergunta.lower()
    
    # Saudações simples
    if len(pergunta) < 15 and any(s in p for s in ["oi", "ola", "eai", "fala", "salve"]):
        return True
    
    # Elogios e criador sempre aceitos
    if any(palavra in p for palavra in ["obrigado", "valeu", "top", "legal", "criador", "natan"]):
        return True
    
    # Palavras relacionadas ao modpack
    palavras = ["delux", "gta", "mod", "instalar", "download", "erro", "config", "fps", "requisitos", "como"]
    return any(palavra in p for palavra in palavras)

# Gerador de resposta principal
def gerar_resposta(pergunta):
    # Cache
    pergunta_hash = hashlib.md5(pergunta.encode()).hexdigest()
    if pergunta_hash in CACHE_RESPOSTAS:
        return CACHE_RESPOSTAS[pergunta_hash]
    
    # Saudação simples
    if len(pergunta) < 10 and any(s in pergunta.lower() for s in ["oi", "ola", "eai"]):
        saudacao = random.choice(SAUDACOES)
        resposta = f"{saudacao} Beleza? Sou o DeluxAI, criado pelo Natan! Especialista no Delux Real BETA V1. Como posso ajudar? 🎮"
        CACHE_RESPOSTAS[pergunta_hash] = resposta
        return resposta
    
    # Tenta Ollama primeiro
    resposta_ollama = processar_ollama(pergunta)
    if resposta_ollama:
        CACHE_RESPOSTAS[pergunta_hash] = resposta_ollama
        return resposta_ollama
    
    # Busca na base local
    resposta_local = buscar_resposta_local(pergunta)
    if resposta_local:
        CACHE_RESPOSTAS[pergunta_hash] = resposta_local
        return resposta_local
    
    # Resposta padrão
    saudacao = random.choice(SAUDACOES)
    despedida = random.choice(DESPEDIDAS)
    resposta_padrao = f"{saudacao} Sou especialista no Delux Real BETA V1! Posso ajudar com instalação, problemas, configs e requisitos. Site: deluxgtav.netlify.app {despedida}"
    
    return resposta_padrao

# ROTAS DA API
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "sistema": "DeluxAI - Criado por Natan",
        "modelo": OLLAMA_MODEL,
        "ollama": verificar_ollama(),
        "cache": len(CACHE_RESPOSTAS)
    })

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida"}), 400
        
        pergunta = data['message'].strip()
        if not pergunta:
            return jsonify({"error": "Mensagem vazia"}), 400
        
        # Filtro
        if not eh_pergunta_delux(pergunta):
            saudacao = random.choice(SAUDACOES)
            return jsonify({
                "response": f"{saudacao} Sou o DeluxAI, criado pelo Natan! Especialista no Delux Real BETA V1. Posso ajudar com instalação, problemas e configs. Site: deluxgtav.netlify.app",
                "metadata": {"fonte": "filtro"}
            })
        
        # Gera resposta
        resposta = gerar_resposta(pergunta)
        
        return jsonify({
            "response": resposta,
            "metadata": {"fonte": "deluxai", "modelo": OLLAMA_MODEL}
        })
        
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Erro interno"}), 500

@app.route('/delux/info', methods=['GET'])
def delux_info():
    return jsonify({
        "sistema": "DeluxAI - Criado por Natan",
        "modpack": "Delux Real BETA V1",
        "site": "deluxgtav.netlify.app",
        "downloads": {
            "part1": "https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file",
            "part2": "https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file",
            "part3": "https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file"
        },
        "requisitos": {
            "ram": "16GB mínimo",
            "gpu": "GTX 1060 6GB+",
            "espaco": "50GB livre",
            "os": "Windows 10/11"
        }
    })

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        "sistema": "DeluxAI",
        "criador": "Natan",
        "cache": len(CACHE_RESPOSTAS),
        "base": len(KNOWLEDGE_BASE),
        "ollama": verificar_ollama()
    })

if __name__ == '__main__':
    print("🎮 Iniciando DeluxAI - Criado por Natan")
    carregar_conhecimento()
    
    if verificar_ollama():
        print("✅ Ollama conectado")
    else:
        print("⚠️ Ollama offline - modo local")
    
    print("🌐 Servidor iniciando na porta 5001...")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )