import os
import time
import requests
import warnings
import hashlib
import random
import re
import json
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Configuração
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = "gemma3:1b"
RENDER_URL = os.getenv("RENDER_URL", "")

# Cache e dados melhorados
CACHE_RESPOSTAS = {}
KNOWLEDGE_BASE = []
HISTORICO_CONVERSAS = []
PING_INTERVAL = 300

# Auto-ping para manter servidor ativo
def auto_ping():
    while True:
        try:
            if RENDER_URL:
                requests.get(f"{RENDER_URL}/health", timeout=10)
                print(f"🏓 Auto-ping realizado: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"❌ Erro no auto-ping: {e}")
        time.sleep(PING_INTERVAL)

threading.Thread(target=auto_ping, daemon=True).start()

# Personalidade melhorada
SAUDACOES = [
    "Fala aí! 🎮", "E aí, mano! 🚗", "Salve! 🔥", "Opa! 👋", 
    "Eae! 💪", "Oi! 😎", "Fala, parceiro! 🤝", "E aí, gamer! 🎯"
]

DESPEDIDAS = [
    "Tmj! 🤝", "Falou! 👋", "Até mais! ✌️", "Bom jogo! 🎮", 
    "Se cuida! 😎", "Partiu RP! 🔥", "Vai na fé! 🙏"
]

# Sistema de análise de intenção MELHORADO
def analisar_intencao(pergunta):
    """Analisa a intenção real do usuário"""
    p = pergunta.lower()
    
    # Remove palavras irrelevantes para melhor análise
    p_limpa = re.sub(r'\b(como|eu|essa|essa|merda|porra|caralho)\b', '', p)
    
    intencoes = {
        "instalacao": 0,
        "gameplay": 0,
        "problema": 0,
        "download": 0,
        "requisitos": 0,
        "contato": 0,
        "saudacao": 0,
        "opiniao": 0
    }
    
    # Palavras-chave ESPECÍFICAS para cada intenção
    palavras_instalacao = [
        "instala", "instalacao", "instalar", "install", "como instalar", 
        "passo a passo", "tutorial instalacao", "instalo", "instalando",
        "extrair", "executar", "administrador", "pasta do gta", "script hook"
    ]
    
    palavras_gameplay = [
        "jogar", "jogo", "como joga", "gameplay", "controles", "como usar",
        "fome", "sede", "trabalho", "emprego", "casa", "propriedade", "sistemas"
    ]
    
    palavras_problema = [
        "erro", "crash", "crashando", "problema", "nao funciona", "travando",
        "bugou", "nao abre", "nao roda", "fps baixo", "lag"
    ]
    
    palavras_download = [
        "baixar", "download", "onde baixo", "link", "mediafire", "partes",
        "arquivos", "site oficial"
    ]
    
    palavras_requisitos = [
        "requisitos", "specs", "meu pc", "roda", "compativel", "gtx", "ram",
        "processador", "pc fraco", "configuracao"
    ]
    
    # Conta ocorrências
    for palavra in palavras_instalacao:
        if palavra in p:
            intencoes["instalacao"] += 3 if len(palavra) > 7 else 2
    
    for palavra in palavras_gameplay:
        if palavra in p:
            intencoes["gameplay"] += 2
    
    for palavra in palavras_problema:
        if palavra in p:
            intencoes["problema"] += 3
    
    for palavra in palavras_download:
        if palavra in p:
            intencoes["download"] += 3
    
    for palavra in palavras_requisitos:
        if palavra in p:
            intencoes["requisitos"] += 2
    
    # Saudações
    if len(pergunta) < 15 and any(s in p for s in ["oi", "ola", "eai", "fala", "salve"]):
        intencoes["saudacao"] = 10
    
    # Opiniões
    if any(op in p for op in ["vale pena", "é bom", "recomenda", "opiniao"]):
        intencoes["opiniao"] = 3
    
    # Retorna a intenção com maior score
    intencao_principal = max(intencoes, key=intencoes.get)
    score_principal = intencoes[intencao_principal]
    
    return intencao_principal if score_principal > 1 else "geral"

# Base de conhecimento SUPER ESPECÍFICA
def carregar_conhecimento_especializado():
    global KNOWLEDGE_BASE
    
    KNOWLEDGE_BASE = {
        "instalacao": {
            "resposta": """Fala aí! 🎮 INSTALAÇÃO COMPLETA Delux Modpack v Beta 1.0:

**ANTES DE COMEÇAR:**
✅ **GTA V Original** - Steam/Epic/Rockstar (atualizado)
✅ **Backup dos saves** - Documents/Rockstar Games/GTA V
✅ **20GB livres** no disco
✅ **Antivírus DESATIVADO** temporariamente

**PRÉ-REQUISITOS OBRIGATÓRIOS:**
1. **Script Hook V** - Versão mais recente
2. **OpenIV** - Instalado e configurado  
3. **Visual C++ 2015-2022** - Todas versões
4. **.NET Framework 4.8** - Atualizado

**PASSO A PASSO DETALHADO:**
1. **SITE OFICIAL:** deluxgtav.netlify.app
2. **BAIXE AS 3 PARTES** (MediaFire) na mesma pasta
3. **EXTRAIA TUDO** juntos (não separe!)
4. **FECHE GTA V** completamente
5. **EXECUTE O INSTALLER como ADMINISTRADOR**
6. **SELECIONE A PASTA** do GTA V:
   - Steam: C:/Program Files/Steam/steamapps/common/Grand Theft Auto V
   - Epic: C:/Program Files/Epic Games/GTAV
   - Rockstar: C:/Program Files/Rockstar Games/GTA V
7. **AGUARDE INSTALAÇÃO** (15-30 min)
8. **REINICIE O PC** se solicitado
9. **ABRA GTA V** normalmente

**SE DER PROBLEMA:**
- Verificar integridade dos arquivos
- Reinstalar Script Hook V
- Executar sempre como administrador
- Pasta correta do GTA V selecionada

Instalação perfeita = RP perfeito! 🔥 Partiu Los Santos! 🇧🇷""",
            "keywords": ["instala", "instalacao", "instalar", "install", "passo", "tutorial", "como instalar"]
        },
        
        "download": {
            "resposta": """Salve! 🔥 DOWNLOADS OFICIAIS Delux Modpack v Beta 1.0:

**🌐 SITE OFICIAL ÚNICO:**
**deluxgtav.netlify.app**
⚠️ **ATENÇÃO:** Outros sites = VÍRUS garantido!

**📁 ARQUIVOS NECESSÁRIOS:**
1. **Installer(Delux Real BETA) V1 - part1.rar**
2. **Installer(Delux Real BETA) V1 - part2.rar**  
3. **Installer(Delux Real BETA) V1 - part3.rar**

**COMO BAIXAR:**
1. Acesse **deluxgtav.netlify.app**
2. Clique nos links **MediaFire**
3. Aguarde 5 segundos no MediaFire
4. Clique "**Download**"
5. Baixe **TODAS AS 3 PARTES** na mesma pasta
6. **NÃO EXTRAIA** ainda!

**VERIFICAÇÃO:**
✅ Part1.rar baixado completo
✅ Part2.rar baixado completo  
✅ Part3.rar baixado completo
✅ Todos na mesma pasta
✅ ~15GB total

**PROBLEMAS COMUNS:**
❌ **Link não abre:** Limpe cache do navegador
❌ **Download lento:** Use VPN se necessário
❌ **Arquivo corrompido:** Baixe novamente
❌ **MediaFire travado:** Aguarde e tente novamente

**SEGURANÇA:**
- NUNCA baixe de outros sites
- Natan só publica no site oficial
- Links sempre MediaFire

Download seguro = modpack seguro! 📥 Tmj! 🤝""",
            "keywords": ["baixar", "download", "onde baixar", "link", "mediafire", "site", "oficial"]
        },
        
        "gameplay": {
            "resposta": """E aí! 🎮 COMO JOGAR Delux Modpack v Beta 1.0:

**PRIMEIROS PASSOS:**
1. **Abra GTA V** normalmente
2. **Selecione "Story Mode"**
3. **Aguarde carregar** (demora mais agora)
4. **Explore as novidades!**

**⭐ SISTEMAS PRINCIPAIS:**

**🍔 FOME E SEDE:**
- Barras aparecem na interface
- **TAB:** Verificar necessidades
- Vá a: Cluckin' Bell, Burger Shot, 24/7
- **E:** Interagir com comércios

**💼 TRABALHOS:**
- **F6:** Menu de empregos
- Disponíveis: Taxista, Caminhoneiro, Paramédico
- Vá ao local indicado no mapa
- Ganhe dinheiro realisticamente

**🏠 CASAS:**
- Procure placas "À VENDA"
- **E:** Ver detalhes da propriedade
- Compre com dinheiro do trabalho
- Benefícios: Spawn, garagem, descanso

**🚗 CARROS REALISTAS:**
- Combustível limitado
- Abasteça em postos
- Sons brasileiros
- Danos mais realistas

**CONTROLES ESPECIAIS:**
- **TAB:** Status (fome/sede)
- **F6:** Menu trabalhos
- **E:** Interações gerais
- **M:** Mapa com locais

**DICAS PRO:**
1. Comece arranjando um emprego
2. Sempre cuide da fome/sede
3. Economize dinheiro para casa própria
4. Explore os mapas brasileiros
5. Faça RP realista sempre!

É uma vida virtual completa! 🇧🇷 Bom RP! 🔥""",
            "keywords": ["jogar", "jogo", "como joga", "gameplay", "controles", "sistemas", "fome", "sede"]
        },
        
        "requisitos": {
            "resposta": """Fala! 💻 REQUISITOS SISTEMA Delux Modpack v Beta 1.0:

**⚡ MÍNIMOS (30-40 FPS):**
- **OS:** Windows 10 64-bit
- **CPU:** Intel i5-4460 / AMD FX-6300
- **RAM:** 8GB (16GB recomendado)
- **GPU:** GTX 1050 Ti 4GB / RX 570 4GB
- **Storage:** 20GB livres (SSD recomendado)

**🔥 RECOMENDADOS (60+ FPS):**
- **OS:** Windows 11 64-bit
- **CPU:** Intel i7-8700K / AMD Ryzen 5 3600
- **RAM:** 16GB DDR4
- **GPU:** GTX 1660 Super / RX 6600 XT
- **Storage:** SSD com 25GB livres

**🚀 IDEAIS (Ultra 1080p):**
- **CPU:** Intel i7-10700K / AMD Ryzen 7 3700X
- **RAM:** 32GB DDR4
- **GPU:** RTX 3060 Ti / RX 6700 XT
- **Storage:** NVMe SSD

**📊 ANÁLISE POR PLACA:**

**GTX 1050/1050 Ti:**
⚠️ Roda mas limitado
- Configs LOW/MEDIUM
- 720p/1080p: 30-45 FPS
- ReShade OFF inicialmente

**GTX 1060 6GB:**
✅ Performance boa
- Configs MEDIUM/HIGH
- 1080p: 45-60 FPS
- ReShade ON possível

**RTX 3060/4060:**
🔥 Performance excelente
- Configs HIGH/ULTRA
- 1080p: 60-80 FPS
- ReShade completo

**⚠️ IMPORTANTE:**
- **Launcher:** Steam/Epic/Rockstar (original)
- **Antivírus:** Desativar durante instalação
- **Espaço:** 20GB+ livres sempre
- **Internet:** Para downloads das 3 partes

**PC FRACO?**
- Feche outros programas
- Modo Alto Performance
- Limite FPS em 30
- Texturas baixas primeiro

Seu PC roda? Me fala as specs! 🎯 Tmj! 🤝""",
            "keywords": ["requisitos", "specs", "meu pc", "roda", "compativel", "placa", "ram", "fps"]
        },
        
        "problema": {
            "resposta": """E aí! 🛠️ SOLUÇÃO DE PROBLEMAS Delux Modpack v Beta 1.0:

**❌ GTA V NÃO ABRE:**
1. **Verificar integridade** dos arquivos (Steam/Epic)
2. **Reinstalar Script Hook V** (versão atual)
3. **Executar como ADMINISTRADOR**
4. **Desativar antivírus** temporariamente
5. **Reiniciar PC** completamente

**💥 CRASH AO CARREGAR:**
1. **Atualizar Visual C++** 2015-2022
2. **Verificar .NET Framework** 4.8+
3. **Limpar cache** do GTA V
4. **Modo compatibilidade** Windows 10
5. **Reinstalar** o modpack

**🐌 FPS BAIXO/TRAVANDO:**
1. **Configs gráficas BAIXAS**
2. **ReShade OFF** inicialmente  
3. **Fechar outros programas**
4. **Modo Alto Performance** Windows
5. **Verificar temperatura** PC

**⚠️ ERRO "SCRIPT HOOK":**
1. Baixar **Script Hook V** atualizado
2. Extrair na **pasta do GTA V**
3. **ScriptHookV.dll** na raiz do jogo
4. **Não usar** com GTA Online

**🔄 MODPACK NÃO DETECTADO:**
1. **Pasta correta** do GTA V selecionada
2. **Todas as 3 partes** baixadas
3. **Extrair juntas** na mesma pasta
4. **Executar installer** como ADMIN

**💾 SAVE CORROMPIDO:**
1. **Backup** em Documents/Rockstar Games
2. **Verificar espaço** em disco
3. **Não misturar** com outros mods
4. **Save limpo** do GTA V

**🆘 PROBLEMAS ESPECÍFICOS:**
- **"Memória insuficiente":** Feche programas
- **"Arquivo não encontrado":** Reinstale modpack
- **"Acesso negado":** Execute como admin
- **"DLL missing":** Instale dependências

**ÚLTIMA TENTATIVA:**
1. **Desinstalar** modpack
2. **Verificar integridade** GTA V
3. **Limpar** pasta temp
4. **Reinstalar** tudo limpo

Me fala o erro específico que te ajudo melhor! 🔧 Tmj! 🤝""",
            "keywords": ["erro", "crash", "problema", "nao funciona", "travando", "fps baixo", "bugou"]
        },
        
        "saudacao": {
            "resposta": """Salve! 🔥 

Beleza aí? Sou o **DeluxAI**, criado pelo **Natan Borges**!

Especialista no **Delux Modpack v Beta 1.0** - o modpack brasileiro que transforma GTA V num RP realista completo!

**Posso te ajudar com:**
🎮 **Instalação** passo a passo
📥 **Downloads** oficiais seguros  
🛠️ **Problemas** técnicos
💻 **Requisitos** do sistema
🎯 **Gameplay** e sistemas RP
📞 **Contato** direto com Natan

**Site oficial:** deluxgtav.netlify.app

No que posso ajudar hoje? 🤝""",
            "keywords": ["oi", "ola", "eai", "fala", "salve", "hey", "bom dia"]
        }
    }
    
    print(f"✅ Base ESPECIALIZADA carregada: {len(KNOWLEDGE_BASE)} categorias")

# Busca inteligente MELHORADA
def buscar_resposta_especializada(pergunta):
    intencao = analisar_intencao(pergunta)
    
    print(f"🎯 Intenção detectada: {intencao}")
    
    if intencao in KNOWLEDGE_BASE:
        return KNOWLEDGE_BASE[intencao]["resposta"]
    
    return None

# Processamento Ollama FOCADO
def processar_ollama_focado(pergunta, intencao):
    if not verificar_ollama():
        return None
    
    try:
        # Prompts específicos por intenção
        prompts = {
            "instalacao": "Explique como instalar o Delux Modpack passo a passo:",
            "gameplay": "Ensine como jogar e usar os sistemas do Delux Modpack:",
            "problema": "Resolva este problema técnico do Delux Modpack:",
            "download": "Explique como baixar o Delux Modpack com segurança:",
            "requisitos": "Analise se este PC roda o Delux Modpack:",
            "geral": "Responda sobre o Delux Modpack:"
        }
        
        prompt_base = prompts.get(intencao, prompts["geral"])
        
        prompt = f"""Você é DeluxAI, criado por Natan Borges, especialista EXCLUSIVO no Delux Modpack v Beta 1.0 para GTA V.

PERSONALIDADE: Brasileiro descontraído, direto, útil.

INFORMAÇÕES ESSENCIAIS:
- Site oficial: deluxgtav.netlify.app
- Criador: Natan Borges 
- Contato: borgesnatan09@gmail.com, WhatsApp +55 21 99282-6074
- Instagram: @Ntzinnn87

FOCO: {intencao.upper()}

{prompt_base} {pergunta}

Resposta direta e prática (máximo 400 palavras):"""

        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "num_predict": 300,
                "temperature": 0.2,
                "top_k": 20,
                "top_p": 0.8,
                "repeat_penalty": 1.2,
                "stop": ["</s>", "Human:", "PERGUNTA:"]
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
            
            if resposta and len(resposta) > 20:
                return limpar_resposta_focada(resposta)
        
        return None
        
    except Exception as e:
        print(f"❌ Erro Ollama: {e}")
        return None

# Limpeza focada
def limpar_resposta_focada(resposta):
    # Remove prefixos desnecessários
    prefixos = [
        "Resposta direta e prática:", "DeluxAI:", "Como DeluxAI",
        "RESPOSTA:", "Resposta:", "FOCO:"
    ]
    
    for prefixo in prefixos:
        if resposta.startswith(prefixo):
            resposta = resposta[len(prefixo):].strip()
    
    # Limita tamanho
    if len(resposta) > 800:
        corte = resposta[:800]
        ultimo_ponto = corte.rfind('.')
        if ultimo_ponto > 600:
            resposta = resposta[:ultimo_ponto + 1]
    
    # Adiciona saudação se não tiver
    if not any(s in resposta.lower()[:20] for s in ["fala", "e aí", "opa", "salve"]):
        saudacao = random.choice(["Fala aí! 🎮", "Opa! 👋", "Salve! 🔥"])
        resposta = f"{saudacao} {resposta}"
    
    # Adiciona despedida se não tiver
    if not any(d in resposta.lower()[-30:] for d in ["tmj", "falou", "🤝", "🔥"]):
        despedida = random.choice(["Tmj! 🤝", "Falou! 👋", "Bom jogo! 🎮"])
        resposta += f" {despedida}"
    
    return resposta.strip()

# Verificação melhorada
def eh_pergunta_delux_focada(pergunta):
    p = pergunta.lower()
    
    # Sempre aceita saudações
    if len(pergunta) < 20 and any(s in p for s in ["oi", "ola", "eai", "fala", "salve"]):
        return True
    
    # Keywords específicas
    keywords_delux = [
        "delux", "gta", "mod", "modpack", "instalar", "instalacao", "install",
        "baixar", "download", "erro", "crash", "problema", "requisitos", 
        "jogar", "gameplay", "como", "natan", "site", "oficial"
    ]
    
    return any(keyword in p for keyword in keywords_delux)

# Gerador principal OTIMIZADO
def gerar_resposta_otimizada(pergunta):
    # Cache melhorado
    pergunta_hash = hashlib.md5(pergunta.lower().strip().encode()).hexdigest()
    
    if pergunta_hash in CACHE_RESPOSTAS:
        return CACHE_RESPOSTAS[pergunta_hash]
    
    # Analisa intenção
    intencao = analisar_intencao(pergunta)
    print(f"🎯 Intenção: {intencao} para: '{pergunta[:50]}...'")
    
    # Busca na base especializada primeiro
    resposta_especializada = buscar_resposta_especializada(pergunta)
    if resposta_especializada:
        CACHE_RESPOSTAS[pergunta_hash] = resposta_especializada
        print("✅ Resposta da base especializada")
        return resposta_especializada
    
    # Tenta Ollama focado
    resposta_ollama = processar_ollama_focado(pergunta, intencao)
    if resposta_ollama:
        CACHE_RESPOSTAS[pergunta_hash] = resposta_ollama
        print("✅ Resposta do Ollama focado")
        return resposta_ollama
    
    # Resposta de fallback
    resposta_fallback = f"Opa! 👋 Sou especialista no Delux Modpack v Beta 1.0. Me pergunta sobre instalação, downloads, problemas, requisitos ou gameplay! Site oficial: deluxgtav.netlify.app 🎮"
    
    CACHE_RESPOSTAS[pergunta_hash] = resposta_fallback
    print("⚠️ Resposta fallback")
    return resposta_fallback

# Verificação Ollama
def verificar_ollama():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False

# ROTAS DA API

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online_otimizado",
        "sistema": "DeluxAI ESPECIALIZADO v3.0 - Criado por Natan Borges",
        "especialidade": "Delux Modpack v Beta 1.0",
        "modelo": OLLAMA_MODEL,
        "ollama_ativo": verificar_ollama(),
        "cache_size": len(CACHE_RESPOSTAS),
        "categorias": list(KNOWLEDGE_BASE.keys()) if KNOWLEDGE_BASE else [],
        "melhorias_v3": [
            "Sistema de intenções específico",
            "Respostas por categoria",
            "Análise contextual melhorada",
            "Cache otimizado por hash",
            "Base de conhecimento especializada",
            "Prompts focados por tipo"
        ]
    })

@app.route('/chat', methods=['POST'])
def chat_otimizado():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida"}), 400
        
        pergunta = data['message'].strip()
        if not pergunta:
            return jsonify({"error": "Mensagem vazia"}), 400
        
        print(f"💬 [{datetime.now().strftime('%H:%M:%S')}] Pergunta: {pergunta}")
        
        # Filtro melhorado
        if not eh_pergunta_delux_focada(pergunta):
            resposta_filtro = "Opa! 🎮 Sou o DeluxAI, especialista no Delux Modpack v Beta 1.0 criado pelo Natan Borges. Posso ajudar com: instalação, downloads, problemas, requisitos, gameplay RP. Site oficial: deluxgtav.netlify.app - Me pergunta algo específico! 🤝"
            return jsonify({
                "response": resposta_filtro,
                "metadata": {
                    "fonte": "filtro_especializado",
                    "tipo": "redirecionamento"
                }
            })
        
        # Gera resposta otimizada
        resposta = gerar_resposta_otimizada(pergunta)
        
        # Determina fonte
        intencao = analisar_intencao(pergunta)
        if intencao in KNOWLEDGE_BASE:
            fonte = f"base_especializada_{intencao}"
        elif verificar_ollama():
            fonte = f"ollama_focado_{intencao}"
        else:
            fonte = "fallback_contextual"
        
        return jsonify({
            "response": resposta,
            "metadata": {
                "fonte": fonte,
                "intencao": intencao,
                "modelo": OLLAMA_MODEL,
                "sistema": "DeluxAI_v3_Especializado"
            }
        })
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({
            "response": "Eae! 😅 Deu um probleminha aqui. Tenta novamente ou me pergunta sobre instalação, downloads, problemas do Delux Modpack! 🔧",
            "error": "erro_temporario"
        }), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "sistema": "DeluxAI v3.0 - Auto-Ping Ativo"
    })

if __name__ == '__main__':
    print("🎮 Iniciando DeluxAI ESPECIALIZADO v3.0")
    print("=" * 60)
    print("👨‍💻 Criado por: Natan Borges")  
    print("📧 Contato: borgesnatan09@gmail.com")
    print("📱 WhatsApp: +55 21 99282-6074")
    print("🌐 Site: deluxgtav.netlify.app")
    print("=" * 60)
    
    # Carrega base especializada
    carregar_conhecimento_especializado()
    
    # Status
    if verificar_ollama():
        print("✅ Ollama CONECTADO - Modo Híbrido Especializado")
    else:
        print("⚠️ Ollama offline - Modo Base Especializada")
    
    print("🎯 Sistema de intenções ativo")
    print("📚 Base de conhecimento por categorias")
    print("🔄 Auto-ping ativo (5min)")
    print("🚀 Servidor iniciando na porta 5001...")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )