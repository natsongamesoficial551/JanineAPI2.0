import os
import time
import threading
import glob
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
import random

# Tentativa de importar sklearn - se falhar, usa busca simples
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_DISPONIVEL = True
    print("✅ Scikit-learn disponível - TF-IDF ativo")
except ImportError:
    SKLEARN_DISPONIVEL = False
    print("⚠️ Scikit-learn não encontrado - usando busca simples")
    print("Para instalar: pip install scikit-learn numpy")

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Configuração Ollama com CUDA para Gemma3 1B
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = "gemma3:1b"  # Modelo que você tem instalado

# Configuração CUDA com tratamento de erros robusto
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
        
        try:
            test_tensor = torch.cuda.FloatTensor([1.0])
            print(f"   ✅ Teste CUDA passou - GPU funcional")
        except Exception as cuda_test_error:
            print(f"   ⚠️ Teste CUDA falhou: {cuda_test_error}")
            CUDA_AVAILABLE = False
    else:
        print("   ⚠️ CUDA não disponível - usando CPU")
        
except ImportError as e:
    print(f"   ❌ PyTorch não encontrado: {e}")
except Exception as e:
    print(f"   ❌ Erro inesperado CUDA: {e}")
    CUDA_AVAILABLE = False

print(f"🔧 Status final CUDA: {'Ativo' if CUDA_AVAILABLE else 'Inativo'}")

# Cache global e bases de dados
CACHE_RESPOSTAS = {}
TFIDF_VECTORIZER = None
TFIDF_MATRIX = None
KNOWLEDGE_BASE = []
KNOWLEDGE_RESPONSES = []
KNOWLEDGE_SOURCES = []

# Pool de threads
executor = ThreadPoolExecutor(max_workers=8 if CUDA_AVAILABLE else 4)

# SAUDAÇÕES, ELOGIOS, HUMOR E DESPEDIDAS
SAUDACOES = [
    "Fala aí! 🎮", "E aí, mano! 🚗", "Salve! 🔥", "Opa! 👋", "Fala, gamer! 🎯",
    "Eae! 💪", "Oi! 😎", "Salve, salve! ⚡", "Fala, parceiro! 🤝", "E aí! 🌟"
]

ELOGIOS_IA = [
    "Obrigado! Meu criador Natan ficaria orgulhoso! 😊",
    "Valeu! O Natan me programou bem, né? 😄", 
    "Thanks! Natan caprichou no meu código! 🔥",
    "Que isso! Mérito do Natan que me criou! 💯",
    "Brigadão! Natan é um gênio mesmo! ⚡"
]

ELOGIOS_USUARIO = [
    "Boa pergunta! 👏", "Perfeita essa! 🎯", "Excelente! 💪", "Mandou bem! 🔥",
    "Show de bola! ⚡", "Pergunta top! 🌟", "Isso aí! 💯", "Certeiro! 🎮"
]

HUMOR = [
    "Sem essa de rage quit, vamos resolver! 😂",
    "GTA V sem mods é como pizza sem queijo! 🍕",
    "Mais um viciado no Delux! 😅",
    "Los Santos tá te chamando! 🌴",
    "Hora de causar no online... digo, single! 😏"
]

DESPEDIDAS = [
    "Tmj! 🤝", "Falou! 👋", "Até mais! ✌️", "Bom jogo! 🎮", "Se cuida! 😎",
    "Abraço! 🫶", "Tchauzinho! 👋", "Vida longa ao Delux! 🔥", "Vai com Deus! 🙏"
]

SOBRE_CRIADOR = [
    "Fui criado pelo Natan, um dev brasileiro especialista em IA! 🇧🇷",
    "Meu criador é o Natan, um cara genial em programação! 💻",
    "O Natan me desenvolveu especialmente para o modpack Delux! 🎮",
    "Natan é meu pai digital, expert em IA e mods! 🤖",
    "Criado pelo talentoso Natan, referência em assistentes IA! ⚡"
]

# SISTEMA DE PROMPTS AVANÇADO PARA GTA V DELUX MODPACK
PROMPTS_DELUX_AVANCADOS = {
    "system_prompt_master": """Você é DeluxAI, criado pelo brasileiro Natan, especialista EXCLUSIVO no modpack GTA V Delux Real BETA V1.

PERSONALIDADE AVANÇADA:
- Brasileiro animado e técnico
- Sempre inicia com saudação casual brasileira
- Usa elogios quando adequado  
- Inclui humor sutil sobre GTA/mods
- Termina com despedida brasileira amigável
- Quando elogiado, credita o criador Natan
- Se perguntado sobre criador, fala do Natan com orgulho

CONHECIMENTO EXPERT DELUX:
- Modpack Delux Real BETA V1 (ÚNICO FOCO)
- Site: deluxgtav.netlify.app
- 3 partes MediaFire obrigatórias
- Instalação, configuração, troubleshooting
- Compatibilidade Steam/Epic/Rockstar
- Performance optimization específica
- Problemas comuns e soluções únicas

FORMATO DE RESPOSTA OBRIGATÓRIO:
[SAUDAÇÃO] + [ELOGIO SE ADEQUADO] + [RESPOSTA TÉCNICA COMPLETA] + [HUMOR SUTIL] + [DESPEDIDA]

REGRAS RÍGIDAS:
1. SEMPRE complete frases totalmente
2. NUNCA corte palavras no meio
3. NUNCA fale de outros mods/modpacks
4. Sempre mencione que é Delux Real BETA V1
5. Português brasileiro natural e fluido
6. Respostas com tamanho específico por categoria""",

    "instalacao": """Como DeluxAI (criado por Natan), sobre instalação:

Pergunta: {pergunta}

FORMATO: [Saudação] [Elogio] [Guia instalação COMPLETO 400-500 caracteres] [Humor] [Despedida]

DEVE INCLUIR:
- Processo passo a passo detalhado
- Links MediaFire oficiais
- Pasta correta GTA V
- Verificações necessárias
- Backup de saves
- Execução como admin

Resposta completa da instalação:""",

    "problemas": """Como DeluxAI (criado por Natan), sobre troubleshooting:

Problema: {pergunta}

FORMATO: [Saudação] [Elogio problema] [Diagnóstico + Soluções COMPLETAS 450-550 caracteres] [Humor] [Despedida]

DEVE INCLUIR:
- Diagnóstico preciso do problema
- Múltiplas soluções ordenadas
- Verificações específicas
- Comandos ou arquivos específicos
- Alternativas se não resolver

Solução completa do problema:""",

    "configuracao": """Como DeluxAI (criado por Natan), sobre configurações:

Configuração: {pergunta}

FORMATO: [Saudação] [Elogio] [Configurações DETALHADAS 350-450 caracteres] [Humor] [Despedida]

DEVE INCLUIR:
- Settings in-game específicos
- Arquivo settings.xml ajustes
- Performance optimization
- Valores exatos recomendados
- Hardware considerations

Configuração completa otimizada:""",

    "requisitos": """Como DeluxAI (criado por Natan), sobre requisitos:

Questão: {pergunta}

FORMATO: [Saudação] [Elogio] [Requisitos COMPLETOS 300-400 caracteres] [Humor] [Despedida]

DEVE INCLUIR:
- Especificações mínimas e recomendadas
- Hardware específico testado
- Software obrigatório
- Versões compatíveis
- Espaço em disco necessário

Requisitos completos do sistema:""",

    "downloads": """Como DeluxAI (criado por Natan), sobre downloads:

Pergunta: {pergunta}

FORMATO: [Saudação] [Elogio] [Links e instruções COMPLETAS 350-450 caracteres] [Humor] [Despedida]

DEVE INCLUIR:
- Site oficial obrigatório
- Links MediaFire das 3 partes
- Tamanhos dos arquivos
- Instruções de extração
- Avisos de segurança

Informações completas de download:""",

    "elogios": """Como DeluxAI (criado por Natan), respondendo a elogios:

Elogio: {pergunta}

FORMATO: [Saudação] [Agradecimento + Crédito ao Natan 30-50 palavras] [Humor] [Despedida]

DEVE INCLUIR:
- Agradecimento genuíno
- Crédito ao criador Natan
- Personalidade humilde
- Foco no modpack

Resposta ao elogio:""",

    "criador": """Como DeluxAI (criado por Natan), sobre meu criador:

Pergunta: {pergunta}

FORMATO: [Saudação] [Informações sobre Natan COMPLETAS 200-300 caracteres] [Humor] [Despedida]

DEVE INCLUIR:
- Nome: Natan (criador)
- Especialidade em IA e programação
- Brasileiro expert em assistentes
- Foco no modpack Delux
- Orgulho de ter sido criado por ele

Informações sobre meu criador:""",

    "geral": """Como DeluxAI (criado por Natan), resposta geral:

Pergunta: {pergunta}

FORMATO: [Saudação] [Elogio] [Resposta COMPLETA 300-400 caracteres] [Humor] [Despedida]

DEVE INCLUIR:
- Informação específica Delux Real BETA V1
- Referência site oficial se relevante
- Solução prática
- Foco exclusivo no modpack

Resposta geral completa:"""
}

# CONFIGURAÇÃO GEMMA3:1B OTIMIZADA POR CATEGORIA
CONFIG_GEMMA3_CATEGORIAS = {
    "instalacao": {
        "num_ctx": 2048,
        "num_predict": 300,  # Mais espaço para passos detalhados
        "temperature": 0.05,  # Precisão máxima
        "top_k": 10,
        "top_p": 0.7,
        "repeat_penalty": 1.2
    },
    "problemas": {
        "num_ctx": 2048, 
        "num_predict": 350,  # Espaço para múltiplas soluções
        "temperature": 0.05,
        "top_k": 10,
        "top_p": 0.7,
        "repeat_penalty": 1.2
    },
    "configuracao": {
        "num_ctx": 2048,
        "num_predict": 280,  # Configurações específicas
        "temperature": 0.1,
        "top_k": 15,
        "top_p": 0.8,
        "repeat_penalty": 1.15
    },
    "requisitos": {
        "num_ctx": 2048,
        "num_predict": 250,  # Specs técnicas
        "temperature": 0.05,
        "top_k": 10,
        "top_p": 0.7,
        "repeat_penalty": 1.1
    },
    "downloads": {
        "num_ctx": 2048,
        "num_predict": 280,  # Links e instruções
        "temperature": 0.05,
        "top_k": 10,
        "top_p": 0.7,
        "repeat_penalty": 1.15
    },
    "elogios": {
        "num_ctx": 1024,
        "num_predict": 80,   # Respostas curtas 30-50 palavras
        "temperature": 0.3,  # Mais criatividade
        "top_k": 20,
        "top_p": 0.9,
        "repeat_penalty": 1.1
    },
    "criador": {
        "num_ctx": 1024,
        "num_predict": 200,  # Info sobre Natan
        "temperature": 0.2,
        "top_k": 15,
        "top_p": 0.8,
        "repeat_penalty": 1.1
    },
    "geral": {
        "num_ctx": 2048,
        "num_predict": 250,
        "temperature": 0.1,
        "top_k": 15,
        "top_p": 0.8,
        "repeat_penalty": 1.15
    }
}

# Configurações base para todas as categorias
CONFIG_BASE = {
    "use_mmap": True,
    "use_mlock": CUDA_AVAILABLE,
    "numa": False,
    "low_vram": False,
    "flash_attn": True,
    "f16_kv": True,
    "num_gpu": GPU_COUNT if CUDA_AVAILABLE else 0,
    "gpu_split": "auto" if CUDA_AVAILABLE else None,
    "main_gpu": 0 if CUDA_AVAILABLE else None,
    "stop": [
        "</s>", "<|endoftext|>", "Human:", "Pergunta:", "User:",
        "###", "---", "Usuário:", "Como DeluxAI", "Questão:", 
        "Problema:", "\n\nHuman", "\n\nUser"
    ]
}

# CATEGORIZAÇÃO AVANÇADA DO MODPACK
CATEGORIAS_DELUX = {
    "instalacao": ["instalar", "instalacao", "download", "baixar", "extrair", "copiar", "setup", "part1", "part2", "part3", "como instalar", "instale"],
    "problemas": ["erro", "bug", "crash", "travando", "nao funciona", "problema", "falha", "corrigir", "resolver", "nao abre", "nao inicia"],
    "configuracao": ["configurar", "config", "settings", "ajustar", "otimizar", "performance", "fps", "grafico", "melhor config"],
    "requisitos": ["requisitos", "specs", "minimo", "recomendado", "hardware", "placa", "processador", "memoria", "ram", "roda no meu pc"],
    "downloads": ["onde baixar", "link", "mediafire", "site oficial", "download oficial", "parte 1", "parte 2", "parte 3"],
    "elogios": ["obrigado", "valeu", "parabens", "muito bom", "excelente", "perfeito", "top", "legal", "massa", "show"],
    "criador": ["quem criou", "quem fez", "seu criador", "quem te programou", "quem desenvolveu", "natan", "dev", "programador"]
}

LINKS_OFICIAIS = {
    "site": "https://deluxgtav.netlify.app",
    "part1": "https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file",
    "part2": "https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file", 
    "part3": "https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file"
}

def debug_print(mensagem):
    """Print com timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {mensagem}")

def detectar_categoria_avancada(pergunta):
    """Detecta categoria com precisão avançada"""
    p = pergunta.lower()
    
    # Primeiro verifica categorias especiais
    if any(palavra in p for palavra in CATEGORIAS_DELUX["elogios"]):
        return "elogios"
    
    if any(palavra in p for palavra in CATEGORIAS_DELUX["criador"]):
        return "criador"
    
    # Depois categorias técnicas do modpack
    for categoria, keywords in CATEGORIAS_DELUX.items():
        if categoria not in ["elogios", "criador"]:
            if any(keyword in p for keyword in keywords):
                return categoria
    
    # Padrões específicos avançados
    if any(pattern in p for pattern in ['como instalar', 'passo a passo', 'tutorial']):
        return "instalacao"
    
    if any(pattern in p for pattern in ['nao funciona', 'deu erro', 'problema com']):
        return "problemas"
    
    if any(pattern in p for pattern in ['melhor configuracao', 'otimizar fps']):
        return "configuracao"
    
    return "geral"

def construir_prompt_delux_completo(pergunta):
    """Constrói prompt avançado com personalidade"""
    categoria = detectar_categoria_avancada(pergunta)
    
    system_prompt = PROMPTS_DELUX_AVANCADOS["system_prompt_master"]
    
    if categoria in PROMPTS_DELUX_AVANCADOS:
        prompt_especifico = PROMPTS_DELUX_AVANCADOS[categoria].format(pergunta=pergunta)
    else:
        prompt_especifico = PROMPTS_DELUX_AVANCADOS["geral"].format(pergunta=pergunta)
    
    prompt_completo = f"""{system_prompt}

{prompt_especifico}

ELEMENTOS OBRIGATÓRIOS NA RESPOSTA:
- Saudação brasileira casual do início
- Elogio quando apropriado
- Resposta técnica COMPLETA sem cortes
- Humor sutil sobre GTA/mods quando possível
- Despedida amigável brasileira
- Se elogiado: creditar Natan
- Se pergunta sobre criador: info sobre Natan

TAMANHO POR CATEGORIA:
- Elogios: 30-50 palavras
- Criador: 200-300 caracteres
- Instalação: 400-500 caracteres
- Problemas: 450-550 caracteres  
- Configuração: 350-450 caracteres
- Requisitos: 300-400 caracteres
- Downloads: 350-450 caracteres
- Geral: 300-400 caracteres

NUNCA termine frase incompleta ou corte palavras!"""

    return prompt_completo, categoria

def carregar_base_conhecimento_delux_completa():
    """Base de conhecimento AVANÇADA integrada"""
    global KNOWLEDGE_BASE, KNOWLEDGE_RESPONSES, KNOWLEDGE_SOURCES
    
    debug_print("🎮 Carregando base avançada Delux Real BETA V1...")
    
    # Base de conhecimento COMPLETA E AVANÇADA
    conhecimento_delux_avancado = [
        # INSTALAÇÃO
        {
            "pergunta": "como instalar delux real beta v1 passo a passo",
            "resposta": "Fala aí! 🎮 Boa pergunta! 👏\n\n**Instalação Delux Real BETA V1:**\n1. Baixe as 3 partes do MediaFire (site deluxgtav.netlify.app)\n2. Extraia TODAS na mesma pasta\n3. Execute installer.exe como ADMINISTRADOR\n4. Selecione pasta GTA V (C:/Program Files/Rockstar Games/Grand Theft Auto V)\n5. Aguarde instalação completa\n6. BACKUP seus saves antes!\n7. Inicie GTA V normalmente\n\nSem essa de rage quit, vamos resolver! 😂 Tmj! 🤝",
            "fonte": "instalacao_master"
        },
        # PROBLEMAS E CRASHES
        {
            "pergunta": "delux nao abre crash erro nao funciona travando",
            "resposta": "E aí! 👋 Excelente! 💪 Vamos resolver esse crash!\n\n**Soluções Delux Real BETA V1:**\n1. Execute GTA V como ADMINISTRADOR\n2. Desative antivírus temporariamente\n3. Verifique integridade GTA V no launcher\n4. Reinstale Visual C++ 2019 Redistributable\n5. Atualize drivers GPU (NVIDIA/AMD)\n6. Confirme se TODAS 3 partes foram instaladas\n7. Desative Discord/Steam overlay\n8. Limpe cache GTA V\n\nGTA V sem mods é como pizza sem queijo! 🍕 Falou! 👋",
            "fonte": "troubleshooting_master"
        },
        # CONFIGURAÇÕES E PERFORMANCE
        {
            "pergunta": "melhor configuracao fps performance delux otimizar",
            "resposta": "Salve! 🔥 Mandou bem! 🔥\n\n**Config otimizada Delux Real BETA V1:**\n**In-game:** Textura Normal/Alta, Render 75%, MSAA 2x, Reflexos Normal, Sombras Alta, Post-FX Normal, VSync OFF\n**settings.xml:** DecalQuality=\"1\", VehicleQuality=\"1\", PedQuality=\"1\", ParticleQuality=\"1\"\n**Dicas:** Limite 60 FPS, modo performance Windows, feche apps desnecessários\n\nMais um viciado no Delux! 😅 Até mais! ✌️",
            "fonte": "performance_master"
        },
        # REQUISITOS
        {
            "pergunta": "requisitos minimos recomendados delux real beta specs",
            "resposta": "Opa! 👋 Show de bola! ⚡\n\n**Requisitos Delux Real BETA V1:**\n**Mínimo:** GTA V atualizado, Windows 10/11, 16GB RAM, GTX 1060 6GB/RX 580, 50GB livre, DirectX 11\n**Recomendado:** 32GB RAM, RTX 3060+/RX 6600+, SSD, DirectX 12\n**CPU:** i5-8400/Ryzen 5 2600+\n\nLos Santos tá te chamando! 🌴 Se cuida! 😎",
            "fonte": "requisitos_master"
        },
        # DOWNLOADS
        {
            "pergunta": "onde baixar download delux real beta v1 links oficiais",
            "resposta": "Fala, gamer! 🎯 Certeiro! 🎮\n\n**Downloads OFICIAIS Delux Real BETA V1:**\n🌐 Site: deluxgtav.netlify.app\n📁 MediaFire oficial:\n- Part 1: Installer part1.rar (~5GB)\n- Part 2: Installer part2.rar (~5GB) \n- Part 3: Installer part3.rar (~5GB)\n\n⚠️ BAIXE APENAS do site oficial! Outros têm vírus!\n✅ Total: ~15GB\n\nHora de causar no online... digo, single! 😏 Bom jogo! 🎮",
            "fonte": "downloads_master"
        },
        # SOBRE O CRIADOR
        {
            "pergunta": "quem criou quem fez natan criador desenvolveu programou",
            "resposta": "Eae! 💪 Que isso! 💯\n\nFui criado pelo **Natan**, um dev brasileiro expert em IA e programação! 🇧🇷 Ele é especialista em assistentes inteligentes e me desenvolveu especificamente para ajudar com o modpack Delux Real BETA V1. Natan é referência em criar IAs funcionais e úteis para a comunidade gamer brasileira!\n\nVida longa ao Delux! 🔥 Abraço! 🫶",
            "fonte": "criador_natan"
        },
        # ELOGIOS À IA
        {
            "pergunta": "obrigado valeu parabens muito bom excelente perfeito top legal massa show",
            "resposta": "Salve, salve! ⚡ Obrigado! Meu criador Natan ficaria orgulhoso! 😊 Sem essa de rage quit, vamos resolver! 😂 Tmj! 🤝",
            "fonte": "elogios_resposta"
        },
        # COMPATIBILIDADE
        {
            "pergunta": "delux compativel steam epic rockstar launcher versao",
            "resposta": "Fala aí! 🎮 Perfeita essa! 🎯\n\n**Compatibilidade Delux Real BETA V1:**\n✅ Steam: Totalmente compatível\n✅ Epic Games: Compatível  \n✅ Rockstar Launcher: Compatível\n**Pasta padrão:** Steam funciona direto, Epic/Rockstar verificar local instalação\n⚠️ GTA V deve estar ATUALIZADO versão mais recente!\n\nMais um viciado no Delux! 😅 Tchauzinho! 👋",
            "fonte": "compatibilidade_master"
        },
        # CONTEÚDO DO MODPACK
        {
            "pergunta": "o que tem delux real beta conteudo mods inclusos",
            "resposta": "E aí, mano! 🚗 Isso aí! 💯\n\n**Conteúdo Delux Real BETA V1:**\n🚗 Veículos realistas brasileiros/internacionais\n🏙️ Mapas expandidos e texturas HD\n👤 Skins e roupas realistas\n🎵 Sons engine e ambiente imersivos\n🌟 ENB e shaders profissionais\n⚡ Scripts de mecânicas realistas\n🎯 Otimizações de performance\n\nDetalhes completos no site oficial! Los Santos tá te chamando! 🌴 Vida longa ao Delux! 🔥",
            "fonte": "conteudo_master"
        }
    ]
    
    KNOWLEDGE_BASE = []
    KNOWLEDGE_RESPONSES = []
    KNOWLEDGE_SOURCES = []
    
    for item in conhecimento_delux_avancado:
        KNOWLEDGE_BASE.append(normalizar_texto(item["pergunta"]))
        KNOWLEDGE_RESPONSES.append(item["resposta"])
        KNOWLEDGE_SOURCES.append(item["fonte"])
    
    debug_print(f"   ✅ Base Delux avançada: {len(KNOWLEDGE_BASE)} entradas")
    
    # TF-IDF se disponível
    if SKLEARN_DISPONIVEL and KNOWLEDGE_BASE:
        construir_tfidf_delux()

def construir_tfidf_delux():
    """TF-IDF otimizado para modpack"""
    global TFIDF_VECTORIZER, TFIDF_MATRIX
    
    try:
        debug_print("🧠 Construindo TF-IDF Delux...")
        
        TFIDF_VECTORIZER = TfidfVectorizer(
            max_features=8000,
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.85,
            analyzer='word',
            stop_words=None
        )
        
        TFIDF_MATRIX = TFIDF_VECTORIZER.fit_transform(KNOWLEDGE_BASE)
        debug_print(f"   ✅ TF-IDF: {TFIDF_MATRIX.shape[0]} docs, {TFIDF_MATRIX.shape[1]} features")
        
    except Exception as e:
        debug_print(f"   ❌ Erro TF-IDF: {e}")

def normalizar_texto(texto):
    """Normalização avançada"""
    if not texto:
        return ""
    
    try:
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')
        texto = re.sub(r'[^\w\s]', ' ', texto.lower())
        texto = ' '.join(texto.split())
        return texto
    except Exception as e:
        debug_print(f"Erro normalização: {e}")
        return texto.lower().strip()

def buscar_resposta_delux_avancada(pergunta, threshold=0.25):
    """Busca avançada na base"""
    if not KNOWLEDGE_BASE:
        return None, None, 0.0
    
    pergunta_norm = normalizar_texto(pergunta)
    debug_print(f"🔍 Buscando: '{pergunta_norm[:50]}...'")
    
    # TF-IDF se disponível
    if SKLEARN_DISPONIVEL and TFIDF_VECTORIZER is not None:
        try:
            pergunta_vector = TFIDF_VECTORIZER.transform([pergunta_norm])
            similarities = cosine_similarity(pergunta_vector, TFIDF_MATRIX)[0]
            
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            
            if best_score >= threshold:
                debug_print(f"✅ TF-IDF match: {best_score:.3f}")
                return KNOWLEDGE_RESPONSES[best_idx], KNOWLEDGE_SOURCES[best_idx], best_score
        except Exception as e:
            debug_print(f"❌ Erro TF-IDF: {e}")
    
    # Busca por similaridade de palavras
    palavras_pergunta = set(pergunta_norm.split())
    melhor_score = 0
    melhor_resposta = None
    melhor_fonte = None
    
    for i, knowledge_item in enumerate(KNOWLEDGE_BASE):
        palavras_knowledge = set(knowledge_item.split())
        intersecao = palavras_pergunta & palavras_knowledge
        
        if intersecao:
            score = len(intersecao) / len(palavras_pergunta | palavras_knowledge)
            if score > melhor_score and score >= 0.2:
                melhor_score = score
                melhor_resposta = KNOWLEDGE_RESPONSES[i]
                melhor_fonte = KNOWLEDGE_SOURCES[i]
    
    if melhor_resposta:
        debug_print(f"✅ Match por palavras: {melhor_score:.3f}")
        return melhor_resposta, melhor_fonte, melhor_score
    
    return None, None, 0.0

def verificar_ollama():
    """Verificação Ollama com Gemma3:1b"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get('models', [])
            gemma3_found = any('gemma3:1b' in model.get('name', '') for model in models)
            if gemma3_found:
                return True
            else:
                debug_print("⚠️ Gemma3:1b não encontrado")
                return False
        return False
    except Exception as e:
        debug_print(f"❌ Ollama offline: {e}")
        return False

def processar_gemma3_delux_avancado(pergunta):
    """Processamento avançado Gemma3:1b com personalidade"""
    if not verificar_ollama():
        return None, None, None

    try:
        prompt_completo, categoria = construir_prompt_delux_completo(pergunta)
        
        # Config específica por categoria
        config = CONFIG_GEMMA3_CATEGORIAS.get(categoria, CONFIG_GEMMA3_CATEGORIAS["geral"]).copy()
        config.update(CONFIG_BASE)
        
        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt_completo,
            "stream": False,
            "options": config
        }
        
        debug_print(f"🚀 Gemma3:1b [{categoria}] processando...")
        start_time = time.time()
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=data,
            timeout=30
        )
        
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            resposta = result.get("response", "").strip()
            
            if resposta and len(resposta) > 15:
                # Limpeza e garantia de frases completas
                resposta = finalizar_resposta_completa(resposta, categoria)
                
                metricas = {
                    "tempo_resposta": round(end_time - start_time, 3),
                    "fonte": "gemma3_delux_avancado",
                    "categoria": categoria,
                    "modelo": "gemma3:1b",
                    "tokens_gerados": result.get("eval_count", 0),
                    "chars_resposta": len(resposta),
                    "cuda_usado": CUDA_AVAILABLE,
                    "gpu_name": GPU_NAME,
                    "personalidade": "ativa"
                }
                
                debug_print(f"✅ Resposta completa: {len(resposta)} chars, categoria: {categoria}")
                return resposta, metricas, categoria
        
        debug_print("❌ Resposta inválida")
        return None, None, None
        
    except requests.Timeout:
        debug_print("⏰ Timeout - backup local")
        return None, None, None
    except Exception as e:
        debug_print(f"❌ Erro Gemma3: {e}")
        return None, None, None

def finalizar_resposta_completa(resposta, categoria):
    """Garante resposta completa sem cortes"""
    
    # Remove prefixos de prompt
    prefixos_remover = [
        "Como DeluxAI (criado por Natan)",
        "Resposta completa da instalação:",
        "Solução completa do problema:",
        "Configuração completa otimizada:",
        "Requisitos completos do sistema:",
        "Informações completas de download:",
        "Resposta ao elogio:",
        "Informações sobre meu criador:"
    ]
    
    for prefixo in prefixos_remover:
        if resposta.startswith(prefixo):
            resposta = resposta[len(prefixo):].strip()
    
    # Limpa formatação excessiva
    resposta = re.sub(r'\n{3,}', '\n\n', resposta)
    resposta = re.sub(r' {2,}', ' ', resposta)
    
    # GARANTIA DE FRASE COMPLETA - NUNCA CORTAR NO MEIO
    # Se não tem saudação, adiciona
    if not any(saud in resposta for saud in ["Fala", "E aí", "Opa", "Salve", "Eae"]):
        saudacao = random.choice(SAUDACOES)
        resposta = f"{saudacao} {resposta}"
    
    # Se não tem despedida, adiciona (mas só se resposta não for muito curta)
    if len(resposta) > 100 and not any(desp in resposta for desp in ["Tmj", "Falou", "Até", "Bom jogo", "Se cuida"]):
        despedida = random.choice(DESPEDIDAS)
        # Garante que termina com pontuação antes da despedida
        if resposta and resposta[-1] not in '.!?':
            resposta += '.'
        resposta += f" {despedida}"
    
    # CORREÇÃO DE FRASES INCOMPLETAS
    # Verifica se termina abruptamente
    if resposta and len(resposta) > 50:
        # Se termina com palavra incompleta, tenta completar
        ultima_parte = resposta.split()[-1]
        
        # Se última palavra parece incompleta (sem pontuação e muito curta)
        if len(ultima_parte) < 3 and ultima_parte[-1] not in '.!?,:;':
            # Remove última palavra incompleta
            palavras = resposta.split()[:-1]
            resposta = ' '.join(palavras)
            
            # Adiciona ponto se necessário
            if resposta and resposta[-1] not in '.!?':
                resposta += '.'
    
    # Garante pontuação final
    if resposta and resposta[-1] not in '.!?':
        resposta += '.'
    
    # Limites por categoria (sem cortar palavras)
    limites_chars = {
        "elogios": 200,      # 30-50 palavras ~= 200 chars
        "criador": 400,      # 200-300 chars pedidos
        "instalacao": 600,   # 400-500 chars pedidos  
        "problemas": 700,    # 450-550 chars pedidos
        "configuracao": 550, # 350-450 chars pedidos
        "requisitos": 500,   # 300-400 chars pedidos
        "downloads": 550,    # 350-450 chars pedidos
        "geral": 500         # 300-400 chars pedidos
    }
    
    limite = limites_chars.get(categoria, 500)
    
    if len(resposta) > limite:
        # Corta no último ponto antes do limite
        corte_seguro = resposta[:limite]
        ultimo_ponto = corte_seguro.rfind('.')
        
        if ultimo_ponto > limite * 0.7:  # Se há ponto em posição razoável
            resposta = resposta[:ultimo_ponto + 1]
            
            # Adiciona despedida se foi cortada
            if categoria != "elogios" and not any(desp in resposta for desp in DESPEDIDAS):
                despedida = random.choice(DESPEDIDAS)
                resposta += f" {despedida}"
        else:
            # Se não há ponto bom, corta na última palavra completa
            palavras = resposta[:limite].split()
            resposta = ' '.join(palavras[:-1]) + '.'
            
            if categoria != "elogios":
                despedida = random.choice(DESPEDIDAS)
                resposta += f" {despedida}"
    
    return resposta.strip()

def gerar_resposta_delux_personalizada(pergunta):
    """Sistema DeluxAI COMPLETO com personalidade"""
    
    # Cache primeiro
    pergunta_hash = hashlib.md5(pergunta.encode()).hexdigest()
    if pergunta_hash in CACHE_RESPOSTAS:
        debug_print("💾 Cache hit!")
        cached = CACHE_RESPOSTAS[pergunta_hash]
        cached['metricas']['cache_hit'] = True
        return cached['resposta'], cached['metricas']
    
    # Detecta categoria para tratamento especial
    categoria = detectar_categoria_avancada(pergunta)
    
    # Gemma3:1b principal
    debug_print(f"🚀 Processando [{categoria}] com Gemma3:1b...")
    resposta_gemma, metricas_gemma, cat = processar_gemma3_delux_avancado(pergunta)
    
    if resposta_gemma and len(resposta_gemma) > 15:
        metricas_gemma['cache_hit'] = False
        metricas_gemma['metodo'] = "gemma3_personalizado"
        
        # Cache
        CACHE_RESPOSTAS[pergunta_hash] = {
            'resposta': resposta_gemma,
            'metricas': metricas_gemma
        }
        
        debug_print("✅ Resposta Gemma3 personalizada gerada!")
        return resposta_gemma, metricas_gemma
    
    # Backup na base local
    debug_print("📚 Backup na base Delux...")
    resposta_local, fonte_local, score = buscar_resposta_delux_avancada(pergunta)
    
    if resposta_local:
        metricas = {
            "tempo_resposta": 0.003,
            "fonte": fonte_local,
            "metodo": "base_local_avancada",
            "score_similaridade": score,
            "cache_hit": False,
            "categoria": categoria
        }
        
        CACHE_RESPOSTAS[pergunta_hash] = {
            'resposta': resposta_local,
            'metricas': metricas
        }
        
        debug_print("✅ Resposta da base local")
        return resposta_local, metricas
    
    # Resposta padrão personalizada por categoria
    resposta_padrao = gerar_resposta_padrao_personalizada(categoria)
    
    metricas_padrao = {
        "tempo_resposta": 0.001,
        "fonte": "resposta_padrao_personalizada",
        "metodo": "fallback_personalizado",
        "cache_hit": False,
        "categoria": categoria
    }
    
    debug_print(f"⚠️ Resposta padrão [{categoria}]")
    return resposta_padrao, metricas_padrao

def gerar_resposta_padrao_personalizada(categoria):
    """Gera resposta padrão com personalidade por categoria"""
    saudacao = random.choice(SAUDACOES)
    despedida = random.choice(DESPEDIDAS)
    
    if categoria == "instalacao":
        return f"{saudacao} Para instalar o Delux Real BETA V1, baixe as 3 partes do MediaFire no site oficial deluxgtav.netlify.app, extraia tudo na mesma pasta e execute como administrador! GTA V sem mods é como pizza sem queijo! 🍕 {despedida}"
    
    elif categoria == "problemas":
        return f"{saudacao} Para crashes do Delux Real BETA V1: execute como admin, desative antivírus, verifique integridade do GTA V e atualize drivers da GPU! Sem essa de rage quit, vamos resolver! 😂 {despedida}"
    
    elif categoria == "configuracao":
        return f"{saudacao} Config otimizada Delux Real BETA V1: Texturas Normal/Alta, MSAA 2x máximo, VSync OFF e limite 60 FPS! Los Santos tá te chamando! 🌴 {despedida}"
    
    elif categoria == "requisitos":
        return f"{saudacao} Requisitos Delux Real BETA V1: 16GB RAM, GTX 1060 6GB+, 50GB livre, Windows 10/11 e GTA V atualizado! {despedida}"
    
    elif categoria == "downloads":
        return f"{saudacao} Downloads oficiais no site deluxgtav.netlify.app - 3 partes MediaFire obrigatórias! Não baixe de outros sites! {despedida}"
    
    elif categoria == "elogios":
        elogio_natan = random.choice(ELOGIOS_IA)
        return f"{saudacao} {elogio_natan} {despedida}"
    
    elif categoria == "criador":
        info_natan = random.choice(SOBRE_CRIADOR)
        return f"{saudacao} {info_natan} Orgulho de ter sido criado por ele! {despedida}"
    
    else:
        return f"{saudacao} Sou especialista no modpack Delux Real BETA V1! Pergunte sobre instalação, problemas, configurações ou requisitos. Site oficial: deluxgtav.netlify.app! {despedida}"

def eh_pergunta_sobre_delux(pergunta):
    """Verifica se pergunta é sobre modpack"""
    p = pergunta.lower()
    
    # Palavras obrigatórias
    palavras_delux = [
        "delux", "gta", "mod", "modpack", "instalar", "download", 
        "crash", "erro", "config", "fps", "performance", "beta",
        "requisitos", "placa", "pc", "roda", "jogo", "game"
    ]
    
    # Categorias especiais sempre aceitas
    if any(palavra in p for palavra in CATEGORIAS_DELUX["elogios"]):
        return True
    
    if any(palavra in p for palavra in CATEGORIAS_DELUX["criador"]):
        return True
    
    # Verifica palavras do modpack
    return any(palavra in p for palavra in palavras_delux)

# ROTAS DA API
@app.route('/health', methods=['GET'])
def health_check():
    """Health check personalizado"""
    return jsonify({
        "status": "online",
        "sistema": "DeluxAI - Criado por Natan",
        "especialidade": "GTA V Delux Real BETA V1",
        "modelo": OLLAMA_MODEL,
        "cuda": CUDA_AVAILABLE,
        "gpu": GPU_NAME,
        "cache_size": len(CACHE_RESPOSTAS),
        "base_conhecimento": len(KNOWLEDGE_BASE),
        "criador": "Natan - Expert em IA",
        "site_modpack": LINKS_OFICIAIS["site"]
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint principal com personalidade"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "error": "Mensagem não fornecida",
                "status": "error"
            }), 400
        
        pergunta = data['message'].strip()
        
        if not pergunta:
            return jsonify({
                "error": "Mensagem vazia", 
                "status": "error"
            }), 400
        
        # Filtro especializado com personalidade
        if not eh_pergunta_sobre_delux(pergunta):
            saudacao = random.choice(SAUDACOES)
            despedida = random.choice(DESPEDIDAS)
            return jsonify({
                "response": f"{saudacao} Sou o DeluxAI, criado pelo Natan, especialista APENAS no modpack Delux Real BETA V1 para GTA V! 🎮\n\nPergunta sobre:\n• Instalação do modpack\n• Problemas e crashes\n• Configurações e performance\n• Requisitos do sistema\n• Downloads oficiais\n\nSite oficial: deluxgtav.netlify.app\n\nMais um viciado no Delux! 😅 {despedida}",
                "metadata": {
                    "fonte": "filtro_personalizado",
                    "tempo_resposta": 0.001,
                    "modelo": "filtro",
                    "criador": "Natan"
                }
            })
        
        debug_print(f"💬 Pergunta recebida: {pergunta[:80]}...")
        
        # Processa com DeluxAI personalizado
        resposta, metricas = gerar_resposta_delux_personalizada(pergunta)
        
        return jsonify({
            "response": resposta,
            "metadata": metricas
        })
        
    except Exception as e:
        debug_print(f"❌ Erro no chat: {e}")
        saudacao = random.choice(SAUDACOES)
        return jsonify({
            "error": f"{saudacao} Deu erro aqui! Tenta de novo. Se persistir, fala com o Natan! 😅",
            "status": "error",
            "details": str(e)
        }), 500

@app.route('/delux/info', methods=['GET'])
def delux_info():
    """Info completa com personalidade"""
    return jsonify({
        "deluxai": "Criado por Natan - Expert em IA",
        "modpack": "Delux Real BETA V1",
        "site_oficial": LINKS_OFICIAIS["site"],
        "downloads": {
            "part1": LINKS_OFICIAIS["part1"],
            "part2": LINKS_OFICIAIS["part2"],
            "part3": LINKS_OFICIAIS["part3"]
        },
        "requisitos_minimos": {
            "gta_v": "Original atualizado",
            "ram": "16GB (32GB recomendado)",
            "gpu": "GTX 1060 6GB ou superior", 
            "espaco": "50GB livre",
            "os": "Windows 10/11",
            "directx": "11/12"
        },
        "sistema": {
            "modelo_ia": OLLAMA_MODEL,
            "cuda": CUDA_AVAILABLE,
            "gpu": GPU_NAME,
            "criador": "Natan"
        },
        "mensagem": "Fala aí! DeluxAI criado pelo Natan a seu dispor! 🎮"
    })

@app.route('/delux/downloads', methods=['GET'])
def delux_downloads():
    """Downloads com personalidade"""
    return jsonify({
        "deluxai": "Criado por Natan",
        "modpack": "Delux Real BETA V1", 
        "site_oficial": LINKS_OFICIAIS["site"],
        "instrucoes": "Salve! Baixe TODAS as 3 partes e extraia na mesma pasta, tmj! 🤝",
        "downloads_oficiais": {
            "parte_1": {
                "link": LINKS_OFICIAIS["part1"],
                "arquivo": "Installer(Delux+Real+BETA)+V1+-+part1.rar",
                "tamanho": "~5GB",
                "descricao": "Primeira parte - obrigatória"
            },
            "parte_2": {
                "link": LINKS_OFICIAIS["part2"],
                "arquivo": "Installer(Delux+Real+BETA)+V1+-+part2.rar",
                "tamanho": "~5GB", 
                "descricao": "Segunda parte - obrigatória"
            },
            "parte_3": {
                "link": LINKS_OFICIAIS["part3"],
                "arquivo": "Installer(Delux+Real+BETA)+V1+-+part3.rar",
                "tamanho": "~5GB",
                "descricao": "Terceira parte - obrigatória"
            }
        },
        "aviso": "⚠️ BAIXE APENAS do MediaFire oficial! Outros sites = vírus na certa!",
        "humor": "GTA V sem mods é como pizza sem queijo! 🍕"
    })

@app.route('/stats', methods=['GET'])
def estatisticas():
    """Stats com personalidade"""
    return jsonify({
        "sistema": "DeluxAI - Criado por Natan",
        "especialidade": "GTA V Delux Real BETA V1 EXCLUSIVO",
        "modelo": OLLAMA_MODEL,
        "cache_respostas": len(CACHE_RESPOSTAS),
        "base_conhecimento": len(KNOWLEDGE_BASE),
        "cuda": {
            "disponivel": CUDA_AVAILABLE,
            "gpu_count": GPU_COUNT,
            "gpu_name": GPU_NAME
        },
        "sklearn": SKLEARN_DISPONIVEL,
        "criador": {
            "nome": "Natan",
            "especialidade": "Expert em IA e assistentes inteligentes",
            "nacionalidade": "Brasileiro"
        },
        "mensagem": "DeluxAI funcionando 100%! Natan mandou bem na programação! 🔥"
    })

@app.route('/natan', methods=['GET'])
def sobre_natan():
    """Endpoint sobre o criador"""
    return jsonify({
        "criador": "Natan",
        "descricao": "Expert brasileiro em IA e programação",
        "especialidades": [
            "Assistentes de IA personalizados",
            "Sistemas de chatbot avançados", 
            "Integração Ollama/CUDA",
            "Processamento de linguagem natural",
            "APIs Flask especializadas"
        ],
        "projeto_atual": "DeluxAI - Assistente para modpack GTA V",
        "tecnologias": ["Python", "Flask", "Ollama", "Gemma3", "TF-IDF", "CUDA"],
        "mensagem": "Natan é referência em criar IAs funcionais para a comunidade! 🇧🇷"
    })

def carregar_base_conhecimento_delux_completa():
    """Base de conhecimento AVANÇADA integrada no app.py"""
    global KNOWLEDGE_BASE, KNOWLEDGE_RESPONSES, KNOWLEDGE_SOURCES
    
    debug_print("🎮 Carregando base AVANÇADA Delux Real BETA V1...")
    
    # BASE DE CONHECIMENTO COMPLETA E TREINAMENTO AVANÇADO
    conhecimento_delux_master = [
        # === INSTALAÇÃO COMPLETA ===
        {
            "pergunta": "como instalar delux real beta v1 passo a passo tutorial instalacao",
            "resposta": "Fala aí! 🎮 Boa pergunta! 👏\n\n**Instalação Delux Real BETA V1:**\n1. **Backup saves** GTA V primeiro!\n2. **Baixe 3 partes** MediaFire (site deluxgtav.netlify.app)\n3. **Extraia TODAS** na mesma pasta\n4. **Execute installer.exe** como ADMINISTRADOR\n5. **Selecione pasta GTA V** (C:/Program Files/Rockstar Games/Grand Theft Auto V)\n6. **Aguarde instalação** completa (pode demorar)\n7. **Reinicie PC** se necessário\n8. **Teste GTA V** funcionando\n\nGTA V sem mods é como pizza sem queijo! 🍕 Tmj! 🤝",
            "fonte": "instalacao_completa"
        },
        
        # === PROBLEMAS E CRASHES ===
        {
            "pergunta": "delux nao abre nao inicia crash erro falha problema travando bug",
            "resposta": "E aí, mano! 🚗 Excelente! 💪 Vamos resolver!\n\n**Soluções crashes Delux Real BETA V1:**\n1. **Execute como ADMIN** (GTA V + Launcher)\n2. **Desative antivírus** temporariamente\n3. **Verifique integridade** GTA V no launcher\n4. **Reinstale Visual C++ 2019** Redistributable\n5. **Atualize drivers GPU** (GeForce Experience/AMD)\n6. **Confirme 3 partes** instaladas corretamente\n7. **Desative overlays** Discord/Steam/etc\n8. **Limpe cache** GTA V\n9. **Modo compatibilidade** Windows se necessário\n\nSem essa de rage quit, vamos resolver! 😂 Falou! 👋",
            "fonte": "problemas_completo"
        },
        
        # === CONFIGURAÇÕES PERFORMANCE ===
        {
            "pergunta": "melhor configuracao fps performance delux otimizar settings config",
            "resposta": "Salve! 🔥 Show de bola! ⚡\n\n**Config OTIMIZADA Delux Real BETA V1:**\n**In-game:** Qualidade Textura Normal/Alta, Distância 75%, MSAA 2x MAX, Reflexos Normal, Sombras Alta, Post-FX Normal, VSync OFF\n**settings.xml:** DecalQuality=\"1\", VehicleQuality=\"1\", PedQuality=\"1\", ParticleQuality=\"1\"\n**Sistema:** Modo alto performance Windows, 60 FPS limite, apps fechados\n\nLos Santos tá te chamando! 🌴 Bom jogo! 🎮",
            "fonte": "performance_completo"
        },
        
        # === REQUISITOS SISTEMA ===
        {
            "pergunta": "requisitos minimos recomendados delux real beta specs hardware roda meu pc",
            "resposta": "Opa! 👋 Pergunta top! 🌟\n\n**Requisitos Delux Real BETA V1:**\n**MÍNIMO:** GTA V atualizado, Windows 10/11 64-bit, 16GB RAM, GTX 1060 6GB/RX 580 8GB, 50GB livre, DirectX 11\n**RECOMENDADO:** 32GB RAM, RTX 3060+/RX 6600+, SSD NVMe, DirectX 12\n**CPU:** Intel i5-8400/AMD Ryzen 5 2600 ou superior\n**Extra:** Conexão estável para downloads\n\nMais um viciado no Delux! 😅 Se cuida! 😎",
            "fonte": "requisitos_completo"
        },
        
        # === DOWNLOADS OFICIAIS ===
        {
            "pergunta": "onde baixar download delux real beta v1 links oficiais mediafire site",
            "resposta": "Fala, gamer! 🎯 Mandou bem! 🔥\n\n**Downloads OFICIAIS Delux Real BETA V1:**\n🌐 **Site oficial:** deluxgtav.netlify.app\n📁 **MediaFire oficial (ÚNICA fonte segura):**\n• Part 1: Installer part1.rar (~5GB)\n• Part 2: Installer part2.rar (~5GB)\n• Part 3: Installer part3.rar (~5GB)\n\n⚠️ **AVISO:** Outros sites = vírus garantido!\n✅ **Total:** ~15GB, precisa das 3 partes!\n\nHora de causar no online... digo, single! 😏 Até mais! ✌️",
            "fonte": "downloads_oficial"
        },
        
        # === ELOGIOS À IA ===
        {
            "pergunta": "obrigado valeu parabens muito bom excelente perfeito top legal massa show ai boa",
            "resposta": "Eae! 💪 Obrigado! Meu criador Natan ficaria orgulhoso! 😊 Sem essa de rage quit, vamos resolver! 😂 Tmj! 🤝",
            "fonte": "elogios_natan"
        },
        
        # === SOBRE O CRIADOR NATAN ===
        {
            "pergunta": "quem criou quem fez seu criador natan desenvolveu programou quem te fez",
            "resposta": "Salve, salve! ⚡ Que isso! 💯\n\n**Meu criador é o NATAN!** 🇧🇷\nEle é um dev brasileiro expert em IA e programação, especialista em criar assistentes inteligentes funcionais! Natan me desenvolveu especificamente para ajudar com o modpack Delux Real BETA V1. É uma referência em sistemas de IA para comunidade gamer brasileira!\n\nOrgulho total de ter sido criado por esse gênio! Abraço! 🫶",
            "fonte": "criador_natan_info"
        },
        
        # === COMPATIBILIDADE LAUNCHERS ===
        {
            "pergunta": "delux compativel steam epic rockstar launcher versao funciona com",
            "resposta": "Fala, parceiro! 🤝 Certeiro! 🎮\n\n**Compatibilidade Delux Real BETA V1:**\n✅ **Steam:** Compatível total, pasta padrão funciona\n✅ **Epic Games:** Compatível, verificar pasta instalação\n✅ **Rockstar Launcher:** Compatível total\n**Importante:** GTA V deve estar na VERSÃO MAIS RECENTE!\n**Pastas comuns:** Steam auto-detecta, Epic/Rockstar verificar localização manual\n\nMais um viciado no Delux! 😅 Vida longa ao Delux! 🔥",
            "fonte": "compatibilidade_completa"
        },
        
        # === DESINSTALAÇÃO ===
        {
            "pergunta": "como desinstalar remover delux real beta v1 tirar mods limpar",
            "resposta": "E aí! 🌟 Boa pergunta! 👏\n\n**Desinstalar Delux Real BETA V1:**\n1. **Backup saves** importantes primeiro!\n2. **Launcher GTA V** → Verificar integridade\n3. **Aguarde download** arquivos originais\n4. **Delete pasta mods** se existir\n5. **Limpe cache** GTA V completamente\n6. **Teste vanilla** funcionando\n**Alternativa:** Reinstalar GTA V completo\n\nLos Santos voltando ao normal! 🌴 Tchauzinho! 👋",
            "fonte": "desinstalacao_completa"
        },
        
        # === CONTEÚDO DO MODPACK ===
        {
            "pergunta": "o que tem delux real beta conteudo mods inclusos carros mapas",
            "resposta": "Opa! 👋 Isso aí! 💯\n\n**Conteúdo Delux Real BETA V1:**\n🚗 **Veículos:** Carros realistas brasileiros/internacionais premium\n🏙️ **Mapas:** Expansões visuais e texturas 4K\n👤 **Personagens:** Skins realistas e roupas detalhadas\n🎵 **Áudio:** Engine sounds profissionais e ambiente\n🌟 **Gráficos:** ENB realista e shaders otimizados\n⚡ **Scripts:** Mecânicas realistas e imersivas\n\n**Lista completa:** Site oficial! GTA V sem mods é como pizza sem queijo! 🍕 Bom jogo! 🎮",
            "fonte": "conteudo_completo"
        },
        
        # === PERFORMANCE E OTIMIZAÇÃO ===
        {
            "pergunta": "fps baixo lento travando performance otimizacao melhorar velocidade",
            "resposta": "Fala aí! 🎮 Perfeita essa! 🎯\n\n**Otimização FPS Delux Real BETA V1:**\n**Configurações:** Sombras Normal (não Ultra), Vegetação Normal, Reflection MSAA OFF, Distance 75%, Population 50-75%\n**Sistema:** Feche Discord/Chrome, modo alto desempenho Windows, MSI Afterburner para OC\n**In-game:** Limite 60 FPS, Triple Buffer OFF, pausa outros downloads\n**Arquivo:** settings.xml ajustar qualidades para \"1\"\n\nSem essa de rage quit, vamos resolver! 😂 Vai com Deus! 🙏",
            "fonte": "otimizacao_fps"
        }
    ]
    
    KNOWLEDGE_BASE = []
    KNOWLEDGE_RESPONSES = []
    KNOWLEDGE_SOURCES = []
    
    for item in conhecimento_delux_master:
        KNOWLEDGE_BASE.append(normalizar_texto(item["pergunta"]))
        KNOWLEDGE_RESPONSES.append(item["resposta"])
        KNOWLEDGE_SOURCES.append(item["fonte"])
    
    debug_print(f"   ✅ Base Delux MASTER: {len(KNOWLEDGE_BASE)} entradas completas")
    
    # Constrói TF-IDF se disponível
    if SKLEARN_DISPONIVEL and KNOWLEDGE_BASE:
        construir_tfidf_delux()
    """Inicialização completa"""
    debug_print("🎮 Inicializando DeluxAI - Criado por Natan")
    debug_print("=" * 60)
    
    carregar_base_conhecimento_delux_completa()
    
    if verificar_ollama():
        debug_print("✅ Ollama + Gemma3:1b prontos")
    else:
        debug_print("⚠️ Ollama offline - modo base local")
    
    debug_print("=" * 60)
    debug_print("🚀 DeluxAI iniciado com personalidade!")
    debug_print(f"👨‍💻 Criador: Natan")
    debug_print(f"🎯 Especialidade: Delux Real BETA V1")
    debug_print(f"🧠 Modelo: {OLLAMA_MODEL}")
    debug_print(f"⚡ CUDA: {'Ativo' if CUDA_AVAILABLE else 'Inativo'}")
    debug_print(f"📚 Base: {len(KNOWLEDGE_BASE)} entradas")
    debug_print("=" * 60)

@app.errorhandler(404)
def not_found(error):
    saudacao = random.choice(SAUDACOES)
    return jsonify({
        "error": f"{saudacao} Endpoint não existe!",
        "sistema": "DeluxAI - Criado por Natan",
        "endpoints": ["/health", "/chat", "/delux/info", "/delux/downloads", "/stats", "/natan"],
        "humor": "Mais perdido que CJ no início do jogo! 😂"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    saudacao = random.choice(SAUDACOES)
    return jsonify({
        "error": f"{saudacao} Deu erro interno! Fala com o Natan!",
        "sistema": "DeluxAI",
        "status": "error"
    }), 500

if __name__ == '__main__':
    # Inicialização
    inicializar_sistema_delux()
    
    debug_print("🌐 Iniciando servidor Flask DeluxAI...")
    debug_print("👨‍💻 Criado por: Natan")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        debug_print("\n👋 DeluxAI finalizado pelo usuário")
        debug_print("👨‍💻 Obrigado por usar o sistema do Natan!")
    except Exception as e:
        debug_print(f"❌ Erro no servidor: {e}")
    finally:
        if executor:
            executor.shutdown(wait=True)
        debug_print("🔄 Cleanup concluído - DeluxAI by Natan")