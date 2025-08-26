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
    "Se cuida! 😎", "Partiu RP! 🔥", "Vai na fé! 🙏", "Até logo! 😉",
    "Flw! 🔥", "Tchau! 👋", "Nos vemos! ✨"
]

ELOGIOS_RESPOSTAS = [
    "Valeu, mano! 😎 O Natan caprichou mesmo no Delux Modpack!",
    "Obrigado! 🔥 É isso aí, o modpack é show mesmo!",
    "Opa, brigadão! 🎮 Natan fez um trampo top!",
    "Valeu! 😊 Fico feliz que curtiu o modpack!",
    "Tmj! 🤝 O Delux é realmente incrível!"
]

# Sistema de análise de intenção SUPER MELHORADO
def analisar_intencao(pergunta):
    """Analisa a intenção real do usuário com mais precisão"""
    p = pergunta.lower().strip()
    
    intencoes = {
        "instalacao": 0,
        "gameplay": 0,
        "problema": 0,
        "download": 0,
        "requisitos": 0,
        "contato": 0,
        "saudacao": 0,
        "despedida": 0,
        "elogio": 0,
        "opiniao": 0,
        "desenvolvedor": 0,
        "geral": 0
    }
    
    # Palavras-chave ESPECÍFICAS para cada intenção
    palavras_instalacao = [
        "instala", "instalacao", "instalar", "install", "como instalar", 
        "passo a passo", "tutorial instalacao", "instalo", "instalando",
        "extrair", "executar", "administrador", "pasta do gta", "script hook",
        "openiv", "visual c++", "net framework", "pre requisitos"
    ]
    
    palavras_gameplay = [
        "jogar", "jogo", "como joga", "gameplay", "controles", "como usar",
        "fome", "sede", "trabalho", "emprego", "casa", "propriedade", "sistemas",
        "rp", "roleplay", "realista", "mecanicas", "funcionalidades"
    ]
    
    palavras_problema = [
        "erro", "crash", "crashando", "problema", "nao funciona", "travando",
        "bugou", "nao abre", "nao roda", "fps baixo", "lag", "bug", "reportar"
    ]
    
    palavras_download = [
        "baixar", "download", "onde baixar", "link", "mediafire", "partes",
        "arquivos", "site oficial", "gratuito", "free"
    ]
    
    palavras_requisitos = [
        "requisitos", "specs", "meu pc", "roda", "compativel", "gtx", "ram",
        "processador", "pc fraco", "configuracao", "sistema", "windows"
    ]
    
    palavras_contato = [
        "contato", "falar", "desenvolvedor", "criador", "whatsapp", "email",
        "instagram", "discord", "suporte", "ajuda", "borgesnatan", "natan"
    ]
    
    palavras_saudacao = [
        "oi", "ola", "hey", "eai", "fala", "salve", "bom dia", "boa tarde",
        "boa noite", "tudo bem", "beleza", "como vai"
    ]
    
    palavras_despedida = [
        "tchau", "bye", "flw", "falou", "ate mais", "ate logo", "nos vemos",
        "obrigado", "vlw", "valeu", "brigado"
    ]
    
    palavras_elogio = [
        "legal", "top", "show", "incrivel", "otimo", "excelente", "perfeito",
        "massa", "da hora", "maneiro", "bacana", "bom", "boa", "gostei",
        "curti", "parabens", "muito bom", "fantastico"
    ]
    
    palavras_desenvolvedor = [
        "natan", "borges", "desenvolvedor", "criador", "quem fez", "autor",
        "programador", "ntzinnn", "portfolio"
    ]
    
    # Conta ocorrências com pesos diferentes
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
    
    for palavra in palavras_contato:
        if palavra in p:
            intencoes["contato"] += 3
    
    for palavra in palavras_saudacao:
        if palavra in p:
            intencoes["saudacao"] += 4
    
    for palavra in palavras_despedida:
        if palavra in p:
            intencoes["despedida"] += 4
    
    for palavra in palavras_elogio:
        if palavra in p:
            intencoes["elogio"] += 3
    
    for palavra in palavras_desenvolvedor:
        if palavra in p:
            intencoes["desenvolvedor"] += 3
    
    # Análise contextual
    if len(pergunta) < 20:
        if any(s in p for s in ["oi", "ola", "eai", "fala", "salve"]):
            intencoes["saudacao"] += 5
        elif any(d in p for d in ["tchau", "flw", "falou", "bye"]):
            intencoes["despedida"] += 5
        elif any(e in p for e in ["legal", "top", "show", "massa"]):
            intencoes["elogio"] += 4
    
    # Retorna a intenção com maior score
    intencao_principal = max(intencoes, key=intencoes.get)
    score_principal = intencoes[intencao_principal]
    
    return intencao_principal if score_principal > 1 else "geral"

