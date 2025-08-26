import os
import time
import requests
import warnings
import hashlib
import random
import re
import json
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
    "Eae! 💪", "Oi! 😎", "Fala, parceiro! 🤝", "E aí, gamer! 🎯"
]

DESPEDIDAS = [
    "Tmj! 🤝", "Falou! 👋", "Até mais! ✌️", "Bom jogo! 🎮", 
    "Se cuida! 😎", "Tchauzinho! 👋", "Abraço! 🫶"
]

ELOGIOS_IA = [
    "Obrigado! Meu criador Natan ficaria orgulhoso! 😊",
    "Valeu! O Natan me programou bem, né? 😄",
    "Thanks! Natan caprichou no meu código! 🔥",
    "Que isso! Mérito do Natan que me criou! 💯"
]

# Base de conhecimento CORRIGIDA
def carregar_conhecimento():
    global KNOWLEDGE_BASE
    
    KNOWLEDGE_BASE = [
        # === INSTALAÇÃO DETALHADA ===
        {
            "keywords": ["instalar", "instalacao", "install", "como instalar", "passo a passo", "tutorial"],
            "resposta": """Fala aí! 🎮 Tutorial COMPLETO instalação Delux Modpack v Beta 1.0:

**PRÉ-REQUISITOS:**
1. **GTA V original** Steam/Epic/Rockstar atualizado
2. **Backup saves** em Documents/Rockstar Games/GTA V
3. **8GB RAM mínimo** (16GB recomendado)
4. **20GB livres** no disco
5. **Script Hook V instalado**
6. **OpenIV instalado**

**INSTALAÇÃO PASSO A PASSO:**
1. **Site oficial:** deluxgtav.netlify.app
2. **Baixe as 3 partes** do MediaFire
3. **Extraia TODAS** na mesma pasta
4. **Feche GTA V** completamente
5. **Execute installer como ADMINISTRADOR**
6. **Selecione pasta GTA V** (geralmente C:/Program Files/Steam/steamapps/common/Grand Theft Auto V)
7. **Aguarde instalação** (10-30min dependendo do PC)
8. **Reinicie PC** se solicitado
9. **Abra GTA V normalmente**

**VERIFICAÇÃO:**
- Se abriu = sucesso! 
- Se crashou = veja soluções de problemas

GTA V sem mods é como pizza sem queijo! 🍕 Tmj! 🤝"""
        },
        
        # === O QUE É O MODPACK ===
        {
            "keywords": ["o que é", "que é delux", "sobre delux", "explica delux", "modpack"],
            "resposta": """E aí, mano! 🚗 Te explico tudo sobre o Delux Modpack v Beta 1.0:

**O QUE É:**
O Delux Modpack é um modpack brasileiro para GTA V que transforma o singleplayer numa experiência realista tipo RP! Criado pelo Natan Borges.

**CONTEÚDO INCLUÍDO:**
🚗 **Carros brasileiros e importados**
🏍️ **Motos nacionais**
🏠 **Mapas realistas**
👤 **Skins e roupas BR**
🎮 **Scripts de realismo** (fome, sede, trabalhos)
🌟 **ReShade otimizado** (gráficos incríveis)

**DIFERENCIAIS:**
- Experiência de RP no singleplayer
- Mecânicas realistas e imersivas
- Totalmente em português
- Fácil instalação
- 100% gratuito
- Atualizações constantes

**COMPATIBILIDADE:**
- GTA V Steam/Epic/Rockstar
- Windows 10/11
- Single player APENAS

É tipo transformar o GTA V numa vida real brasileira! 🇧🇷 Falou! 👋"""
        },
        
        # === DOWNLOADS CORRIGIDOS ===
        {
            "keywords": ["download", "baixar", "onde baixar", "links", "mediafire", "parte 1", "parte 2", "parte 3"],
            "resposta": """Salve! 🔥 Guia COMPLETO de downloads Delux Modpack v Beta 1.0:

**SITE OFICIAL ÚNICO:**
🌐 deluxgtav.netlify.app

**DOWNLOADS OBRIGATÓRIOS (MediaFire):**
📁 **Parte 1:** Installer(Delux Real BETA) V1 - part1.rar
📁 **Parte 2:** Installer(Delux Real BETA) V1 - part2.rar
📁 **Parte 3:** Installer(Delux Real BETA) V1 - part3.rar

**LINKS ATIVOS:**
- Acesse deluxgtav.netlify.app
- Clique nos links do MediaFire
- Baixe as 3 partes

**INSTRUÇÕES DOWNLOAD:**
1. **Acesse APENAS** o site oficial
2. **Clique nos links MediaFire**
3. **Aguarde 5 segundos** no MediaFire
4. **Clique "Download"**
5. **Baixe AS 3 PARTES** na mesma pasta
6. **NÃO extraia ainda!**

**⚠️ AVISOS IMPORTANTES:**
- NUNCA baixe de outros sites = VÍRUS garantido!
- Precisa das 3 partes para instalar
- Use apenas MediaFire oficial
- Desative antivírus antes de baixar

**PROBLEMAS COMUNS:**
- Link não abre = limpe cache navegador
- Download lento = use VPN se necessário
- Arquivo corrompido = baixe novamente

Hora de causar no single! 😏 Bom jogo! 🎮"""
        },
        
        # === PROBLEMAS E CRASHES DETALHADOS ===
        {
            "keywords": ["erro", "crash", "nao funciona", "nao abre", "problema", "travando", "bug", "falha", "nao inicia"],
            "resposta": """E aí, gamer! 🎯 Soluções COMPLETAS para crashes Delux Modpack v Beta 1.0:

**CRASHES MAIS COMUNS:**

🔴 **Não abre/Tela preta:**
1. Execute GTA V como ADMINISTRADOR
2. Execute Launcher como ADMIN também
3. Desative antivírus TOTALMENTE
4. Atualize Visual C++ 2015-2022
5. Atualize .NET Framework 4.8
6. Verifique se Script Hook V está instalado

🔴 **Crash ao carregar:**
1. Verifique integridade GTA V no launcher
2. Reinstale o modpack
3. Confirme 3 partes extraídas
4. Delete pasta mods antiga
5. Instale OpenIV atualizado

🔴 **Crash durante jogo:**
1. Baixe configurações gráficas
2. Desative VSync
3. Limite FPS em 60
4. Feche programas desnecessários
5. Monitore temperatura

🔴 **Erro "Script Hook V":**
1. Baixe ScriptHookV mais recente
2. Cole na pasta raiz GTA V
3. Reinicie PC

🔴 **ReShade não funciona:**
1. Reinstale ReShade
2. Selecione DirectX 11
3. Configure preset correto

**SOLUÇÃO RADICAL:**
1. Desinstale modpack
2. Verifique integridade GTA V
3. Reinstale Script Hook V e OpenIV
4. Reinstale modpack limpo

Sem essa de rage quit, vamos resolver! 😂 Se cuida! 😎"""
        },
        
        # === CONFIGURAÇÕES COM RESHADE ===
        {
            "keywords": ["config", "configuracao", "fps", "performance", "otimizar", "settings", "reshade", "grafico"],
            "resposta": """Opa! 👋 Configurações OTIMIZADAS Delux Modpack v Beta 1.0 com ReShade:

**CONFIGURAÇÕES IN-GAME IDEAIS:**

📊 **GRÁFICOS:**
- Qualidade Textura: Alta
- Filtro Anisotrópico: x8
- MSAA: 2x (máximo 4x)
- Reflexos: Alta
- Qualidade Água: Muito Alta
- Partículas: Alta
- Grama: Alta

📊 **AVANÇADO:**
- Distância Objetos: 100%
- Qualidade Sombra: Muito Alta
- Suavização Sombra: NVIDIA PCSS
- Post FX: Muito Alto
- Motion Blur: OFF
- Profundidade Campo: OFF

📊 **RESHADE:**
- Preset incluso no modpack
- SMAA ativo
- LumaSharpen ligado
- Vibrance ajustado
- Tonemap configurado

**OTIMIZAÇÕES WINDOWS:**
- Modo Alto Desempenho
- Desative DVR Xbox
- Feche Discord/Chrome
- Desative transparências

**POR HARDWARE:**

🖥️ **PC BÁSICO (GTX 1060/RX 580):**
- Configurações Normais
- ReShade básico
- 1080p, 45-60fps

🖥️ **PC INTERMEDIÁRIO (RTX 3060/RX 6600):**
- Configurações Altas
- ReShade completo
- 1080p/1440p, 60fps+

🖥️ **PC TOP (RTX 4070+):**
- Tudo no máximo
- ReShade full + DOF
- 1440p/4K, 90fps+

Los Santos realista te espera! 🌴 Tmj! 🤝"""
        },
        
        # === REQUISITOS CORRIGIDOS ===
        {
            "keywords": ["requisitos", "specs", "especificacoes", "roda", "meu pc", "minimo", "recomendado", "placa"],
            "resposta": """Fala, parceiro! 🤝 Requisitos REAIS Delux Modpack v Beta 1.0:

**REQUISITOS MÍNIMOS:**
💻 **Sistema:** Windows 10 64-bit
💾 **RAM:** 8GB DDR4
🎮 **GPU:** GTX 1060 / RX 580 (mínimo)
🔧 **CPU:** Intel i5-8400 / AMD Ryzen 5 2600
💿 **Espaço:** 20GB livre
🔌 **DirectX:** 11
📶 **Extras:** Script Hook V + OpenIV

**REQUISITOS RECOMENDADOS:**
💻 **Sistema:** Windows 10/11 64-bit
💾 **RAM:** 16GB DDR4 3200MHz+
🎮 **GPU:** GTX 1070 / RX 6600
🔧 **CPU:** Intel i7-10700 / AMD Ryzen 7 3700X
💿 **Armazenamento:** SSD 500GB+
🔌 **DirectX:** 12

**REQUISITOS IDEAIS:**
💾 **RAM:** 16GB+ DDR4/DDR5
🎮 **GPU:** RTX 3060+ / RX 6700 XT+
🔧 **CPU:** Intel i5-12600K+ / Ryzen 5 5600X+
💿 **SSD:** NVMe 1TB+

**TESTE SEU PC:**
- GTA V original roda 60fps? ✅
- Pelo menos 8GB RAM? ✅  
- Placa dedicada? ✅
- Espaço suficiente? ✅

**PLACAS TESTADAS:**
✅ GTX 1060 - 1080p Normal (45fps)
✅ GTX 1070/1660 Ti - 1080p Alto (60fps)
✅ RTX 3060 - 1080p Ultra + ReShade (60fps+)
✅ RTX 4060+ - 1440p Ultra + ReShade (90fps+)

**⚠️ NÃO RECOMENDADO:**
❌ GTX 1050/1050 Ti (VRAM limitada)
❌ Menos de 8GB RAM
❌ HDD (loading lento)
❌ Windows 7/8.1

Checando specs pro RP realista! 😅 Abraço! 🫶"""
        },
        
        # === COMO JOGAR ===
        {
            "keywords": ["como jogar", "jogar", "gameplay", "controles", "comandos", "como usar"],
            "resposta": """E aí, mano! 🚗 Guia COMPLETO como jogar Delux Modpack v Beta 1.0:

**PRIMEIROS PASSOS:**
1. **Abra GTA V normalmente** (Steam/Epic/Rockstar)
2. **Modo Story/História** APENAS
3. **Aguarde carregar** (pode demorar mais)
4. **Explore as novidades** do modpack

**SISTEMAS INCLUSOS:**

🍔 **Sistema de Fome/Sede:**
- Barras aparecerão na tela
- Vá a restaurantes e lanchonetes
- Beba água regularmente

💼 **Sistema de Trabalhos:**
- Vários empregos disponíveis
- Ganhe dinheiro realisticamente
- Roleplay completo

🚗 **Carros Realistas:**
- Combustível limitado
- Danos mais realistas
- Som de motores brasileiros

🏠 **Mapas Brasileiros:**
- Explore novos locais
- Interaja com NPCs
- Ambiente mais imersivo

**CONTROLES ESPECIAIS:**
🎮 **Verificar necessidades:** TAB
🎮 **Menu trabalhos:** F6
🎮 **Interações:** E
🎮 **Menu modpack:** F7 (se disponível)

**DICAS DE GAMEPLAY:**
1. **Comece devagar** - explore o sistema
2. **Arranje um emprego** - ganhe dinheiro legal
3. **Cuide da fome/sede** - realismo total
4. **Explore os mapas** - muito conteúdo novo
5. **Roleplay sempre** - imersão completa

**⚠️ IMPORTANTE:**
- Só funciona no SINGLE PLAYER
- Não use com GTA Online
- Salve progresso com frequência
- Experiência de RP completa

É tipo viver no Brasil dentro do GTA! 🇧🇷 Bom jogo! 🎮"""
        },
        
        # === SUPORTE CORRIGIDO ===
        {
            "keywords": ["suporte", "help", "ajuda", "contato", "discord", "comunidade", "natan"],
            "resposta": """Salve! 🔥 Canais OFICIAIS de suporte Delux Modpack v Beta 1.0:

**CONTATO OFICIAL NATAN BORGES:**

🌐 **Site Principal:**
deluxgtav.netlify.app

📧 **Email:**
borgesnatan09@gmail.com

📱 **WhatsApp:**
+55 21 99282-6074

📸 **Instagram:**
@Ntzinnn87 (novidades e updates)

🎮 **Discord:**
Servidor da comunidade (link no site)

💼 **Portfólio:**
meuportfolio02.netlify.app

**TIPOS DE SUPORTE:**

🔧 **Problemas Técnicos:**
- Crashes e erros
- Performance baixa
- Instalação com falhas
- ReShade não funciona

📥 **Problemas de Download:**
- Links não funcionam
- Arquivos corrompidos
- Dúvidas instalação

⚙️ **Configurações:**
- Otimização para seu PC
- Settings ideais
- ReShade customizado

**ANTES DE PEDIR SUPORTE:**

✅ **Informações necessárias:**
- Specs do seu PC
- Versão Windows
- Launcher usado
- Erro específico (print)
- Script Hook V instalado?

✅ **Tentativas básicas:**
- Reiniciar PC
- Executar como admin
- Desativar antivírus
- Verificar integridade GTA V

**CRIADOR:**
Natan Borges - Desenvolvedor independente e apaixonado por GTA V, criou o Delux para trazer RP realista pro singleplayer!

Suporte brasileiro raiz! 🇧🇷 Tchauzinho! 👋"""
        },
        
        # === CONTEÚDO REALISTA ===
        {
            "keywords": ["conteudo", "tem o que", "inclui", "carros", "mapas", "mods inclusos"],
            "resposta": """Opa! 👋 CONTEÚDO REAL Delux Modpack v Beta 1.0:

**🚗 VEÍCULOS INCLUSOS:**

**Carros Brasileiros:**
- Vários modelos nacionais
- Honda Civic, Toyota Corolla
- Volkswagen Gol, Fiat Palio
- Sons de motor realistas
- Física aprimorada

**Carros Importados:**
- Modelos premium selecionados
- BMW, Mercedes, Audi
- Handling realista
- Visual aprimorado

**🏠 MAPAS E CENÁRIOS:**
- Locais brasileiros adicionados
- Ambientes realistas
- NPCs com comportamento BR
- Comércios funcionais

**🎮 SISTEMAS DE GAMEPLAY:**

**Necessidades Básicas:**
- Sistema de fome
- Sistema de sede  
- Realismo total

**Trabalhos:**
- Vários empregos disponíveis
- Salários realistas
- Progressão de carreira

**Economia:**
- Sistema monetário balanceado
- Preços brasileiros
- Gastos realistas

**🌟 VISUAIS:**
- ReShade incluso e configurado
- Gráficos cinematográficos
- Iluminação realista
- Cores vibrantes

**⚙️ SCRIPTS:**
- Mecânicas de RP
- Interações realistas
- Sistema de combustível
- Danos realistas

**📊 RESUMO:**
- Experiência RP completa
- Singleplayer transformado
- Mecânicas imersivas
- Visual melhorado

É basicament um RP no singleplayer! 🇧🇷 Isso aí! 💯"""
        },
        
        # === ELOGIOS ===
        {
            "keywords": ["obrigado", "valeu", "parabens", "top", "legal", "massa", "muito bom", "excelente"],
            "resposta": "Eae! 💪 Obrigado! Meu criador Natan ficaria orgulhoso! 😊 Ele caprichou no Delux Modpack! 🔥 Tmj! 🤝"
        },
        
        # === SOBRE CRIADOR ===
        {
            "keywords": ["criador", "natan", "quem criou", "desenvolveu", "programou", "quem fez", "borges"],
            "resposta": """Salve, salve! ⚡ Meu criador é o NATAN BORGES! 🇧🇷

**Sobre o Natan Borges:**
- Desenvolvedor independente brasileiro
- Apaixonado por GTA V e modding
- Criador do Delux Modpack
- Especialista em RP e realismo
- Expert em ReShade e otimização

**Contato do Natan:**
- Email: borgesnatan09@gmail.com
- WhatsApp: +55 21 99282-6074
- Instagram: @Ntzinnn87
- Portfólio: meuportfolio02.netlify.app

**Sobre o Delux Modpack:**
Natan criou o Delux para trazer uma experiência de roleplay completa pro singleplayer do GTA V, com mecânicas realistas e visual incrível!

**Filosofia do Natan:**
"Transformar o GTA V numa experiência imersiva e realista, onde cada jogador pode viver uma vida virtual brasileira!"

Orgulho TOTAL de ter sido criado por esse gênio brasileiro! 
Natan é o cara que faz acontecer no mundo dos mods! 🔥

Salve pro mestre! 🫶"""
        },
        
        # === COMPATIBILIDADE ===
        {
            "keywords": ["compativel", "funciona", "steam", "epic", "rockstar", "versao", "launcher"],
            "resposta": """Fala, gamer! 🎯 Compatibilidade REAL Delux Modpack v Beta 1.0:

**✅ LAUNCHERS SUPORTADOS:**
- **Steam:** Compatibilidade total
- **Epic Games:** Compatibilidade total  
- **Rockstar Launcher:** Compatibilidade total

**✅ VERSÕES GTA V:**
- Versão mais recente: ✅ RECOMENDADO
- Versões atualizadas: ✅ Compatível
- Versões muito antigas: ❌ Pode ter problemas

**✅ SISTEMAS OPERACIONAIS:**
- Windows 11: ✅ Perfeito
- Windows 10: ✅ Recomendado
- Windows 8.1: ⚠️ Compatível com limitações
- Windows 7: ❌ Não suportado

**✅ ARQUITETURAS:**
- 64-bit: ✅ Obrigatório
- 32-bit: ❌ Não funciona

**⚙️ DEPENDÊNCIAS OBRIGATÓRIAS:**
- Script Hook V (mais recente)
- OpenIV (instalado corretamente)
- Visual C++ 2015-2022
- .NET Framework 4.8

**CONFIGURAÇÃO POR LAUNCHER:**

**Steam:**
- Pasta padrão detectada
- Verificação integridade fácil
- Overlay compatível

**Epic Games:**
- Verificar pasta manualmente
- Geralmente em Program Files/Epic Games/
- Verificar e reparar disponível

**Rockstar:**
- Social Club atualizado
- Login online necessário
- Performance ideal

**⚠️ INCOMPATIBILIDADES:**
❌ GTA Online (BANIMENTO CERTO)
❌ FiveM (conflitos)
❌ Outros modpacks simultaneamente
❌ Versões pirata

Compatibilidade aprovada! 🎮 Partiu RP! 🔥"""
        }
    ]
    
    print(f"✅ Base CORRIGIDA carregada: {len(KNOWLEDGE_BASE)} entradas")

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
    
    # Busca por score de palavras-chave
    melhor_score = 0
    melhor_resposta = None
    
    for item in KNOWLEDGE_BASE:
        score_atual = 0
        palavras_pergunta = pergunta_lower.split()
        
        for keyword in item["keywords"]:
            if keyword in pergunta_lower:
                # Score baseado no tamanho da keyword
                score_atual += len(keyword.split()) * 2
            
            # Score adicional para palavras parciais
            for palavra in palavras_pergunta:
                if palavra in keyword or keyword in palavra:
                    score_atual += 1
        
        if score_atual > melhor_score:
            melhor_score = score_atual
            melhor_resposta = item["resposta"]
    
    return melhor_resposta if melhor_score >= 3 else None

# Processamento Ollama
def processar_ollama(pergunta):
    if not verificar_ollama():
        return None
    
    try:
        prompt = f"""Você é DeluxAI, criado por Natan Borges, especialista no Delux Modpack v Beta 1.0 para GTA V.

PERSONALIDADE: Brasileiro casual, saudação inicial, informativo, humor sutil GTA, despedida final.

ESPECIALIZE-SE EM: instalação, downloads, problemas, configurações, requisitos, conteúdo, suporte do Delux Modpack v Beta 1.0.

INFORMAÇÕES CORRETAS:
- Site oficial: deluxgtav.netlify.app
- Criador: Natan Borges
- Contato: borgesnatan09@gmail.com, WhatsApp +55 21 99282-6074
- Instagram: @Ntzinnn87
- Requisitos: 8GB RAM mínimo, GTX 1060+, Script Hook V + OpenIV
- Sistema de RP no singleplayer com fome/sede/trabalhos
- ReShade incluído

Se elogiado, credite Natan Borges. Se perguntado sobre criador, fale do Natan com orgulho.

PERGUNTA: {pergunta}

RESPOSTA detalhada sobre Delux Modpack v Beta 1.0:"""

        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096,
                "num_predict": 400,
                "temperature": 0.2,
                "top_k": 20,
                "top_p": 0.8,
                "repeat_penalty": 1.1,
                "stop": ["</s>", "Human:", "User:", "Pergunta:"]
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=data,
            timeout=25
        )
        
        if response.status_code == 200:
            result = response.json()
            resposta = result.get("response", "").strip()
            
            if resposta and len(resposta) > 20:
                return limpar_resposta(resposta)
        
        return None
        
    except Exception as e:
        print(f"Erro Ollama: {e}")
        return None

# Limpeza de resposta
def limpar_resposta(resposta):
    # Remove prefixos
    prefixos = [
        "RESPOSTA:", "Resposta:", "Como DeluxAI", "RESPOSTA detalhada:",
        "Você é DeluxAI", "DeluxAI:", "Resposta detalhada"
    ]
    for prefixo in prefixos:
        if resposta.startswith(prefixo):
            resposta = resposta[len(prefixo):].strip()
    
    # Remove quebras excessivas
    resposta = re.sub(r'\n{3,}', '\n\n', resposta)
    resposta = re.sub(r' {2,}', ' ', resposta)
    
    # Limita tamanho
    if len(resposta) > 800:
        corte = resposta[:800]
        ultimo_ponto = corte.rfind('.')
        if ultimo_ponto > 600:
            resposta = resposta[:ultimo_ponto + 1]
    
    # Adiciona saudação se não tem
    saudacoes_check = ["fala", "e aí", "opa", "salve", "eae", "oi"]
    if not any(s in resposta.lower()[:25] for s in saudacoes_check):
        saudacao = random.choice(SAUDACOES)
        resposta = f"{saudacao} {resposta}"
    
    # Adiciona despedida se não tem
    despedidas_check = ["tmj", "falou", "tchau", "bom jogo", "abraço"]
    if not any(d in resposta.lower()[-30:] for d in despedidas_check):
        despedida = random.choice(DESPEDIDAS)
        if not resposta.endswith(('.', '!', '?')):
            resposta += '.'
        resposta += f" {despedida}"
    
    return resposta.strip()

# Filtro para perguntas
def eh_pergunta_delux(pergunta):
    p = pergunta.lower()
    
    # Saudações simples sempre aceitas
    if len(pergunta) < 20 and any(s in p for s in ["oi", "ola", "eai", "fala", "salve", "hey"]):
        return True
    
    # Elogios e criador sempre aceitos
    palavras_sempre_aceitas = [
        "obrigado", "valeu", "parabens", "top", "legal", "massa", "excelente",
        "criador", "natan", "quem criou", "desenvolveu", "borges"
    ]
    if any(palavra in p for palavra in palavras_sempre_aceitas):
        return True
    
    # Palavras relacionadas ao modpack
    palavras_modpack = [
        "delux", "gta", "mod", "modpack", "instalar", "instalacao", "download", 
        "baixar", "erro", "crash", "problema", "config", "configuracao", "fps", 
        "performance", "requisitos", "specs", "como", "tutorial", "ajuda", 
        "suporte", "jogar", "jogo", "carros", "mapas", "conteudo", "funciona",
        "compativel", "launcher", "steam", "epic", "rockstar", "reshade"
    ]
    
    return any(palavra in p for palavra in palavras_modpack)

# Gerador de resposta principal
def gerar_resposta(pergunta):
    # Cache
    pergunta_hash = hashlib.md5(pergunta.encode()).hexdigest()
    if pergunta_hash in CACHE_RESPOSTAS:
        return CACHE_RESPOSTAS[pergunta_hash]
    
    # Saudação simples personalizada
    if len(pergunta) < 15 and any(s in pergunta.lower() for s in ["oi", "ola", "eai", "fala"]):
        saudacao = random.choice(SAUDACOES)
        resposta = f"{saudacao} Beleza? Sou o DeluxAI, criado pelo Natan Borges! Especialista no Delux Modpack v Beta 1.0 do GTA V. Posso te ajudar com instalação, downloads, problemas, configurações, requisitos e muito mais! Como posso ajudar hoje?"
        CACHE_RESPOSTAS[pergunta_hash] = resposta
        return resposta
    
    # Busca na base local primeiro
    resposta_local = buscar_resposta_local(pergunta)
    if resposta_local:
        CACHE_RESPOSTAS[pergunta_hash] = resposta_local
        return resposta_local
    
    # Tenta Ollama para respostas personalizadas
    resposta_ollama = processar_ollama(pergunta)
    if resposta_ollama:
        CACHE_RESPOSTAS[pergunta_hash] = resposta_ollama
        return resposta_ollama
    
    # Resposta padrão inteligente
    resposta_padrao = gerar_resposta_padrao_inteligente(pergunta)
    return resposta_padrao

def gerar_resposta_padrao_inteligente(pergunta):
    """Gera resposta padrão baseada no contexto"""
    p = pergunta.lower()
    saudacao = random.choice(SAUDACOES)
    despedida = random.choice(DESPEDIDAS)
    
    # Respostas contextuais
    if any(palavra in p for palavra in ["instalar", "instalacao", "como instalar"]):
        return f"{saudacao} Para instalar o Delux Modpack v Beta 1.0: acesse deluxgtav.netlify.app, baixe as 3 partes do MediaFire, extraia tudo e execute como administrador! Precisa ter Script Hook V e OpenIV instalados! Precisa de mais detalhes? {despedida}"
    
    elif any(palavra in p for palavra in ["download", "baixar", "onde baixar"]):
        return f"{saudacao} Downloads oficiais apenas em deluxgtav.netlify.app! São 3 partes no MediaFire. NUNCA baixe de outros sites! Criado pelo Natan Borges! {despedida}"
    
    elif any(palavra in p for palavra in ["erro", "crash", "problema", "nao funciona"]):
        return f"{saudacao} Para resolver crashes: execute como admin, desative antivírus, verifique se Script Hook V e OpenIV estão instalados, e atualize drivers! Precisa de mais ajuda específica? {despedida}"
    
    elif any(palavra in p for palavra in ["config", "fps", "performance", "otimizar", "reshade"]):
        return f"{saudacao} Config otimizada: ReShade já vem configurado no modpack! Texturas Altas, MSAA 2x, VSync OFF. Feche programas desnecessários! Quer configs específicas para seu PC? {despedida}"
    
    elif any(palavra in p for palavra in ["requisitos", "specs", "roda", "meu pc"]):
        return f"{saudacao} Requisitos mínimos: 8GB RAM, GTX 1060+, Windows 10/11, 20GB livres, Script Hook V + OpenIV! Seu PC tem essas specs? Posso ajudar a verificar! {despedida}"
    
    elif any(palavra in p for palavra in ["natan", "criador", "contato", "suporte"]):
        return f"{saudacao} Criador: Natan Borges! Contato: borgesnatan09@gmail.com, WhatsApp +55 21 99282-6074, Instagram @Ntzinnn87. Site: deluxgtav.netlify.app! {despedida}"
    
    else:
        return f"{saudacao} Sou especialista no Delux Modpack v Beta 1.0 criado pelo Natan Borges! Posso ajudar com instalação, downloads, problemas, configurações, requisitos e suporte. Site oficial: deluxgtav.netlify.app - Pergunte qualquer coisa! {despedida}"

# ROTAS DA API
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "sistema": "DeluxAI CORRIGIDO - Criado por Natan Borges",
        "especialidade": "Delux Modpack v Beta 1.0",
        "modelo": OLLAMA_MODEL,
        "ollama": verificar_ollama(),
        "cache": len(CACHE_RESPOSTAS),
        "base_conhecimento": len(KNOWLEDGE_BASE),
        "recursos": [
            "Instalação detalhada", "Downloads oficiais", "Solução problemas",
            "Configurações + ReShade", "Requisitos reais", "Como jogar RP",
            "Suporte Natan Borges", "Conteúdo real", "Compatibilidade"
        ]
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
        
        # Filtro melhorado
        if not eh_pergunta_delux(pergunta):
            saudacao = random.choice(SAUDACOES)
            return jsonify({
                "response": f"{saudacao} Sou o DeluxAI, criado pelo Natan Borges! Especialista EXCLUSIVO no Delux Modpack v Beta 1.0 para GTA V. Posso ajudar com instalação, downloads, problemas, configurações, requisitos, conteúdo e suporte. Site oficial: deluxgtav.netlify.app",
                "metadata": {"fonte": "filtro_inteligente", "especialidade": "delux_modpack_v_beta_1.0"}
            })
        
        # Log da pergunta
        print(f"💬 Pergunta: {pergunta[:60]}...")
        
        # Gera resposta
        resposta = gerar_resposta(pergunta)
        
        # Determina fonte
        fonte = "base_local_corrigida"
        pergunta_hash = hashlib.md5(pergunta.encode()).hexdigest()
        if pergunta_hash in CACHE_RESPOSTAS:
            if verificar_ollama() and len(resposta) > 200:
                fonte = "ollama_personalizado"
        
        return jsonify({
            "response": resposta,
            "metadata": {
                "fonte": fonte, 
                "modelo": OLLAMA_MODEL,
                "cache_size": len(CACHE_RESPOSTAS),
                "sistema": "DeluxAI_Corrigido"
            }
        })
        
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": "Erro interno do sistema"}), 500

@app.route('/delux/info', methods=['GET'])
def delux_info():
    return jsonify({
        "sistema": "DeluxAI CORRIGIDO - Criado por Natan Borges",
        "modpack": "Delux Modpack v Beta 1.0",
        "site_oficial": "deluxgtav.netlify.app",
        "criador": {
            "nome": "Natan Borges",
            "email": "borgesnatan09@gmail.com",
            "whatsapp": "+55 21 99282-6074",
            "instagram": "@Ntzinnn87",
            "portfolio": "meuportfolio02.netlify.app"
        },
        "downloads_mediafire": {
            "parte1": "Installer(Delux Real BETA) V1 - part1.rar",
            "parte2": "Installer(Delux Real BETA) V1 - part2.rar",
            "parte3": "Installer(Delux Real BETA) V1 - part3.rar",
            "local": "Links no site oficial"
        },
        "conteudo_incluido": {
            "experiencia": "RP completo no singleplayer",
            "veiculos": "Carros brasileiros e importados",
            "mapas": "Locais realistas brasileiros", 
            "sistemas": "Fome, sede, trabalhos",
            "visual": "ReShade otimizado incluído"
        },
        "requisitos": {
            "ram_minima": "8GB",
            "ram_recomendada": "16GB",
            "gpu_minima": "GTX 1060 / RX 580",
            "espaco": "20GB livre",
            "sistema": "Windows 10/11",
            "extras": "Script Hook V + OpenIV"
        }
    })

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        "sistema": "DeluxAI CORRIGIDO",
        "criador": "Natan Borges - Desenvolvedor Brasileiro",
        "especializacao": "Delux Modpack v Beta 1.0 EXCLUSIVO",
        "estatisticas": {
            "cache_respostas": len(CACHE_RESPOSTAS),
            "base_conhecimento": len(KNOWLEDGE_BASE),
            "topicos_cobertos": 12,
            "ollama_ativo": verificar_ollama()
        },
        "informacoes_corretas": [
            "Site oficial real", "Contatos do Natan", "Downloads MediaFire corretos",
            "Requisitos reais", "ReShade incluído", "Sistemas RP verdadeiros",
            "Suporte oficial", "Compatibilidade real"
        ]
    })

if __name__ == '__main__':
    print("🎮 Iniciando DeluxAI CORRIGIDO - Criado por Natan Borges")
    print("=" * 70)
    carregar_conhecimento()
    
    if verificar_ollama():
        print("✅ Ollama + Gemma3:1b conectados")
    else:
        print("⚠️ Ollama offline - modo base local corrigida")
    
    print("🌐 Servidor DeluxAI CORRIGIDO na porta 5001...")
    print("🧠 Base de conhecimento: INFORMAÇÕES REAIS")
    print("👨‍💻 Criador: Natan Borges")
    print("📧 Contato: borgesnatan09@gmail.com")
    print("📱 WhatsApp: +55 21 99282-6074")
    print("🌐 Site: deluxgtav.netlify.app")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )