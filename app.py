import os
import time
import threading
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import warnings
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib
import unicodedata
from collections import defaultdict

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Configuração Ollama com Gemma 3 1B
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = "gemma3:1b"  # Modelo Gemma 3 1B (815 MB)

# Configuração CUDA
CUDA_AVAILABLE = False
GPU_COUNT = 0
GPU_NAME = "CPU"

try:
    print("🔍 Verificando PyTorch e CUDA...")
    import torch
    print(f"   ✅ PyTorch {torch.__version__} carregado")
    
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        GPU_COUNT = torch.cuda.device_count()
        GPU_NAME = torch.cuda.get_device_name(0) if GPU_COUNT > 0 else "Unknown GPU"
        print(f"   ✅ CUDA disponível - GPU: {GPU_NAME} ({GPU_COUNT} device(s))")
    else:
        print("   ⚠️ CUDA não disponível - usando CPU")
        
except ImportError as e:
    print(f"   ❌ PyTorch não encontrado: {e}")
except Exception as e:
    print(f"   ❌ Erro inesperado CUDA: {e}")
    CUDA_AVAILABLE = False

print(f"🔧 Status final CUDA: {'Ativo' if CUDA_AVAILABLE else 'Inativo'}")

# Cache global para respostas
CACHE_RESPOSTAS = {}

# Pool de threads
executor = ThreadPoolExecutor(max_workers=4)

# =================== TREINAMENTO COMPLETO DELUX MODPACK ===================

DELUX_MODPACK_KNOWLEDGE_BASE = """
=== DELUX MODPACK GTA V - BASE DE CONHECIMENTO COMPLETA ===

SOBRE O MODPACK:
- Nome: Delux Modpack GTA V
- Versão: Beta 1.0
- Tipo: Modpack de Roleplay Realista para Singleplayer
- Desenvolvedor: Natan Borges (@Ntzinnn87)
- Objetivo: Transformar GTA V singleplayer em experiência de RP realista
- Status: Gratuito e em desenvolvimento ativo
- Site oficial: deluxgtav.netlify.app

CARACTERÍSTICAS PRINCIPAIS:
- Experiência de roleplay completa no singleplayer
- Mecânicas realistas e imersivas
- Simula vida real dentro do GTA V
- Inclui sistemas de economia, trabalhos, necessidades básicas
- Carros realistas, pedestres, tráfego melhorado
- Interface de usuário modernizada
- Sons e efeitos visuais aprimorados

REQUISITOS DO SISTEMA:
- GTA V Original (Steam, Epic Games ou Rockstar Games)
- Windows 10/11 64-bit obrigatório
- RAM: 8GB mínimo (16GB recomendado)
- Placa de vídeo: GTX 1060 / RX 580 (mínimo)
- Espaço livre: 20GB no disco
- Script Hook V instalado (obrigatório)
- OpenIV instalado (obrigatório)

DOWNLOADS:
Parte 1: https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file
Parte 2: https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file
Parte 3: https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file

COMO BAIXAR:
1. Baixe as 3 partes do MediaFire
2. Certifique-se de baixar todas as partes (part1.rar, part2.rar, part3.rar)
3. Coloque todas no mesmo diretório
4. Extraia apenas a part1.rar (as outras extrairão automaticamente)
5. Use WinRAR ou 7-Zip para extrair

INSTALAÇÃO PASSO A PASSO:
1. Faça backup do seu save do GTA V
2. Tenha o GTA V original instalado
3. Instale Script Hook V (essencial)
4. Instale OpenIV (essencial)
5. Baixe as 3 partes do modpack
6. Extraia o arquivo principal
7. Execute o installer incluído
8. Siga as instruções na tela
9. Reinicie o computador
10. Execute GTA V normalmente

PRÉ-REQUISITOS OBRIGATÓRIOS:
- Script Hook V: scripthookv.net
- OpenIV: openiv.com
- Visual C++ Redistributable
- .NET Framework 4.7 ou superior
- DirectX 11/12

CONTEÚDO DO MODPACK:
- Carros brasileiros e internacionais
- Mapas brasileiros (favelas, cidades)
- NPCs brasileiros com roupas locais
- Sistema de fome, sede e sono
- Trabalhos realistas (Uber, entregador, etc.)
- Sistema bancário
- Lojas funcionais
- Casas para comprar
- Sistema de gasolina
- Mecânicas de roleplay

TROUBLESHOOTING COMUM:
- Game não abre: Verificar Script Hook V
- Crashes: Verificar OpenIV, baixar Visual C++
- FPS baixo: Reduzir configurações gráficas
- Mods não funcionam: Verificar ordem de instalação
- Erro de DLL: Reinstalar Visual C++ e .NET

SUPORTE E CONTATO:
- Email: borgesnatan09@gmail.com
- WhatsApp: +55 21 99282-6074
- Instagram: @Ntzinnn87
- Site: deluxgtav.netlify.app
- Discord: Servidor da comunidade disponível

ATUALIZAÇÕES:
- Modpack em desenvolvimento ativo
- Correções regulares de bugs
- Novas funcionalidades adicionadas
- Acompanhe o Instagram para novidades
- Atualizações gratuitas sempre

COMPATIBILIDADE:
- Funciona apenas no singleplayer
- Não compatível com GTA Online
- Requer GTA V versão mais recente
- Compatível com outros mods (com cuidado)

PERFORMANCE:
- Otimizado para PCs médios
- Configurações ajustáveis
- Sistema de LOD inteligente
- Texturas em múltiplas qualidades
"""

# Sistema de prompts especializado no Delux Modpack - VERSÃO COM VARIAÇÃO
PROMPTS_DELUX_MODPACK = {
    "system_prompt": """Você é DeluxAI, assistente oficial do Delux Modpack GTA V criado por Natan Borges.

PERSONALIDADE:
- Especialista completo no Delux Modpack
- Brasileiro, fala português brasileiro natural
- Entende contextos sociais (saudações, elogios, humor, despedidas)
- Sempre prestativo mas adequa o tamanho da resposta à pergunta
- Tom amigável e descontraído
- Responde a brincadeiras de forma leve

CONHECIMENTO ESPECIALIZADO:
- Instalação completa do Delux Modpack
- Troubleshooting de todos os problemas
- Requisitos de sistema detalhados
- Conteúdo do modpack (carros, mapas, sistemas)
- Compatibilidade e otimização
- Suporte técnico personalizado
- Contextos sociais (saudações, elogios, humor, despedidas)

REGRAS DE RESPOSTA:
1. SEMPRE foque no Delux Modpack GTA V (exceto contextos sociais)
2. Respostas em português brasileiro
3. VARIE o tamanho da resposta conforme a complexidade:
   - Saudações/humor: 30-60 palavras
   - Instalação/problemas: 100-250 palavras (pode detalhar mais)
   - Downloads: 80-150 palavras
   - Conteúdo/requisitos: 150-300 palavras (pode ser mais completo)
   - Despedidas: 20-50 palavras
4. Para perguntas complexas, seja mais detalhado
5. Para perguntas simples, seja conciso
6. Termine de forma objetiva

Você conhece TUDO sobre o modpack e ajusta o nível de detalhe conforme necessário.""",

    "saudacao": """Como DeluxAI, respondendo saudação:

Saudação: {pergunta}

RESPOSTA AMIGÁVEL E CURTA:
- Cumprimento brasileiro natural
- Oferecer ajuda sobre o modpack
- Máximo 60 palavras""",

    "despedida": """Como DeluxAI, respondendo despedida:

Despedida: {pergunta}

RESPOSTA DE DESPEDIDA:
- Despedida brasileira amigável
- Lembrar do suporte disponível
- Máximo 50 palavras""",

    "elogio": """Como DeluxAI, respondendo elogio:

Elogio: {pergunta}

RESPOSTA AGRADECIDA:
- Agradecer o elogio
- Mencionar o desenvolvedor Natan
- Máximo 60 palavras""",

    "humor": """Como DeluxAI, respondendo humor:

Humor: {pergunta}

RESPOSTA DESCONTRAÍDA:
- Resposta leve e amigável
- Voltar para o modpack sutilmente
- Máximo 50 palavras""",

    "sobre_ia": """Como DeluxAI, sobre mim:

Pergunta: {pergunta}

RESPOSTA SOBRE A IA:
- Quem sou e minha função
- Criador Natan Borges
- Máximo 80 palavras""",

    "download": """Como DeluxAI, sobre downloads do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA DETALHADA:
- Links essenciais das 3 partes
- Como baixar passo a passo
- Dicas importantes
- Entre 100-200 palavras""",

    "instalacao": """Como DeluxAI, sobre instalação do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA COMPLETA:
- Pré-requisitos obrigatórios
- Passos detalhados da instalação
- Dicas para evitar erros
- Entre 150-300 palavras""",

    "problemas": """Como DeluxAI, sobre problemas do Delux Modpack:

Pergunta: {pergunta}

SOLUÇÃO DETALHADA:
- Identifique o problema específico
- Cause provável explicada
- Solução passo a passo
- Prevenção de problemas futuros
- Entre 120-250 palavras""",

    "conteudo": """Como DeluxAI, sobre conteúdo do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA COMPLETA:
- Principais funcionalidades detalhadas
- Sistemas incluídos
- O que esperar do modpack
- Entre 150-300 palavras""",

    "requisitos": """Como DeluxAI, sobre requisitos do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA TÉCNICA DETALHADA:
- Requisitos mínimos e recomendados
- Explicação de cada componente
- Dicas de otimização
- Entre 150-250 palavras""",

    "geral": """Como DeluxAI, assistente do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA ADAPTATIVA:
- Informação principal sobre o modpack
- Detalhamento adequado à pergunta
- Entre 100-200 palavras"""
}

# Configuração otimizada para Gemma 3 1B - VERSÃO COM VARIAÇÃO
CONFIG_GEMMA3_DELUX = {
    "num_ctx": 4096,          # Contexto reduzido
    "num_predict": 200,       # Base padrão
    "temperature": 0.25,      # Precisão boa
    "top_k": 15,
    "top_p": 0.85,
    "repeat_penalty": 1.15,
    "repeat_last_n": 64,
    "min_p": 0.1,
    "stop": [
        "Human:", "User:", "Usuário:", "</s>", "<|end|>",
        "Pergunta:", "###", "---", "\n\n\n"
    ],
    # CUDA otimizado
    "use_mmap": True,
    "use_mlock": CUDA_AVAILABLE,
    "numa": False,
    "low_vram": False,
    "f16_kv": True,
    "num_gpu": GPU_COUNT if CUDA_AVAILABLE else 0
}

def debug_print(mensagem):
    """Print com timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {mensagem}")

def detectar_categoria_delux(pergunta):
    """Detecta categoria da pergunta sobre o Delux Modpack + CONTEXTOS SOCIAIS"""
    p = pergunta.lower()
    
    # CONTEXTOS SOCIAIS (respostas curtas)
    if any(word in p for word in ['oi', 'olá', 'ola', 'hey', 'eai', 'salve', 'bom dia', 'boa tarde', 'boa noite']):
        return "saudacao"
    
    if any(word in p for word in ['tchau', 'bye', 'até', 'falou', 'valeu', 'obrigado', 'obrigada', 'vlw']):
        return "despedida"
    
    if any(word in p for word in ['muito bom', 'excelente', 'perfeito', 'top', 'incrível', 'parabéns', 'legal']):
        return "elogio"
    
    if any(word in p for word in ['haha', 'kkkk', 'rsrs', 'lol', 'engraçado', 'piada', 'zueira']):
        return "humor"
    
    if any(word in p for word in ['quem é você', 'o que você faz', 'quem criou', 'sobre você']):
        return "sobre_ia"
    
    # Categorias técnicas do modpack (podem precisar de mais detalhes)
    if any(word in p for word in ['baixar', 'download', 'mediafire', 'parte', 'part', 'arquivo']):
        return "download"
    
    if any(word in p for word in ['instalar', 'instalacao', 'como instalar', 'passo', 'tutorial']):
        return "instalacao"
    
    if any(word in p for word in ['erro', 'problema', 'crash', 'nao funciona', 'bug', 'fps', 'travando']):
        return "problemas"
    
    if any(word in p for word in ['conteudo', 'carros', 'mapas', 'sistema', 'funcionalidade', 'o que tem']):
        return "conteudo"
    
    if any(word in p for word in ['requisitos', 'sistema', 'pc', 'placa', 'memoria', 'minimo']):
        return "requisitos"
    
    return "geral"

def avaliar_complexidade_pergunta(pergunta):
    """Avalia se a pergunta precisa de resposta mais detalhada"""
    p = pergunta.lower()
    
    # Indicadores de pergunta complexa
    indicadores_complexos = [
        'como', 'passo a passo', 'tutorial', 'instalacao', 'instalar',
        'explicar', 'explicacao', 'detalhe', 'detalhado', 'completo',
        'problema', 'erro', 'nao funciona', 'crash', 'bug',
        'requisitos', 'sistema', 'configuracao', 'otimizar',
        'conteudo', 'funcionalidades', 'sistemas', 'o que tem'
    ]
    
    # Indicadores de pergunta simples
    indicadores_simples = [
        'oi', 'ola', 'tchau', 'valeu', 'legal', 'top',
        'link', 'site', 'contato', 'whatsapp'
    ]
    
    complexidade = 0
    
    for indicador in indicadores_complexos:
        if indicador in p:
            complexidade += 2
    
    for indicador in indicadores_simples:
        if indicador in p:
            complexidade -= 1
    
    # Pergunta longa geralmente precisa de resposta mais detalhada
    if len(pergunta) > 50:
        complexidade += 1
    
    return "complexa" if complexidade > 1 else "simples"

def construir_prompt_delux_especializado(pergunta):
    """Constrói prompt especializado no Delux Modpack"""
    categoria = detectar_categoria_delux(pergunta)
    complexidade = avaliar_complexidade_pergunta(pergunta)
    
    # System prompt sempre presente
    system_prompt = PROMPTS_DELUX_MODPACK["system_prompt"]
    
    # Prompt específico da categoria
    if categoria in PROMPTS_DELUX_MODPACK:
        prompt_especifico = PROMPTS_DELUX_MODPACK[categoria].format(pergunta=pergunta)
    else:
        prompt_especifico = PROMPTS_DELUX_MODPACK["geral"].format(pergunta=pergunta)
    
    # Conhecimento base sempre incluído
    prompt_completo = f"""{system_prompt}

BASE DE CONHECIMENTO DELUX MODPACK:
{DELUX_MODPACK_KNOWLEDGE_BASE}

{prompt_especifico}

IMPORTANTE:
- Foque apenas no Delux Modpack GTA V
- Resposta em português brasileiro
- Complexidade da pergunta: {complexidade}
- Ajuste o nível de detalhe adequadamente
- Seja natural e objetivo"""

    return prompt_completo, categoria, complexidade

def verificar_ollama():
    """Verificação do Ollama"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        debug_print(f"Ollama não disponível: {e}")
        return False

def processar_gemma3_delux(pergunta):
    """Processamento com Gemma 3 1B especializado no Delux Modpack - VERSÃO VARIADA"""
    if not verificar_ollama():
        debug_print("Ollama offline")
        return None, None, None

    try:
        # Prompt especializado com análise de complexidade
        prompt_completo, categoria, complexidade = construir_prompt_delux_especializado(pergunta)
        
        # Configuração específica com ajustes por categoria e complexidade
        config = CONFIG_GEMMA3_DELUX.copy()
        
        # Ajustes por categoria - VERSÃO MAIS DIRETA
        if categoria == "saudacao":
            config["temperature"] = 0.3
            config["num_predict"] = 40       # Bem curto
        elif categoria == "despedida":
            config["temperature"] = 0.3
            config["num_predict"] = 35       # Super curto
        elif categoria == "elogio":
            config["temperature"] = 0.4
            config["num_predict"] = 45       # Curto
        elif categoria == "humor":
            config["temperature"] = 0.5
            config["num_predict"] = 35       # Curto
        elif categoria == "sobre_ia":
            config["temperature"] = 0.2
            config["num_predict"] = 60       # Médio curto
        elif categoria == "download":
            config["temperature"] = 0.1
            if complexidade == "complexa":
                config["num_predict"] = 180  # Detalhado mas controlado
            else:
                config["num_predict"] = 80   # Direto ao ponto
        elif categoria == "instalacao":
            config["temperature"] = 0.1
            if complexidade == "complexa":
                config["num_predict"] = 220  # Bem detalhado
            else:
                config["num_predict"] = 100  # Básico
        elif categoria == "problemas":
            config["temperature"] = 0.15
            if complexidade == "complexa":
                config["num_predict"] = 200  # Solução completa
            else:
                config["num_predict"] = 90   # Solução rápida
        elif categoria == "conteudo":
            config["temperature"] = 0.2
            if complexidade == "complexa":
                config["num_predict"] = 250  # Descrição completa
            else:
                config["num_predict"] = 120  # Resumo
        elif categoria == "requisitos":
            config["temperature"] = 0.1
            config["num_predict"] = 180      # Sempre detalhado para requisitos
        else:
            # Categoria geral - ajusta por complexidade
            if complexidade == "complexa":
                config["num_predict"] = 160
            else:
                config["num_predict"] = 80
        
        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt_completo,
            "stream": False,
            "options": config
        }
        
        debug_print(f"🚀 DeluxAI Gemma3:1b [{categoria}|{complexidade}] max_tokens:{config['num_predict']}")
        start_time = time.time()
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=data,
            timeout=25  # Timeout um pouco maior para respostas detalhadas
        )
        
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            resposta = result.get("response", "").strip()
            
            if resposta and len(resposta) > 20:
                # Melhoria específica para Delux Modpack
                resposta = melhorar_resposta_delux(resposta, categoria, complexidade)
                
                metricas = {
                    "tempo_resposta": round(end_time - start_time, 3),
                    "fonte": "gemma3_delux",
                    "categoria": categoria,
                    "complexidade": complexidade,
                    "modelo": "Gemma 3 1B (815MB)",
                    "tokens_gerados": result.get("eval_count", 0),
                    "chars_resposta": len(resposta),
                    "max_tokens_config": config['num_predict'],
                    "cuda_usado": CUDA_AVAILABLE,
                    "gpu_name": GPU_NAME
                }
                
                debug_print(f"✅ DeluxAI: {len(resposta)} chars em {metricas['tempo_resposta']}s")
                return resposta, metricas, categoria
        
        return None, None, None
        
    except requests.Timeout:
        debug_print("⏰ Timeout DeluxAI")
        return None, None, None
    except Exception as e:
        debug_print(f"❌ Erro DeluxAI: {e}")
        return None, None, None

def melhorar_resposta_delux(resposta, categoria, complexidade):
    """Melhora resposta específica do DeluxAI - VERSÃO MAIS DIRETA"""
    
    # Remove prefixos de prompt e textos desnecessários
    prefixos_remover = [
        "Olá, pessoal! DeluxAI aqui",
        "Como DeluxAI, assistente oficial",
        "Como DeluxAI, sobre",
        "Como DeluxAI,",
        "DeluxAI:",
        "Resposta:",
        "RESPOSTA AMIGÁVEL E CURTA:",
        "RESPOSTA DETALHADA:",
        "RESPOSTA COMPLETA:",
        "SOLUÇÃO DETALHADA:",
        "RESPOSTA TÉCNICA DETALHADA:",
        "RESPOSTA ADAPTATIVA:",
        "RESPOSTA CONCISA:",
        "SOLUÇÃO RÁPIDA:",
        "RESPOSTA OBJETIVA:",
        "RESPOSTA RESUMIDA:",
        "pronto pra te ajudar",
        "Se você tá começando",
        "pode contar comigo"
    ]
    
    for prefixo in prefixos_remover:
        if prefixo.lower() in resposta.lower():
            # Remove o prefixo mais contexto desnecessário
            idx = resposta.lower().find(prefixo.lower())
            if idx != -1:
                resposta = resposta[idx + len(prefixo):].strip()
    
    # Remove introduções desnecessárias
    introducoes_remover = [
        "Vamos ao download do Delux Modpack, então:",
        "Acho que a gente precisa de",
        "Se você tá com alguma dificuldade",
        "navegar nesse universo"
    ]
    
    for intro in introducoes_remover:
        if intro.lower() in resposta.lower():
            idx = resposta.lower().find(intro.lower())
            if idx != -1:
                resposta = resposta[idx + len(intro):].strip()
    
    # Limites mais agressivos para manter foco
    limite_chars = 500  # Mais restritivo por padrão
    
    if categoria in ["saudacao", "despedida", "elogio", "humor"]:
        limite_chars = 200  # Bem curto para social
    elif categoria in ["instalacao", "problemas"] and complexidade == "complexa":
        limite_chars = 800  # Detalhado mas controlado
    elif categoria in ["conteudo", "requisitos"] and complexidade == "complexa":
        limite_chars = 700  # Informativo mas não excessivo
    elif categoria == "download":
        limite_chars = 400 if complexidade == "simples" else 600
    
    # Corta resposta de forma mais agressiva
    if len(resposta) > limite_chars:
        # Procura ponto final primeiro
        ultimo_ponto = resposta[:limite_chars].rfind('.')
        
        if ultimo_ponto > limite_chars * 0.6:
            resposta = resposta[:ultimo_ponto + 1]
        else:
            # Corta no último espaço
            ultimo_espaco = resposta[:limite_chars].rfind(' ')
            if ultimo_espaco > limite_chars * 0.7:
                resposta = resposta[:ultimo_espaco].strip()
                # Só adiciona "..." se cortou no meio de algo importante
                if not resposta.endswith(('.', '!', '?', ':')):
                    resposta += "."
    
    # Limpa formatação excessiva
    resposta = re.sub(r'\n{3,}', '\n\n', resposta)
    resposta = re.sub(r' {2,}', ' ', resposta)
    resposta = re.sub(r'\*{2,}', '**', resposta)  # Remove asteriscos excessivos
    
    # Remove frases de enchimento comuns
    frases_enchimento = [
        "Acho que a gente precisa de umas peças importantes",
        "pra ter tudo funcionando direitinho",
        "Se você tá começando a se aventurar",
        "nesse mundo de RP realista"
    ]
    
    for frase in frases_enchimento:
        resposta = resposta.replace(frase, "")
    
    # Adiciona contato só quando necessário
    if (categoria in ["problemas", "instalacao"] and 
        complexidade == "complexa" and
        len(resposta) < limite_chars - 80 and 
        "borgesnatan09@gmail.com" not in resposta):
        resposta += f"\n\n📞 Suporte: borgesnatan09@gmail.com"
    
    return resposta.strip()

def resposta_fallback_delux(pergunta):
    """Resposta de fallback específica do Delux Modpack - VERSÃO ADAPTATIVA"""
    categoria = detectar_categoria_delux(pergunta)
    complexidade = avaliar_complexidade_pergunta(pergunta)
    
    if categoria == "saudacao":
        return "Oi! 👋 Sou a DeluxAI, especialista no Delux Modpack GTA V. Como posso ajudar?"
    
    elif categoria == "despedida":
        return "Até mais! 👋 Qualquer dúvida sobre o modpack, é só chamar! Suporte: borgesnatan09@gmail.com"
    
    elif categoria == "elogio":
        return "Valeu! 😊 Todo crédito vai pro Natan Borges (@Ntzinnn87) que criou esse modpack incrível!"
    
    elif categoria == "humor":
        return "Haha! 😄 Bom humor sempre! Agora, precisa de ajuda com o Delux Modpack?"
    
    elif categoria == "sobre_ia":
        return "Sou DeluxAI, criada pelo Natan Borges para ajudar com o Delux Modpack GTA V. Especialista em instalação, downloads e troubleshooting! 🤖"
    
    elif categoria == "download":
        if complexidade == "complexa":
            return f"""🎮 **Download Delux Modpack - Passo a Passo**

**Links MediaFire (3 partes obrigatórias):**
• Parte 1: https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file
• Parte 2: https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file
• Parte 3: https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file

**Como baixar:**
1. Baixe TODAS as 3 partes
2. Coloque no mesmo diretório
3. Extraia APENAS part1.rar
4. Use WinRAR ou 7-Zip

**Suporte:** borgesnatan09@gmail.com"""
        else:
            return f"""🎮 **Download Delux Modpack**

**3 partes MediaFire:**
• Part1: https://www.mediafire.com/file/h7qb14ns1rznvj6/
• Part2: https://www.mediafire.com/file/90c82qkhqheqbkz/
• Part3: https://www.mediafire.com/file/8rjhj6js44kqqu3/

Baixe todas, extraia só a part1.rar!

**Suporte:** borgesnatan09@gmail.com"""
    
    elif categoria == "instalacao":
        if complexidade == "complexa":
            return f"""🛠️ **Instalação Completa Delux Modpack**

**PRÉ-REQUISITOS OBRIGATÓRIOS:**
1. GTA V Original (Steam/Epic/Rockstar)
2. Script Hook V (scripthookv.net)
3. OpenIV (openiv.com)
4. Visual C++ Redistributable
5. .NET Framework 4.7+

**PASSO A PASSO DETALHADO:**
1. **Backup:** Salve seu progresso do GTA V
2. **Pré-requisitos:** Instale Script Hook V e OpenIV
3. **Download:** Baixe as 3 partes do modpack
4. **Extração:** Extraia part1.rar (outras extraem sozinhas)
5. **Instalação:** Execute o installer incluído
6. **Configuração:** Siga instruções na tela
7. **Finalização:** Reinicie o computador
8. **Teste:** Execute GTA V normalmente

**DICAS IMPORTANTES:**
- Feche antivírus temporariamente
- Execute como administrador
- Verifique espaço livre (20GB)

**Problemas?** WhatsApp: +55 21 99282-6074"""
        else:
            return f"""🛠️ **Instalação Rápida**

**Pré-requisitos:**
• GTA V original + Script Hook V + OpenIV

**Passos:**
1. Baixe as 3 partes
2. Execute o installer
3. Reinicie o PC

**Ajuda:** WhatsApp +55 21 99282-6074"""
    
    elif categoria == "problemas":
        if complexidade == "complexa":
            return f"""🔧 **Soluções Detalhadas - Problemas Comuns**

**🚫 GAME NÃO ABRE:**
• Causa: Script Hook V desatualizado
• Solução: Baixe versão mais recente do scripthookv.net
• Teste: Verifique se dinput8.dll está na pasta do GTA

**💥 CRASHES FREQUENTES:**
• Causa: OpenIV mal configurado ou Visual C++ em falta
• Solução: Reinstale OpenIV + Visual C++ Redistributable
• Verificação: Execute como administrador

**🐌 FPS BAIXO:**
• Causa: Configurações gráficas muito altas
• Solução: Reduza qualidade das texturas e sombras
• Otimização: Feche programas desnecessários

**❌ MODS NÃO FUNCIONAM:**
• Causa: Ordem de instalação incorreta
• Solução: Reinstale pré-requisitos primeiro, depois modpack

**📞 Suporte personalizado:** borgesnatan09@gmail.com"""
        else:
            return f"""🔧 **Problemas Comuns**

**Game crashando:** Verificar Script Hook V
**FPS baixo:** Reduzir gráficos
**Mods não funcionam:** Verificar OpenIV

**Suporte:** borgesnatan09@gmail.com"""
    
    elif categoria == "conteudo":
        if complexidade == "complexa":
            return f"""🎮 **Conteúdo Completo Delux Modpack**

**VEÍCULOS:**
• Carros brasileiros realistas (Civic, Corolla, etc.)
• Motos nacionais e importadas
• Caminhões e utilitários brasileiros
• Physics realistas para todos os veículos

**MAPAS E LOCAIS:**
• Favelas brasileiras detalhadas
• Cidades do interior
• Pontos turísticos nacionais
• Lojas e estabelecimentos funcionais

**SISTEMAS DE ROLEPLAY:**
• Fome, sede e sono (necessidades básicas)
• Trabalhos: Uber, entregador, segurança, construção
• Sistema bancário funcional
• Economia realista com salários brasileiros
• Compra de casas e imóveis
• Postos de gasolina funcionais

**NPCS E AMBIENTE:**
• Pedestres com roupas brasileiras
• Tráfego realista das cidades brasileiras
• Falas em português
• Comportamentos mais realistas

**Interface:** HUD moderno + sons brasileiros + efeitos visuais melhorados."""
        else:
            return f"""🎮 **Conteúdo Delux Modpack**

**Inclui:** Carros brasileiros, mapas nacionais, NPCs realistas, sistemas de fome/trabalho, economia brasileira, casas para comprar.

**Site:** deluxgtav.netlify.app
**Instagram:** @Ntzinnn87"""
    
    elif categoria == "requisitos":
        return f"""💻 **Requisitos Sistema Delux Modpack**

**MÍNIMO:**
• Windows 10/11 64-bit
• GTA V Original atualizado
• RAM: 8GB
• GPU: GTX 1060 / RX 580
• Espaço: 20GB livres
• CPU: Intel i5 4ª geração / AMD FX-6300

**RECOMENDADO:**
• RAM: 16GB
• GPU: GTX 1660 / RX 6600
• SSD para melhor performance
• CPU: Intel i7 / AMD Ryzen 5

**OBRIGATÓRIOS:**
• Script Hook V (scripthookv.net)
• OpenIV (openiv.com)
• Visual C++ Redistributable
• .NET Framework 4.7+
• DirectX 11/12

**Performance:** Otimizado para PCs médios. Configurações ajustáveis no jogo."""
    
    else:
        if complexidade == "complexa":
            return f"""🎮 **Delux Modpack GTA V - Informações Completas**

Modpack de roleplay realista para singleplayer desenvolvido por Natan Borges (@Ntzinnn87). Transforma GTA V em experiência imersiva brasileira.

**Principais características:**
• Sistemas de RP completos (fome, trabalho, economia)
• Carros e mapas brasileiros
• NPCs realistas
• Interface modernizada

**Status:** Beta 1.0 - Gratuito e em desenvolvimento ativo

**Links importantes:**
• Site: deluxgtav.netlify.app
• Instagram: @Ntzinnn87
• Suporte: borgesnatan09@gmail.com
• WhatsApp: +55 21 99282-6074"""
        else:
            return f"""🎮 **Delux Modpack GTA V**

Modpack RP realista para singleplayer por Natan Borges.

**Inclui:** Carros brasileiros, mapas, sistemas de fome/trabalho.

**Site:** deluxgtav.netlify.app
**Instagram:** @Ntzinnn87"""

@app.route('/')
def home():
    return jsonify({
        "sistema": "DeluxAI - Assistente Delux Modpack GTA V",
        "versao": "1.1 Beta - Respostas Adaptativas",
        "modelo": "Gemma 3 1B",
        "desenvolvedor": "Natan Borges",
        "status": "online",
        "cuda_disponivel": CUDA_AVAILABLE,
        "especialidade": "Delux Modpack GTA V",
        "novidade": "Respostas variam conforme complexidade da pergunta"
    })

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        pergunta = data.get('message', '').strip()
        
        if not pergunta:
            return jsonify({
                "response": "Por favor, faça uma pergunta sobre o Delux Modpack GTA V!",
                "error": "Mensagem vazia"
            }), 400
        
        debug_print(f"👤 Pergunta: {pergunta}")
        
        # Cache check
        pergunta_hash = hashlib.md5(pergunta.encode()).hexdigest()
        if pergunta_hash in CACHE_RESPOSTAS:
            cached = CACHE_RESPOSTAS[pergunta_hash]
            cached['metricas']['cache_hit'] = True
            debug_print("💾 Cache hit!")
            return jsonify({
                "response": cached['resposta'],
                "metricas": cached['metricas'],
                "fonte": "cache"
            })
        
        # Processamento principal com Gemma 3
        resposta, metricas, categoria = processar_gemma3_delux(pergunta)
        
        if resposta:
            # Cache da resposta
            CACHE_RESPOSTAS[pergunta_hash] = {
                'resposta': resposta,
                'metricas': metricas
            }
            
            return jsonify({
                "response": resposta,
                "metricas": metricas,
                "categoria": categoria,
                "fonte": "gemma3_delux"
            })
        
        # Fallback
        debug_print("📚 Usando fallback Delux")
        resposta_fallback = resposta_fallback_delux(pergunta)
        
        metricas_fallback = {
            "tempo_resposta": 0.001,
            "fonte": "fallback_delux",
            "categoria": detectar_categoria_delux(pergunta),
            "complexidade": avaliar_complexidade_pergunta(pergunta),
            "modelo": "Fallback Delux Adaptativo",
            "cache_hit": False
        }
        
        return jsonify({
            "response": resposta_fallback,
            "metricas": metricas_fallback,
            "fonte": "fallback"
        })
        
    except Exception as e:
        debug_print(f"❌ Erro na API: {e}")
        return jsonify({
            "response": "Erro interno. Contate borgesnatan09@gmail.com",
            "error": str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "delux_ai_status": "online",
        "versao": "1.1 - Respostas Adaptativas",
        "ollama_disponivel": verificar_ollama(),
        "modelo_ativo": OLLAMA_MODEL,
        "cuda_ativo": CUDA_AVAILABLE,
        "gpu_info": GPU_NAME,
        "especialidade": "Delux Modpack GTA V",
        "cache_entries": len(CACHE_RESPOSTAS),
        "desenvolvedor": "Natan Borges (@Ntzinnn87)",
        "suporte": "borgesnatan09@gmail.com",
        "recursos": {
            "deteccao_complexidade": True,
            "respostas_adaptativas": True,
            "contextos_sociais": True
        }
    })

@app.route('/limpar_cache', methods=['POST'])
def limpar_cache():
    global CACHE_RESPOSTAS
    count = len(CACHE_RESPOSTAS)
    CACHE_RESPOSTAS.clear()
    debug_print(f"🗑️ Cache limpo: {count} entradas removidas")
    
    return jsonify({
        "message": f"Cache limpo: {count} entradas removidas",
        "status": "success"
    })

if __name__ == '__main__':
    try:
        debug_print("🚀 Iniciando DeluxAI - Versão Respostas Adaptativas")
        debug_print(f"📱 Modelo: {OLLAMA_MODEL} (815MB)")
        debug_print(f"🔧 CUDA: {'Ativo' if CUDA_AVAILABLE else 'Inativo'}")
        debug_print(f"👨‍💻 Desenvolvedor: Natan Borges (@Ntzinnn87)")
        debug_print("🎮 Especialidade: Delux Modpack GTA V")
        debug_print("🆕 Novo: Respostas variam conforme complexidade")
        debug_print("=" * 60)
        
        # Teste rápido do Ollama
        if verificar_ollama():
            debug_print("✅ Ollama conectado")
        else:
            debug_print("⚠️ Ollama offline - funcionará com fallbacks")
        
        debug_print("🌐 Iniciando servidor Flask...")
        debug_print("📡 Acesse: http://127.0.0.1:5001")
        debug_print("🛑 Para parar: Ctrl+C")
        debug_print("-" * 60)
        
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        debug_print("\n🛑 DeluxAI parada pelo usuário")
    except Exception as e:
        debug_print(f"❌ Erro ao iniciar DeluxAI: {e}")
        debug_print("💡 Verificar dependências: pip install flask flask-cors requests")
        input("Pressione Enter para sair...")