# Base de conhecimento SUPER ESPECÍFICA E COMPLETA
def carregar_conhecimento_especializado():
    global KNOWLEDGE_BASE
    
    KNOWLEDGE_BASE = {
        "instalacao": {
            "resposta": """Fala aí! 🎮 **INSTALAÇÃO COMPLETA Delux Modpack v Beta 1.0:**

**🚨 ANTES DE COMEÇAR:**
✅ **GTA V Original** - Steam/Epic/Rockstar (atualizado)
✅ **Backup dos saves** - Documents/Rockstar Games/GTA V
✅ **20GB livres** no disco
✅ **Antivírus DESATIVADO** temporariamente

**📋 PRÉ-REQUISITOS OBRIGATÓRIOS:**
1. **Script Hook V** - Versão mais recente
2. **OpenIV** - Instalado e configurado  
3. **Visual C++ 2015-2022** - Todas versões
4. **.NET Framework 4.8** - Atualizado

**📖 PASSO A PASSO DETALHADO:**
1. **ACESSE:** deluxgtav.netlify.app
2. **BAIXE AS 3 PARTES** (MediaFire) na mesma pasta
3. **EXTRAIA TUDO** juntos (não separe!)
4. **FECHE GTA V** completamente
5. **EXECUTE O INSTALLER** como ADMINISTRADOR
6. **SELECIONE A PASTA** do GTA V:
   - Steam: C:/Program Files/Steam/steamapps/common/Grand Theft Auto V
   - Epic: C:/Program Files/Epic Games/GTAV
   - Rockstar: C:/Program Files/Rockstar Games/GTA V
7. **AGUARDE INSTALAÇÃO** (15-30 min)
8. **REINICIE O PC** se solicitado
9. **ABRA GTA V** normalmente

**🔧 SE DER PROBLEMA:**
- Verificar integridade dos arquivos
- Reinstalar Script Hook V
- Executar sempre como administrador
- Pasta correta do GTA V selecionada

**Instalação perfeita = RP perfeito!** 🔥 Partiu Los Santos! 🇧🇷""",
            "keywords": ["instala", "instalacao", "instalar", "install", "passo", "tutorial", "como instalar"]
        },
        
        "download": {
            "resposta": """Salve! 🔥 **DOWNLOADS OFICIAIS Delux Modpack v Beta 1.0:**

**🌐 SITE OFICIAL ÚNICO:**
**deluxgtav.netlify.app**
⚠️ **ATENÇÃO:** Outros sites = VÍRUS garantido!

**📁 ARQUIVOS NECESSÁRIOS:**
1. **Delux Modpack v Beta 1.0** - part1.rar
2. **Delux Modpack v Beta 1.0** - part2.rar  
3. **Delux Modpack v Beta 1.0** - part3.rar

**💾 COMO BAIXAR:**
1. Acesse **deluxgtav.netlify.app**
2. Procure a seção "Download do Modpack"
3. Clique nos links **MediaFire**
4. Aguarde 5 segundos no MediaFire
5. Clique "**Download**"
6. Baixe **TODAS AS 3 PARTES** na mesma pasta
7. **NÃO EXTRAIA** ainda!

**✅ VERIFICAÇÃO:**
✅ Part1.rar baixado completo
✅ Part2.rar baixado completo  
✅ Part3.rar baixado completo
✅ Todos na mesma pasta
✅ ~20GB total

**❌ PROBLEMAS COMUNS:**
- **Link não abre:** Limpe cache do navegador
- **Download lento:** Use VPN se necessário
- **Arquivo corrompido:** Baixe novamente
- **MediaFire travado:** Aguarde e tente novamente

**🔒 100% GRATUITO e SEGURO!**
**Download seguro = modpack seguro!** 📥 Tmj! 🤝""",
            "keywords": ["baixar", "download", "onde baixar", "link", "mediafire", "site", "oficial", "gratuito"]
        },
        
        "gameplay": {
            "resposta": """E aí! 🎮 **COMO JOGAR Delux Modpack v Beta 1.0:**

**🚀 PRIMEIROS PASSOS:**
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

**🏠 CASAS E PROPRIEDADES:**
- Procure placas "À VENDA"
- **E:** Ver detalhes da propriedade
- Compre com dinheiro do trabalho
- Benefícios: Spawn, garagem, descanso

**🚗 CARROS REALISTAS:**
- Combustível limitado
- Abasteça em postos
- Sons brasileiros
- Danos mais realistas

**🎯 CONTROLES ESPECIAIS:**
- **TAB:** Status (fome/sede)
- **F6:** Menu trabalhos
- **E:** Interações gerais
- **M:** Mapa com locais

**💡 DICAS PRO:**
1. Comece arranjando um emprego
2. Sempre cuide da fome/sede
3. Economize dinheiro para casa própria
4. Explore os mapas brasileiros
5. Faça RP realista sempre!

**É uma vida virtual completa!** 🇧🇷 Bom RP! 🔥""",
            "keywords": ["jogar", "jogo", "como joga", "gameplay", "controles", "sistemas", "fome", "sede", "rp"]
        },
        
        "requisitos": {
            "resposta": """Fala! 💻 **REQUISITOS SISTEMA Delux Modpack v Beta 1.0:**

**⚡ MÍNIMOS (30-40 FPS):**
- **OS:** Windows 10/11 64-bit
- **CPU:** Intel i5-4460 / AMD FX-6300
- **RAM:** 8GB (16GB recomendado)
- **GPU:** GTX 1060 / RX 580 (mínimo)
- **Storage:** 20GB livres (SSD recomendado)
- **Extras:** Script Hook V + OpenIV

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
⚠️ Roda mas limitado - Configs LOW/MEDIUM

**GTX 1060 6GB:**
✅ Performance boa - Configs MEDIUM/HIGH

**RTX 3060/4060:**
🔥 Performance excelente - Configs HIGH/ULTRA

**⚠️ IMPORTANTE:**
- **Launcher:** Steam/Epic/Rockstar (ORIGINAL)
- **Antivírus:** Desativar durante instalação
- **Espaço:** 20GB+ livres sempre
- **Internet:** Para downloads das 3 partes

**PC FRACO? DICAS:**
- Feche outros programas
- Modo Alto Performance
- Limite FPS em 30
- Texturas baixas primeiro

**Seu PC roda? Me fala as specs!** 🎯 Tmj! 🤝""",
            "keywords": ["requisitos", "specs", "meu pc", "roda", "compativel", "placa", "ram", "fps", "sistema"]
        },
        
        "problema": {
            "resposta": """E aí! 🛠️ **SOLUÇÃO DE PROBLEMAS Delux Modpack v Beta 1.0:**

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

**🆘 REPORTAR BUGS:**
- Use a seção "Bugs" no site deluxgtav.netlify.app
- Faça login com conta Google
- Descreva detalhadamente o problema

**ÚLTIMA TENTATIVA:**
1. **Desinstalar** modpack
2. **Verificar integridade** GTA V
3. **Limpar** pasta temp
4. **Reinstalar** tudo limpo

**Me fala o erro específico que te ajudo melhor!** 🔧 Tmj! 🤝""",
            "keywords": ["erro", "crash", "problema", "nao funciona", "travando", "fps baixo", "bugou", "bug"]
        },
        
        "contato": {
            "resposta": """Opa! 📞 **CONTATO COM NATAN BORGES (Desenvolvedor):**

**👨‍💻 NATAN BORGES - DESENVOLVEDOR**
Criador do Delux Modpack v Beta 1.0

**📧 EMAIL PRINCIPAL:**
**borgesnatan09@gmail.com**

**📱 WHATSAPP DIRETO:**
**+55 21 99282-6074**
(Clique para abrir: wa.me/5521992826074)

**📸 INSTAGRAM:**
**@Ntzinnn87**
Siga para novidades e atualizações!

**💬 DISCORD:**
Servidor da comunidade disponível no site

**🌐 PORTFÓLIO:**
meuportfolio02.netlify.app
Conheça mais trabalhos do Natan

**🐛 REPORTAR BUGS:**
Use a seção "Bugs" no site deluxgtav.netlify.app
(Login com Google necessário)

**💰 DOAÇÃO:**
Link disponível no site para apoiar o desenvolvimento

**⏰ HORÁRIO DE ATENDIMENTO:**
Natan responde preferencialmente:
- WhatsApp: 9h às 22h
- Email: 24-48h para resposta

**🔥 COMUNIDADE ATIVA:**
- Instagram para novidades
- Discord para chat da galera
- Email/WhatsApp para suporte técnico

**Entre em contato sem medo!** Natan sempre ajuda! 🤝""",
            "keywords": ["contato", "falar", "desenvolvedor", "criador", "whatsapp", "email", "instagram", "natan"]
        },
        
        "desenvolvedor": {
            "resposta": """E aí! 👨‍💻 **SOBRE NATAN BORGES - DESENVOLVEDOR:**

**🔥 QUEM É NATAN BORGES:**
- **Nome:** Natan Borges
- **Profissão:** Desenvolvedor Independente
- **Especialidade:** Modding GTA V
- **Paixão:** Criar experiências realistas de RP

**🎮 CRIAÇÃO DO DELUX MODPACK:**
Natan criou o Delux Modpack v Beta 1.0 para trazer uma experiência de **roleplay realista** para o **singleplayer do GTA V**. O objetivo é simular a vida real dentro do jogo!

**🌟 CARACTERÍSTICAS:**
- Apaixonado por GTA V desde sempre
- Desenvolvedor autodidata
- Foco em qualidade e realismo
- Comunidade brasileira em primeiro lugar
- Suporte direto aos usuários

**📱 REDES SOCIAIS:**
- **Instagram:** @Ntzinnn87
- **Email:** borgesnatan09@gmail.com  
- **WhatsApp:** +55 21 99282-6074

**💼 PORTFÓLIO:**
**meuportfolio02.netlify.app**
Veja outros projetos incríveis do Natan!

**🎯 MISSÃO:**
Trazer a melhor experiência de RP brasileiro para GTA V, **totalmente gratuito** e com suporte completo à comunidade.

**🚀 FUTURO:**
Natan está sempre trabalhando em **atualizações constantes** com correções de bugs e **novas funcionalidades** para o Delux Modpack.

**Um desenvolvedor brasileiro que faz a diferença!** 🇧🇷 Tmj! 🔥""",
            "keywords": ["natan", "borges", "desenvolvedor", "criador", "quem fez", "autor", "programador"]
        },
        
        "saudacao": {
            "resposta": """Salve! 🔥 

**Beleza aí? Sou o DeluxAI, criado pelo Natan Borges!**

Especialista no **Delux Modpack v Beta 1.0** - o modpack brasileiro que transforma GTA V num **RP realista completo!**

**🎮 Posso te ajudar com:**
📖 **Instalação** passo a passo completo
📥 **Downloads** oficiais seguros  
🛠️ **Problemas** técnicos e bugs
💻 **Requisitos** do sistema
🎯 **Gameplay** e sistemas RP
📞 **Contato** direto com Natan Borges
🐛 **Reportar bugs** no site

**🌐 Site oficial:** deluxgtav.netlify.app

**No que posso ajudar hoje?** 🤝""",
            "keywords": ["oi", "ola", "eai", "fala", "salve", "hey", "bom dia", "tudo bem"]
        },
        
        "despedida": {
            "resposta": random.choice(DESPEDIDAS),
            "keywords": ["tchau", "bye", "flw", "falou", "ate mais", "obrigado", "vlw", "valeu"]
        },
        
        "elogio": {
            "resposta": random.choice(ELOGIOS_RESPOSTAS),
            "keywords": ["legal", "top", "show", "incrivel", "massa", "da hora", "bom", "gostei"]
        },
        
        "opiniao": {
            "resposta": """Opa! 🔥 **MINHA OPINIÃO SOBRE O DELUX MODPACK:**

**🌟 É SENSACIONAL, CARA!**

O **Delux Modpack v Beta 1.0** é simplesmente **o melhor modpack brasileiro** de RP para GTA V! O Natan Borges caprichou demais:

**✅ PONTOS FORTES:**
- **100% Gratuito** - Acesso total sem pagar nada
- **RP Realista** - Sistemas de fome, sede, trabalho
- **Instalação Fácil** - Tutorial completo incluído  
- **Comunidade BR** - Feito por brasileiro para brasileiros
- **Suporte Ativo** - Natan sempre ajuda
- **Atualizações Constantes** - Sempre melhorando

**🎮 EXPERIÊNCIA:**
Transforma **GTA V singleplayer** numa **experiência de RP completa**! Você trabalha, compra casa, cuida da fome/sede, vive uma vida virtual realista.

**🇧🇷 DIFERENCIAL BRASILEIRO:**
- Sons brasileiros nos carros
- Mapas e locais do Brasil
- Comunidade que fala português
- Suporte em português

**💯 VALE A PENA?**
**SIM, DEMAIS!** Se você curte RP e GTA V, é **obrigatório** ter esse modpack. Qualidade profissional, **totalmente gratuito**.

**Recomendo 1000%!** 🚀 Baixa logo no deluxgtav.netlify.app! 🎯""",
            "keywords": ["vale pena", "é bom", "recomenda", "opiniao", "review"]
        }
    }
    
    print(f"✅ Base SUPER ESPECIALIZADA carregada: {len(KNOWLEDGE_BASE)} categorias")

# Busca inteligente SUPER MELHORADA
def buscar_resposta_especializada(pergunta):
    intencao = analisar_intencao(pergunta)
    
    print(f"🎯 Intenção detectada: {intencao} para: '{pergunta[:50]}...'")
    
    if intencao in KNOWLEDGE_BASE:
        resposta = KNOWLEDGE_BASE[intencao]["resposta"]
        
        # Para despedidas e elogios, pode variar
        if intencao == "despedida":
            resposta = random.choice(DESPEDIDAS)
        elif intencao == "elogio":
            resposta = random.choice(ELOGIOS_RESPOSTAS)
            
        return resposta
    
    return None

# Processamento Ollama FOCADO
def processar_ollama_focado(pergunta, intencao):
    if not verificar_ollama():
        return None
    
    try:
        # Prompts específicos por intenção
        prompts = {
            "instalacao": "Explique detalhadamente como instalar o Delux Modpack passo a passo:",
            "gameplay": "Ensine como jogar e usar todos os sistemas do Delux Modpack:",
            "problema": "Resolva este problema técnico do Delux Modpack:",
            "download": "Explique como baixar o Delux Modpack com segurança:",
            "requisitos": "Analise se este PC roda o Delux Modpack:",
            "contato": "Forneça informações de contato do desenvolvedor Natan Borges:",
            "desenvolvedor": "Fale sobre Natan Borges, desenvolvedor do Delux Modpack:",
            "saudacao": "Responda educadamente e apresente o DeluxAI:",
            "despedida": "Responda educadamente à despedida:",
            "elogio": "Responda positivamente ao elogio sobre o modpack:",
            "opiniao": "Dê sua opinião sobre o Delux Modpack:",
            "geral": "Responda sobre o Delux Modpack:"
        }
        
        prompt_base = prompts.get(intencao, prompts["geral"])
        
        prompt = f"""Você é DeluxAI, criado por Natan Borges, especialista EXCLUSIVO no Delux Modpack v Beta 1.0 para GTA V.

PERSONALIDADE: Brasileiro descontraído, direto, útil, sempre positivo e prestativo.

INFORMAÇÕES ESSENCIAIS:
- Site oficial: deluxgtav.netlify.app (ÚNICO site oficial e seguro)
- Criador/Desenvolvedor: Natan Borges 
- Contato: borgesnatan09@gmail.com, WhatsApp +55 21 99282-6074
- Instagram: @Ntzinnn87
- Portfólio: meuportfolio02.netlify.app
- Modpack: 100% GRATUITO, RP realista, singleplayer GTA V
- Downloads: MediaFire (3 partes) no site oficial
- Requisitos: Windows 10/11, GTA V original, 8GB RAM, GTX 1060/RX 580 mínimo

IMPORTANTE: SEMPRE responda TUDO que souber sobre o assunto perguntado. Seja completo e detalhado.

FOCO: {intencao.upper()}

{prompt_base} {pergunta}

Resposta completa e detalhada (máximo 500 palavras):"""

        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "num_predict": 400,
                "temperature": 0.3,
                "top_k": 25,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "stop": ["</s>", "Human:", "PERGUNTA:", "Usuario:"]
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
                return limpar_resposta_focada(resposta)
        
        return None
        
    except Exception as e:
        print(f"❌ Erro Ollama: {e}")
        return None

# Limpeza focada MELHORADA
def limpar_resposta_focada(resposta):
    # Remove prefixos desnecessários
    prefixos = [
        "Resposta completa e detalhada:", "DeluxAI:", "Como DeluxAI",
        "RESPOSTA:", "Resposta:", "FOCO:", "Olá!", "Oi!"
    ]
    
    for prefixo in prefixos:
        if resposta.startswith(prefixo):
            resposta = resposta[len(prefixo):].strip()
    
    # Limita tamanho mas mantém informação importante
    if len(resposta) > 1000:
        corte = resposta[:1000]
        ultimo_ponto = corte.rfind('.')
        if ultimo_ponto > 800:
            resposta = resposta[:ultimo_ponto + 1]
    
    # Adiciona saudação se não tiver (apenas para respostas longas)
    if len(resposta) > 100 and not any(s in resposta.lower()[:30] for s in ["fala", "e aí", "opa", "salve", "eae"]):
        saudacao = random.choice(["Fala aí! 🎮", "Opa! 👋", "Salve! 🔥", "E aí! 💪"])
        resposta = f"{saudacao} {resposta}"
    
    # Adiciona despedida se não tiver (apenas para respostas longas)
    if len(resposta) > 100 and not any(d in resposta.lower()[-50:] for d in ["tmj", "falou", "🤝", "🔥", "partiu"]):
        despedida = random.choice(["Tmj! 🤝", "Falou! 👋", "Bom jogo! 🎮", "Partiu RP! 🔥"])
        resposta += f" {despedida}"
    
    return resposta.strip()

# Verificação SUPER melhorada - aceita TUDO sobre o modpack
def eh_pergunta_delux_focada(pergunta):
    p = pergunta.lower().strip()
    
    # SEMPRE aceita saudações, despedidas e elogios
    if len(pergunta) < 25:
        # Saudações
        if any(s in p for s in ["oi", "ola", "eai", "fala", "salve", "hey", "bom dia", "boa tarde", "boa noite"]):
            return True
        # Despedidas
        if any(d in p for d in ["tchau", "bye", "flw", "falou", "ate", "obrigado", "vlw", "valeu"]):
            return True
        # Elogios simples
        if any(e in p for e in ["legal", "top", "show", "massa", "bom", "boa", "otimo", "incrivel"]):
            return True
    
    # Keywords AMPLAS - aceita quase tudo relacionado
    keywords_aceitas = [
        # Sobre o modpack
        "delux", "modpack", "mod", "gta", "v", "beta", "1.0",
        
        # Ações técnicas
        "instalar", "instalacao", "install", "baixar", "download", "rodar", "executar",
        
        # Problemas
        "erro", "crash", "problema", "bug", "nao funciona", "travando", "fps", "lag",
        
        # Sistema
        "requisitos", "pc", "placa", "ram", "processador", "windows", "specs",
        
        # Gameplay
        "jogar", "jogo", "gameplay", "como", "usar", "sistemas", "controles",
        "fome", "sede", "trabalho", "casa", "propriedade", "rp", "roleplay",
        
        # Pessoas e contato
        "natan", "borges", "desenvolvedor", "criador", "contato", "whatsapp", 
        "email", "instagram", "suporte", "ajuda",
        
        # Site e downloads
        "site", "oficial", "mediafire", "link", "gratuito", "free", "seguro",
        
        # Opiniões e avaliações  
        "opiniao", "vale", "pena", "recomenda", "bom", "ruim", "review",
        
        # Palavras gerais que podem estar relacionadas
        "como", "onde", "quando", "porque", "qual", "quem", "quanto"
    ]
    
    # Se tem qualquer palavra relacionada, aceita
    return any(keyword in p for keyword in keywords_aceitas)

# Gerador principal SUPER OTIMIZADO
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
    
    # Resposta de fallback mais completa
    fallbacks = {
        "instalacao": "Fala aí! 🎮 Para instalar o Delux Modpack: 1) Acesse deluxgtav.netlify.app 2) Baixe as 3 partes 3) Extraia juntas 4) Execute como admin. Precisa do GTA V original e Script Hook V! Tmj! 🤝",
        
        "download": "Salve! 🔥 Baixe APENAS no site oficial: deluxgtav.netlify.app - São 3 partes no MediaFire, totalmente GRATUITO e seguro! Outros sites = vírus garantido! 📥",
        
        "gameplay": "E aí! 🎮 No Delux Modpack você tem sistemas de fome/sede (TAB), trabalhos (F6), casas para comprar, carros realistas com combustível. É RP completo no singleplayer! 🇧🇷",
        
        "problema": "Opa! 🛠️ Para problemas: 1) Verificar integridade GTA V 2) Reinstalar Script Hook V 3) Executar como admin 4) Reportar bugs no site deluxgtav.netlify.app. Me fala o erro específico! 🔧",
        
        "requisitos": "Fala! 💻 Requisitos: Windows 10/11, GTA V original, 8GB RAM (16GB ideal), GTX 1060/RX 580 mínimo, 20GB livres. Roda na maioria dos PCs! Me fala suas specs! 🎯",
        
        "contato": "E aí! 📞 Contato do Natan Borges: borgesnatan09@gmail.com, WhatsApp +55 21 99282-6074, Instagram @Ntzinnn87. Ele sempre responde e ajuda! 🤝",
        
        "geral": "Opa! 👋 Sou DeluxAI, especialista no Delux Modpack v Beta 1.0 criado pelo Natan Borges! Modpack brasileiro de RP realista para GTA V. Site: deluxgtav.netlify.app 🎮"
    }
    
    resposta_fallback = fallbacks.get(intencao, fallbacks["geral"])
    
    CACHE_RESPOSTAS[pergunta_hash] = resposta_fallback
    print("⚠️ Resposta fallback contextual")
    return resposta_fallback

# Verificação Ollama
def verificar_ollama():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

# ROTAS DA API

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online_super_otimizado",
        "sistema": "DeluxAI SUPER ESPECIALIZADO v4.0 - Criado por Natan Borges",
        "especialidade": "Delux Modpack v Beta 1.0",
        "modelo": OLLAMA_MODEL,
        "ollama_ativo": verificar_ollama(),
        "cache_size": len(CACHE_RESPOSTAS),
        "categorias": list(KNOWLEDGE_BASE.keys()) if KNOWLEDGE_BASE else [],
        "melhorias_v4": [
            "Entende TUDO sobre o modpack",
            "Reconhece elogios e despedidas", 
            "Respostas mais completas e detalhadas",
            "Informações atualizadas do site oficial",
            "Análise de intenção super precisa",
            "Fallbacks contextuais por categoria",
            "Aceita perguntas muito amplas",
            "Base de conhecimento completa"
        ]
    })

@app.route('/chat', methods=['POST'])
def chat_super_otimizado():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida"}), 400
        
        pergunta = data['message'].strip()
        if not pergunta:
            return jsonify({"error": "Mensagem vazia"}), 400
        
        print(f"💬 [{datetime.now().strftime('%H:%M:%S')}] Pergunta: {pergunta}")
        
        # Filtro SUPER melhorado - aceita quase tudo
        if not eh_pergunta_delux_focada(pergunta):
            resposta_filtro = "Opa! 🎮 Sou o DeluxAI, especialista no Delux Modpack v Beta 1.0 criado pelo Natan Borges. Posso ajudar com TUDO sobre o modpack: instalação, downloads, problemas, requisitos, gameplay RP, contatos, opiniões. Site oficial: deluxgtav.netlify.app - Pergunta qualquer coisa! 🤝"
            return jsonify({
                "response": resposta_filtro,
                "metadata": {
                    "fonte": "filtro_melhorado", 
                    "tipo": "redirecionamento_amplo"
                }
            })
        
        # Gera resposta super otimizada
        resposta = gerar_resposta_otimizada(pergunta)
        
        # Determina fonte mais precisa
        intencao = analisar_intencao(pergunta)
        if intencao in KNOWLEDGE_BASE:
            fonte = f"base_especializada_{intencao}"
        elif verificar_ollama():
            fonte = f"ollama_focado_{intencao}"
        else:
            fonte = f"fallback_contextual_{intencao}"
        
        return jsonify({
            "response": resposta,
            "metadata": {
                "fonte": fonte,
                "intencao": intencao,
                "modelo": OLLAMA_MODEL,
                "sistema": "DeluxAI_v4_Super_Especializado",
                "site_oficial": "deluxgtav.netlify.app"
            }
        })
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({
            "response": "Eae! 😅 Deu um probleminha aqui, mas já volto! Me pergunta sobre instalação, downloads, gameplay, problemas, contatos ou qualquer coisa do Delux Modpack! Site: deluxgtav.netlify.app 🔧",
            "error": "erro_temporario"
        }), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "sistema": "DeluxAI v4.0 - Super Especializado - Auto-Ping Ativo"
    })

if __name__ == '__main__':
    print("🎮 Iniciando DeluxAI SUPER ESPECIALIZADO v4.0")
    print("=" * 70)
    print("👨‍💻 Criado por: Natan Borges")  
    print("📧 Contato: borgesnatan09@gmail.com")
    print("📱 WhatsApp: +55 21 99282-6074")
    print("📸 Instagram: @Ntzinnn87")
    print("🌐 Site: deluxgtav.netlify.app")
    print("💼 Portfólio: meuportfolio02.netlify.app")
    print("=" * 70)
    
    # Carrega base super especializada
    carregar_conhecimento_especializado()
    
    # Status
    if verificar_ollama():
        print("✅ Ollama CONECTADO - Modo Híbrido Super Especializado")
    else:
        print("⚠️ Ollama offline - Modo Base Super Completa")
    
    print("🎯 Sistema de intenções SUPER preciso")
    print("📚 Base de conhecimento COMPLETA por categorias")
    print("💬 Entende elogios, despedidas e TUDO sobre modpack")
    print("🔄 Auto-ping ativo (5min)")
    print("🚀 Servidor iniciando na porta 5001...")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )