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

# Cache e dados - INICIALIZAÇÃO CORRIGIDA
CACHE_RESPOSTAS = {}
KNOWLEDGE_BASE = {}
HISTORICO_CONVERSAS = []  # Inicialização explícita
PING_INTERVAL = 300

# Lock para thread safety
import threading
historico_lock = threading.Lock()

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

# Inicia thread de auto-ping
threading.Thread(target=auto_ping, daemon=True).start()

# Personalidade - Janine (SIMPLIFICADA)
SAUDACOES = [
    "Olá! Sou a Janine",
    "Oi! Como posso ajudar?",
    "Seja bem-vindo!",
    "Oi, tudo bem?",
    "Olá! Em que posso ajudar?",
    "Oi! Bem-vindo!"
]

DESPEDIDAS = [
    "Até logo! Vibrações Positivas!",
    "Tchau! Vibrações Positivas!",
    "Até mais! Vibrações Positivas!",
    "Nos falamos! Vibrações Positivas!"
]

ELOGIOS_IA_RESPOSTAS = [
    "Obrigada! Fico feliz em ajudar!",
    "Que bom! Estou aqui para isso!",
    "Muito obrigada! É um prazer ajudar!",
    "Obrigada! Adoro poder ser útil!"
]

ELOGIOS_ESPACO_RESPOSTAS = [
    "Que bom que gostou! Nosso espaço é muito especial!",
    "Obrigada! O ambiente foi feito com muito carinho!",
    "Fico feliz! A natureza aqui é única!",
    "Que alegria! Nosso espaço tem essa magia!"
]

# Sistema de análise de intenção - Janine Melhorado
def analisar_intencao(pergunta):
    """Analisa a intenção das perguntas sobre o espaço de festas"""
    try:
        p = pergunta.lower().strip()
        
        intencoes = {
            "saudacao": 0,
            "despedida": 0,
            "elogio_ia": 0,
            "elogio_espaco": 0,
            "sobre_ia": 0,
            "sobre_espaco": 0,
            "orcamento": 0,
            "contato": 0,
            "visita": 0,
            "localizacao": 0,
            "horarios": 0,
            "capacidade": 0,
            "eventos": 0,
            "missao": 0,
            "marcar_evento": 0,  # NOVA INTENÇÃO
            "geral": 0
        }
        
        # PALAVRAS-CHAVE EXPANDIDAS
        
        # NOVA CATEGORIA: Marcar Evento
        palavras_marcar_evento = [
            "marcar um evento", "quero marcar", "vou marcar", "preciso marcar",
            "quero um evento", "vou querer um evento", "preciso de um evento",
            "quero fazer uma festa", "vou fazer uma festa", "preciso fazer uma festa",
            "quero agendar", "vou agendar", "preciso agendar",
            "quero reservar", "vou reservar", "preciso reservar",
            "tenho interesse", "estou interessado", "gostaria de fazer",
            "como faço", "como marco", "como reservo", "como contrato",
            "quero fazer", "vou fazer", "preciso fazer", "gostaria",
            "posso marcar", "posso fazer", "posso agendar", "posso reservar",
            "queria fazer", "queria marcar", "queria agendar"
        ]
        
        # Sobre a IA
        palavras_sobre_ia = [
            "janine", "ai", "inteligencia artificial", "o que você é", 
            "quem é você", "você é uma ia", "como funciona", "que ia é essa",
            "para que serve", "o que faz", "sua função"
        ]
        
        # Sobre o Espaço
        palavras_sobre_espaco = [
            "sobre o espaço", "sobre vocês", "quem são", "empresa", "negócio",
            "espaço de festas", "sobre o local", "história", "como começou"
        ]
        
        # Orçamento
        palavras_orcamento = [
            "orçamento", "preço", "valor", "quanto custa", "custo", "orçar",
            "tabela de preços", "valores", "cotação", "quanto fica", "preços",
            "quanto sai", "investimento", "taxa", "pacote"
        ]
        
        # Contato
        palavras_contato = [
            "contato", "whatsapp", "telefone", "numero", "falar", "ligar",
            "alexandre", "responsavel", "dono", "conversar", "entrar em contato",
            "whats", "zap", "chamar"
        ]
        
        # Visita
        palavras_visita = [
            "visita", "conhecer", "ver", "visitar", "mostrar", "agendar visita",
            "ir ai", "ir aí", "ir lá", "conhecer o espaço", "ver o local"
        ]
        
        # Localização
        palavras_localizacao = [
            "endereço", "onde fica", "localização", "local", "vargem grande",
            "cabungui", "pacuí", "rio de janeiro", "rj", "como chegar",
            "fica onde", "estrada"
        ]
        
        # Horários
        palavras_horarios = [
            "horario", "horários", "que horas", "funcionamento", "aberto",
            "das 8h", "18h", "manhã", "tarde", "noite", "fim de semana",
            "sabado", "domingo", "quando funciona"
        ]
        
        # Capacidade
        palavras_capacidade = [
            "capacidade", "quantas pessoas", "100 pessoas", "100 convidados",
            "cabem quantas", "lotação", "máximo", "limite", "comporta"
        ]
        
        # Eventos
        palavras_eventos = [
            "festa", "evento", "aniversario", "casamento", "formatura", "batizado",
            "chá", "confraternização", "celebração", "comemoração", "reunião familiar",
            "tipos de festa", "que eventos", "festas familiares"
        ]
        
        # Missão
        palavras_missao = [
            "missão", "objetivo", "proposta", "filosofia", "unir familias",
            "energia da natureza", "momentos inesquecíveis", "porque escolher"
        ]
        
        # Elogio à IA
        palavras_elogio_ia = [
            "você é boa", "você é ótima", "ia boa", "ia incrível", "você ajuda bem",
            "gostei de você", "você é legal", "ia legal", "ia eficiente", "boa ia",
            "janine boa", "janine legal"
        ]
        
        # Elogio ao Espaço
        palavras_elogio_espaco = [
            "espaço lindo", "lugar bonito", "espaço incrível", "ambiente lindo",
            "local perfeito", "espaço maravilhoso", "lugar show", "ambiente show",
            "espaço top", "local top", "lugar lindo", "energia boa", "vibração boa"
        ]
        
        # Saudação
        palavras_saudacao = [
            "oi", "olá", "ola", "hey", "eai", "e ai", "fala", "bom dia", "boa tarde",
            "boa noite", "tudo bem", "beleza", "como vai", "seja bem vindo"
        ]
        
        # Despedida
        palavras_despedida = [
            "tchau", "bye", "até logo", "até mais", "ate mais", "nos falamos",
            "obrigado", "obrigada", "valeu", "até breve", "até a próxima"
        ]
        
        # CONTAGEM COM PESOS
        
        # PRIORIDADE MÁXIMA para marcar evento
        for palavra in palavras_marcar_evento:
            if palavra in p:
                intencoes["marcar_evento"] += 8
        
        for palavra in palavras_sobre_ia:
            if palavra in p:
                intencoes["sobre_ia"] += 5
        
        for palavra in palavras_sobre_espaco:
            if palavra in p:
                intencoes["sobre_espaco"] += 5
        
        for palavra in palavras_orcamento:
            if palavra in p:
                intencoes["orcamento"] += 6
        
        for palavra in palavras_contato:
            if palavra in p:
                intencoes["contato"] += 6
        
        for palavra in palavras_visita:
            if palavra in p:
                intencoes["visita"] += 5
        
        for palavra in palavras_localizacao:
            if palavra in p:
                intencoes["localizacao"] += 5
        
        for palavra in palavras_horarios:
            if palavra in p:
                intencoes["horarios"] += 5
        
        for palavra in palavras_capacidade:
            if palavra in p:
                intencoes["capacidade"] += 5
        
        for palavra in palavras_eventos:
            if palavra in p:
                intencoes["eventos"] += 4
        
        for palavra in palavras_missao:
            if palavra in p:
                intencoes["missao"] += 5
        
        for palavra in palavras_elogio_ia:
            if palavra in p:
                intencoes["elogio_ia"] += 6
        
        for palavra in palavras_elogio_espaco:
            if palavra in p:
                intencoes["elogio_espaco"] += 6
        
        for palavra in palavras_saudacao:
            if palavra in p:
                intencoes["saudacao"] += 4
        
        for palavra in palavras_despedida:
            if palavra in p:
                intencoes["despedida"] += 4
        
        # Retorna a intenção com maior score
        intencao_principal = max(intencoes, key=intencoes.get)
        score_principal = intencoes[intencao_principal]
        
        return intencao_principal if score_principal > 1 else "geral"
    
    except Exception as e:
        print(f"❌ Erro na análise de intenção: {e}")
        return "geral"

# Base de conhecimento - Janine EXPANDIDA E SIMPLIFICADA
def carregar_conhecimento_especializado():
    global KNOWLEDGE_BASE
    
    try:
        KNOWLEDGE_BASE = {
            "saudacao": {
                "resposta": """Olá! Sou a Janine!

Ajudo com informações sobre nosso espaço para festas em Vargem Grande.

Posso te ajudar com:
- Orçamentos (WhatsApp: 21 98124-6196)
- Agendamento de visitas
- Festas para até 100 pessoas
- Localização em Vargem Grande
- Horários: 8h às 18h (sábado ou domingo)

Em que posso ajudar você?

Vibrações Positivas!""",
                "keywords": ["oi", "ola", "hey", "bom dia", "boa tarde", "tudo bem"]
            },
            
            "despedida": {
                "resposta": random.choice(DESPEDIDAS),
                "keywords": ["tchau", "bye", "até logo", "obrigado", "valeu"]
            },
            
            "sobre_ia": {
                "resposta": """Sou a Janine!

Sou uma inteligência artificial criada para ajudar famílias com eventos especiais em nosso espaço em Vargem Grande.

Posso te ajudar com:
- Orçamentos: 21 98124-6196 (Alexandre)
- Agendar visitas para conhecer o espaço
- Informações sobre festas até 100 pessoas
- Localização: Vargem Grande - RJ
- Horários: 8h às 18h (sábado ou domingo)

Nossa missão: Unir famílias com a energia da natureza!

Como posso te ajudar hoje?

Vibrações Positivas!""",
                "keywords": ["janine", "o que você é", "quem é você", "para que serve"]
            },

            "sobre_espaco": {
                "resposta": """Sobre nosso espaço:

Local: Estrada do Cabungui, 772, Vargem Grande - RJ
Para festas e eventos familiares
Até 100 convidados

Nossa missão:
Unir famílias para momentos especiais com a energia da natureza!

Diferenciais:
- Energia da natureza em Vargem Grande
- Ambiente familiar e acolhedor
- Apenas um evento por fim de semana
- Foco total na sua festa

A energia deste ambiente faz toda diferença no seu evento!

Quer saber sobre orçamentos ou visitas?

Vibrações Positivas!""",
                "keywords": ["sobre o espaço", "sobre vocês", "empresa", "negócio"]
            },
            
            "elogio_ia": {
                "resposta": random.choice(ELOGIOS_IA_RESPOSTAS),
                "keywords": ["você é boa", "ia boa", "você ajuda bem", "gostei de você", "janine boa"]
            },
            
            "elogio_espaco": {
                "resposta": random.choice(ELOGIOS_ESPACO_RESPOSTAS),
                "keywords": ["espaço lindo", "lugar bonito", "ambiente lindo", "local perfeito"]
            },

            # NOVA RESPOSTA PARA MARCAR EVENTOS
            "marcar_evento": {
                "resposta": """Que ótimo! Vou te ajudar a marcar seu evento!

Para marcar sua festa, é simples:

1. Chame Alexandre no WhatsApp: 21 98124-6196
2. Conte sobre sua festa:
   - Que tipo de evento (aniversário, casamento, etc.)
   - Quantos convidados (até 100 pessoas)
   - Data desejada (sábado ou domingo)

3. Alexandre vai fazer seu orçamento personalizado

Informações importantes:
- Horário: 8h às 18h
- Local: Vargem Grande - RJ
- Apenas um evento por fim de semana
- Ambiente familiar com energia da natureza

Também pode agendar uma visita para conhecer o espaço!

Chame Alexandre agora: 21 98124-6196

Vibrações Positivas!""",
                "keywords": ["marcar evento", "quero evento", "fazer festa", "agendar", "reservar"]
            },
            
            "orcamento": {
                "resposta": """Orçamentos:

Para seu orçamento personalizado:
WhatsApp: 21 98124-6196 (Alexandre)

Cada evento é único, Alexandre faz orçamento sob medida considerando:
- Tipo de evento
- Número de convidados (até 100 pessoas)
- Data escolhida (sábado ou domingo)
- Horário: 8h às 18h

Vantagens:
- Apenas um evento por fim de semana
- Localização em Vargem Grande
- Energia da natureza

Entre em contato pelo WhatsApp para seu orçamento!

Vibrações Positivas!""",
                "keywords": ["orçamento", "preço", "valor", "quanto custa", "custo"]
            },

            "contato": {
                "resposta": """Contato:

WhatsApp: 21 98124-6196 (Alexandre)

Alexandre ajuda com:
- Orçamentos personalizados
- Agendamento de visitas
- Planejamento de eventos familiares
- Informações sobre o espaço

Como entrar em contato:
- Chame no WhatsApp: 21 98124-6196
- Diga que soube pela Janine
- Conte sobre seu evento
- Receba atendimento personalizado

Alexandre responde rapidamente durante o dia.

A equipe está pronta para seu evento especial!

Vibrações Positivas!""",
                "keywords": ["contato", "whatsapp", "telefone", "alexandre", "falar", "ligar"]
            },
            
            "visita": {
                "resposta": """Visitas ao espaço:

Para agendar sua visita:
WhatsApp: 21 98124-6196 (Alexandre)

O que você verá:
- Ambiente natural em Vargem Grande
- Estrutura completa para festas
- Energia especial da natureza
- Espaço para até 100 convidados

Localização:
Estrada do Cabungui, 772
Vargem Grande - Rio de Janeiro

Por que visitar:
- Sentir a energia única do ambiente
- Conhecer nossa estrutura completa
- Tirar dúvidas pessoalmente
- Ver sua festa dos sonhos

A energia deste ambiente faz toda diferença no seu evento!

Chame Alexandre para agendar!

Vibrações Positivas!""",
                "keywords": ["visita", "conhecer", "ver", "agendar visita"]
            },

            "localizacao": {
                "resposta": """Localização:

Endereço:
Estrada do Cabungui, 772
(continuação da Estrada do Pacuí)
Vargem Grande - Rio de Janeiro / RJ

Por que Vargem Grande:
- Energia da natureza única
- Ambiente tranquilo e familiar
- Localização no Rio de Janeiro
- Atmosfera especial para eventos

Como chegar:
- Região de fácil acesso
- Estacionamento disponível
- Ambiente seguro

Para orientações:
WhatsApp: 21 98124-6196 (Alexandre)

A localização traz energia especial da natureza!

Quer agendar uma visita?

Vibrações Positivas!""",
                "keywords": ["endereço", "onde fica", "localização", "vargem grande"]
            },

            "horarios": {
                "resposta": """Horários:

Horário para eventos:
Das 8h às 18h

Disponibilidade:
- Finais de semana: Sábado OU Domingo
- Apenas um evento por fim de semana
- Não fazemos eventos noturnos

Vantagens do nosso horário:
- Manhã: Perfeita para chás e eventos matinais
- Tarde: Ideal para almoços e festas
- Até 18h: Tempo suficiente para celebrar
- Luz natural: Aproveita a beleza do dia

Por que esse horário:
- Segurança para famílias
- Energia positiva da luz natural
- Ambiente familiar
- Foco total no seu evento

Para agendar sua data:
WhatsApp: 21 98124-6196 (Alexandre)

Vibrações Positivas!""",
                "keywords": ["horario", "que horas", "funcionamento", "8h", "18h"]
            },

            "capacidade": {
                "resposta": """Capacidade:

Nosso espaço comporta até 100 convidados

Estrutura pensada para:
- Festas familiares de todos os tamanhos
- Eventos íntimos ou celebrações maiores
- Conforto para todos os convidados
- Ambiente acolhedor

Vantagens da nossa capacidade:
- Tamanho ideal para festas familiares
- Mantém ambiente familiar
- Comporta toda família
- Apenas seu evento no dia

Perfeito para:
- Aniversários familiares
- Batizados e chás
- Casamentos íntimos
- Formaturas
- Confraternizações familiares

Para mais detalhes:
WhatsApp: 21 98124-6196 (Alexandre)

Nosso espaço tem o tamanho perfeito!

Vibrações Positivas!""",
                "keywords": ["capacidade", "quantas pessoas", "100", "convidados", "comporta"]
            },
            
            "eventos": {
                "resposta": """Tipos de eventos:

Celebrações familiares que fazemos:
- Aniversários (adulto e infantil)
- Batizados
- Chás (baby shower, revelação, fraldas)
- Formaturas
- Casamentos íntimos
- Confraternizações
- Reuniões familiares especiais

Nosso diferencial:
- Apenas um evento por fim de semana
- Horário: 8h às 18h (sábado ou domingo)
- Ambiente familiar em Vargem Grande
- Energia da natureza
- Até 100 convidados

Nossa filosofia:
Unir famílias para momentos especiais com energia da natureza!

Para planejar seu evento:
WhatsApp: 21 98124-6196 (Alexandre)

Que tipo de festa você está pensando?

Vibrações Positivas!""",
                "keywords": ["festa", "evento", "aniversario", "casamento", "celebração"]
            },

            "missao": {
                "resposta": """Nossa missão:

"Unir famílias e amigos para momentos especiais com a energia da natureza!"

O que isso significa:

Unir famílias e amigos:
- Ambiente perfeito para conexões especiais
- Espaço para fortalecer laços familiares
- Celebrações que aproximam pessoas queridas

De forma leve:
- Tranquilidade no ambiente natural
- Das 8h às 18h para aproveitar
- Apenas seu evento no fim de semana
- Leveza da natureza de Vargem Grande

Momentos especiais:
- Celebrações que ficam na memória
- Energia especial do ambiente natural
- Atmosfera única

Com energia da natureza:
- Localização em Vargem Grande
- Ambiente natural que renova energias
- Vibrações positivas do local

A energia deste ambiente faz diferença no seu evento!

Converse conosco: 21 98124-6196 (Alexandre)

Vibrações Positivas!""",
                "keywords": ["missão", "objetivo", "proposta", "filosofia", "unir familias"]
            }
        }
        
        print(f"✅ Base Janine carregada: {len(KNOWLEDGE_BASE)} categorias")
        
    except Exception as e:
        print(f"❌ Erro ao carregar base de conhecimento: {e}")
        KNOWLEDGE_BASE = {}

# Busca resposta especializada
def buscar_resposta_especializada(pergunta):
    try:
        intencao = analisar_intencao(pergunta)
        
        print(f"🎯 Intenção detectada: {intencao} para: '{pergunta[:50]}...'")
        
        if intencao in KNOWLEDGE_BASE:
            resposta = KNOWLEDGE_BASE[intencao]["resposta"]
            
            # Para despedidas e elogios, pode variar
            if intencao == "despedida":
                resposta = random.choice(DESPEDIDAS)
            elif intencao == "elogio_ia":
                resposta = random.choice(ELOGIOS_IA_RESPOSTAS)
            elif intencao == "elogio_espaco":
                resposta = random.choice(ELOGIOS_ESPACO_RESPOSTAS)
                
            return resposta
        
        return None
        
    except Exception as e:
        print(f"❌ Erro na busca especializada: {e}")
        return None

# Processamento Ollama focado em eventos - MELHORADO E SIMPLIFICADO
def processar_ollama_focado(pergunta, intencao):
    if not verificar_ollama():
        return None
    
    try:
        # Informações do espaço para contexto
        info_espaco = """
ESPAÇO PARA FESTAS FAMILIARES - VARGEM GRANDE:
- Local: Estrada do Cabungui, 772, Vargem Grande - RJ
- Capacidade: Até 100 convidados
- Horário: Das 8h às 18h (sábado OU domingo)
- WhatsApp: 21 98124-6196 (Alexandre)
- Missão: "Unir famílias e amigos, de forma leve e plena, com a energia da natureza"
- Exclusividade: Apenas um evento por fim de semana
- Não fazemos eventos noturnos ou pernoite
"""
        
        # Prompts específicos SIMPLIFICADOS
        prompts = {
            "saudacao": "Faça uma saudação simples como Janine:",
            "despedida": "Faça uma despedida educada:",
            "sobre_ia": "Explique que você é a Janine de forma simples:",
            "sobre_espaco": "Fale sobre o espaço de festas de forma simples:",
            "elogio_ia": "Responda positivamente ao elogio:",
            "elogio_espaco": "Responda ao elogio sobre o espaço:",
            "marcar_evento": "Explique como marcar evento de forma simples, direcionando para WhatsApp:",
            "orcamento": "Responda sobre orçamentos de forma simples:",
            "contato": "Forneça informações de contato de forma simples:",
            "visita": "Explique sobre visitas de forma simples:",
            "localizacao": "Forneça a localização de forma simples:",
            "horarios": "Explique horários de forma simples:",
            "capacidade": "Explique capacidade de forma simples:",
            "eventos": "Fale sobre tipos de eventos de forma simples:",
            "missao": "Explique nossa missão de forma simples:",
            "geral": "Responda sobre o espaço de forma simples:"
        }
        
        prompt_base = prompts.get(intencao, prompts["geral"])
        
        prompt = f"""Você é Janine, assistente do espaço para festas familiares.

{info_espaco}

PERSONALIDADE: Simples, clara, direta, sem palavras difíceis. Use linguagem fácil de entender.

REGRAS IMPORTANTES:
- Use PALAVRAS SIMPLES e FRASES CURTAS
- NÃO use palavras complicadas ou técnicas
- Seja DIRETA, sem rodeios
- Sempre termine com "Vibrações Positivas!"
- Mencione WhatsApp 21 98124-6196 (Alexandre) quando relevante
- Máximo 200 palavras

EXEMPLO DE LINGUAGEM SIMPLES:
❌ "estabelecimento com características diferenciadas"
✅ "lugar especial"
❌ "proporcionar experiências memoráveis"  
✅ "fazer festas inesquecíveis"

FOCO: {intencao.upper()}

{prompt_base} {pergunta}

Resposta simples e clara:"""

        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "num_predict": 200,
                "temperature": 0.2,
                "top_k": 20,
                "top_p": 0.8,
                "repeat_penalty": 1.1,
                "stop": ["</s>", "Human:", "PERGUNTA:", "Usuario:"]
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
                resposta_limpa = limpar_resposta_focada(resposta)
                # Adiciona "Vibrações Positivas!" se não tiver
                if "vibrações positivas" not in resposta_limpa.lower():
                    resposta_limpa += "\n\nVibrações Positivas!"
                return resposta_limpa
        
        return None
        
    except Exception as e:
        print(f"❌ Erro Ollama: {e}")
        return None

# Limpeza de resposta melhorada
def limpar_resposta_focada(resposta):
    try:
        # Remove prefixos desnecessários
        prefixos = [
            "Resposta simples:", "Janine:", "Como Janine",
            "RESPOSTA:", "Resposta:", "FOCO:", "Olá!", "Oi!"
        ]
        
        for prefixo in prefixos:
            if resposta.startswith(prefixo):
                resposta = resposta[len(prefixo):].strip()
        
        # Limita tamanho
        if len(resposta) > 600:
            corte = resposta[:600]
            ultimo_ponto = corte.rfind('.')
            if ultimo_ponto > 400:
                resposta = resposta[:ultimo_ponto + 1]
        
        return resposta.strip()
        
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")
        return resposta

# Verificação expandida para perguntas relacionadas
def eh_pergunta_festa_focada(pergunta):
    try:
        p = pergunta.lower().strip()
        
        # Sempre aceita saudações, despedidas e elogios
        if len(pergunta) < 50:
            if any(s in p for s in ["oi", "ola", "hey", "bom dia", "boa tarde", "tudo bem"]):
                return True
            if any(d in p for d in ["tchau", "bye", "até logo", "obrigado", "valeu"]):
                return True
            if any(e in p for e in ["legal", "bom", "boa", "lindo", "bonito", "incrivel", "top"]):
                return True
        
        # Keywords expandidas incluindo MARCAR EVENTO
        keywords_aceitas = [
            # Marcar evento - NOVA CATEGORIA
            "marcar", "quero", "vou", "preciso", "fazer", "agendar", "reservar",
            "gostaria", "posso", "queria", "tenho interesse", "estou interessado",
            "como faço", "como marco", "como reservo", "como contrato",
            
            # Sobre a IA
            "janine", "ai", "ia", "você", "quem é", "o que é", "para que serve",
            
            # Festas e eventos
            "festa", "evento", "aniversario", "casamento", "batizado", "chá", "formatura",
            "celebração", "comemoração", "confraternização", "reunião",
            
            # Serviços
            "orçamento", "preço", "valor", "custo", "visita", "conhecer",
            
            # Localização e estrutura
            "endereço", "localização", "horário", "vargem grande", "cabungui", "pacuí",
            "rio de janeiro", "rj", "onde fica", "como chegar",
            
            # Espaço e estrutura
            "espaço", "local", "lugar", "ambiente", "salão", "estrutura", "capacidade",
            "100 pessoas", "convidados", "comporta",
            
            # Horários
            "horario", "8h", "18h", "manhã", "tarde", "sabado", "domingo", "fim de semana",
            
            # Contato
            "contato", "whatsapp", "telefone", "alexandre", "falar", "ligar", "chamar",
            
            # Filosofia
            "missão", "energia", "natureza", "vibração", "unir", "família", "familias",
            
            # Família
            "familiar", "família", "familias", "parentes",
            
            # Gerais
            "como", "onde", "quando", "quanto", "qual", "quem", "esse", "isso", "porque"
        ]
        
        # Se tem QUALQUER palavra relacionada, aceita
        if any(keyword in p for keyword in keywords_aceitas):
            return True
            
        return False
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return True  # Em caso de erro, aceita a pergunta

# Gerador principal melhorado com tratamento de erros
def gerar_resposta_otimizada(pergunta):
    global HISTORICO_CONVERSAS  # Declare explicitamente como global
    
    try:
        # Cache
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
        
        # Resposta de fallback melhorada E SIMPLIFICADA
        fallbacks = {
            "saudacao": "Olá! Sou a Janine do espaço de festas em Vargem Grande! Como posso ajudar? Vibrações Positivas!",
            "despedida": "Até logo! Fico à disposição para ajudar com seu evento! Vibrações Positivas!",
            "sobre_ia": "Sou a Janine! Ajudo com festas familiares em Vargem Grande. Posso falar sobre orçamentos, visitas e eventos! Vibrações Positivas!",
            "sobre_espaco": "Nosso espaço em Vargem Grande é perfeito para festas familiares! Até 100 pessoas, das 8h às 18h. WhatsApp: 21 98124-6196 (Alexandre). Vibrações Positivas!",
            "elogio_ia": "Obrigada! Fico feliz em ajudar! Vibrações Positivas!",
            "elogio_espaco": "Que bom que gostou! Nosso espaço em Vargem Grande é muito especial! Vibrações Positivas!",
            "marcar_evento": "Que legal! Para marcar sua festa é fácil: Chame Alexandre no WhatsApp 21 98124-6196. Ele vai fazer seu orçamento e cuidar de tudo! Vibrações Positivas!",
            "orcamento": "Para orçamento chame Alexandre no WhatsApp: 21 98124-6196. Cada festa é única! Vibrações Positivas!",
            "contato": "WhatsApp: 21 98124-6196 (Alexandre). Ele cuida de orçamentos e visitas! Vibrações Positivas!",
            "visita": "Para visitar nosso espaço chame Alexandre: 21 98124-6196. Você vai amar a energia do lugar! Vibrações Positivas!",
            "localizacao": "Estrada do Cabungui, 772, Vargem Grande - RJ. Um local com energia da natureza! Vibrações Positivas!",
            "horarios": "Funcionamos das 8h às 18h, sábado ou domingo. Apenas um evento por fim de semana! Vibrações Positivas!",
            "capacidade": "Nosso espaço é perfeito para até 100 pessoas! Ideal para festas familiares! Vibrações Positivas!",
            "eventos": "Fazemos aniversários, batizados, chás, casamentos e formaturas! WhatsApp: 21 98124-6196. Vibrações Positivas!",
            "missao": "Nossa missão: Unir famílias para momentos especiais com a energia da natureza! Vibrações Positivas!",
            "geral": "Sou a Janine do espaço de festas em Vargem Grande! Como posso ajudar com seu evento? Vibrações Positivas!"
        }
        
        resposta_fallback = fallbacks.get(intencao, fallbacks["geral"])
        
        CACHE_RESPOSTAS[pergunta_hash] = resposta_fallback
        print("⚠️ Resposta fallback melhorada")
        return resposta_fallback
        
    except Exception as e:
        print(f"❌ Erro na geração de resposta: {e}")
        return "Sou a Janine do espaço de festas em Vargem Grande! Como posso ajudar com seu evento? WhatsApp: 21 98124-6196 (Alexandre). Vibrações Positivas!"

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
    try:
        return jsonify({
            "status": "online_janine_ai",
            "sistema": "Janine AI - Espaço para Festas Familiares",
            "especialidade": "Vargem Grande - Rio de Janeiro",
            "contato": "WhatsApp: 21 98124-6196 (Alexandre)",
            "missao": "Unir famílias e amigos com energia da natureza",
            "modelo": OLLAMA_MODEL,
            "ollama_ativo": verificar_ollama(),
            "cache_size": len(CACHE_RESPOSTAS),
            "categorias": list(KNOWLEDGE_BASE.keys()) if KNOWLEDGE_BASE else [],
            "funcionalidades": [
                "Saudações e despedidas",
                "Informações sobre Janine",
                "Detalhes sobre o espaço",
                "MARCAR EVENTOS - NOVA FUNCIONALIDADE",
                "Orçamentos via WhatsApp",
                "Agendamento de visitas",
                "Localização em Vargem Grande",
                "Horários de funcionamento",
                "Capacidade até 100 convidados",
                "Tipos de eventos familiares",
                "Missão e filosofia"
            ],
            "info_espaco": {
                "endereco": "Estrada do Cabungui, 772, Vargem Grande - RJ",
                "capacidade": "Até 100 convidados",
                "horarios": "Das 8h às 18h",
                "dias": "Sábado OU Domingo",
                "exclusividade": "Apenas um evento por fim de semana",
                "whatsapp": "21 98124-6196 (Alexandre)"
            }
        })
    except Exception as e:
        return jsonify({"error": f"Erro no health check: {e}"}), 500

@app.route('/chat', methods=['POST'])
def chat_janine_ai():
    global HISTORICO_CONVERSAS  # Declare explicitamente como global
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida"}), 400
        
        pergunta = data['message'].strip()
        if not pergunta:
            return jsonify({"error": "Mensagem vazia"}), 400
        
        print(f"💬 [{datetime.now().strftime('%H:%M:%S')}] Pergunta: {pergunta}")
        
        # Inicializa HISTORICO_CONVERSAS se não existir (failsafe)
        if 'HISTORICO_CONVERSAS' not in globals():
            HISTORICO_CONVERSAS = []
        
        # Filtro para temas relacionados a festas/eventos - SIMPLIFICADO
        if not eh_pergunta_festa_focada(pergunta):
            resposta_filtro = "Olá! Sou a Janine do espaço para festas familiares em Vargem Grande! Posso ajudar com: orçamentos, visitas, localização, horários e tipos de eventos. WhatsApp: 21 98124-6196 (Alexandre). Como posso ajudar com seu evento? Vibrações Positivas!"
            return jsonify({
                "response": resposta_filtro,
                "metadata": {
                    "fonte": "filtro_janine_ai", 
                    "tipo": "especialidade_limitada",
                    "sistema": "Janine AI"
                }
            })
        
        # Gera resposta
        resposta = gerar_resposta_otimizada(pergunta)
        
        # Determina fonte
        intencao = analisar_intencao(pergunta)
        if intencao in KNOWLEDGE_BASE:
            fonte = f"base_janine_{intencao}"
        elif verificar_ollama():
            fonte = f"ollama_janine_{intencao}"
        else:
            fonte = f"fallback_janine_{intencao}"
        
        # Histórico para análise com thread safety
        try:
            with historico_lock:
                HISTORICO_CONVERSAS.append({
                    "timestamp": datetime.now().isoformat(),
                    "pergunta": pergunta,
                    "intencao": intencao,
                    "fonte": fonte,
                    "resposta_size": len(resposta)
                })
                
                # Limita histórico
                if len(HISTORICO_CONVERSAS) > 1000:
                    HISTORICO_CONVERSAS = HISTORICO_CONVERSAS[-500:]
        except Exception as hist_error:
            print(f"⚠️ Erro no histórico: {hist_error}")
        
        return jsonify({
            "response": resposta,
            "metadata": {
                "fonte": fonte,
                "intencao": intencao,
                "modelo": OLLAMA_MODEL,
                "sistema": "Janine AI",
                "especialidade": "Festas Familiares - Vargem Grande",
                "contato": "21 98124-6196 (Alexandre)"
            }
        })
        
    except Exception as e:
        print(f"❌ Erro no chat: {e}")
        return jsonify({
            "response": "Desculpe, tive um problema. Sou a Janine e ajudo com eventos familiares em Vargem Grande! WhatsApp: 21 98124-6196 (Alexandre). Vibrações Positivas!",
            "error": "erro_temporario"
        }), 500

@app.route('/estatisticas', methods=['GET'])
def estatisticas():
    """Nova rota para estatísticas da Janine"""
    try:
        # Inicializa se não existir
        if 'HISTORICO_CONVERSAS' not in globals() or not HISTORICO_CONVERSAS:
            return jsonify({
                "total_conversas": 0,
                "intencoes": {},
                "message": "Nenhuma conversa registrada ainda"
            })
        
        # Análise do histórico
        intencoes_count = {}
        fontes_count = {}
        
        with historico_lock:
            for conversa in HISTORICO_CONVERSAS:
                intencao = conversa.get("intencao", "geral")
                fonte = conversa.get("fonte", "unknown")
                
                intencoes_count[intencao] = intencoes_count.get(intencao, 0) + 1
                fontes_count[fonte] = fontes_count.get(fonte, 0) + 1
            
            ultima_conversa = HISTORICO_CONVERSAS[-1]["timestamp"] if HISTORICO_CONVERSAS else None
            total_conversas = len(HISTORICO_CONVERSAS)
        
        return jsonify({
            "total_conversas": total_conversas,
            "intencoes_populares": dict(sorted(intencoes_count.items(), key=lambda x: x[1], reverse=True)),
            "fontes_utilizadas": fontes_count,
            "sistema": "Janine AI",
            "especialidade": "Festas Familiares - Vargem Grande",
            "ultima_conversa": ultima_conversa
        })
        
    except Exception as e:
        return jsonify({"error": f"Erro nas estatísticas: {e}"}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "sistema": "Janine AI - Auto-Ping Ativo",
        "especialidade": "Festas Familiares - Vargem Grande",
        "contato": "WhatsApp: 21 98124-6196 (Alexandre)"
    })

@app.route('/', methods=['GET'])
def home():
    """Interface web simples para testar a Janine"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Janine AI - Teste</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f8ff; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; color: #4a90e2; margin-bottom: 20px; }
            .chat-box { border: 1px solid #ddd; height: 400px; overflow-y: scroll; padding: 10px; margin: 10px 0; background: #fafafa; border-radius: 5px; }
            .input-area { display: flex; gap: 10px; }
            input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { padding: 10px 20px; background: #4a90e2; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #357abd; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background: #e3f2fd; text-align: right; }
            .bot { background: #f1f8e9; }
            .info { font-size: 12px; color: #666; text-align: center; margin: 20px 0; }
            .nova { background: #fffbf0; border: 2px solid #ffc107; padding: 10px; margin: 10px 0; border-radius: 5px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Janine AI</h1>
                <p>Espaço para Festas Familiares - Vargem Grande</p>
                <p><strong>WhatsApp:</strong> 21 98124-6196 (Alexandre)</p>
            </div>
            
            <div class="nova">
                <strong>NOVO!</strong> Agora a Janine entende quando você quer marcar um evento!<br>
                Experimente: "Quero marcar um evento" ou "Vou fazer uma festa"
            </div>
            
            <div id="chat-box" class="chat-box">
                <div class="message bot">
                    Olá! Sou a Janine!<br><br>
                    Ajudo com informações sobre nosso espaço para festas familiares em Vargem Grande!<br><br>
                    <strong>Vibrações Positivas!</strong>
                </div>
            </div>
            
            <div class="input-area">
                <input type="text" id="message-input" placeholder="Digite sua pergunta sobre eventos familiares..." onkeypress="if(event.key==='Enter') enviarMensagem()">
                <button onclick="enviarMensagem()">Enviar</button>
            </div>
            
            <div class="info">
                <p><strong>Local:</strong> Estrada do Cabungui, 772, Vargem Grande - RJ</p>
                <p><strong>Horários:</strong> Das 8h às 18h (sábado ou domingo)</p>
                <p><strong>Capacidade:</strong> Até 100 convidados</p>
                <p><strong>Eventos:</strong> Aniversários, Batizados, Chás, Casamentos, Formaturas</p>
            </div>
        </div>

        <script>
        async function enviarMensagem() {
            const input = document.getElementById('message-input');
            const chatBox = document.getElementById('chat-box');
            const mensagem = input.value.trim();
            
            if (!mensagem) return;
            
            // Adiciona mensagem do usuário
            chatBox.innerHTML += `<div class="message user"><strong>Você:</strong> ${mensagem}</div>`;
            input.value = '';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: mensagem })
                });
                
                const data = await response.json();
                
                // Adiciona resposta da IA
                chatBox.innerHTML += `<div class="message bot"><strong>Janine:</strong> ${data.response.replace(/\n/g, '<br>')}</div>`;
                
            } catch (error) {
                chatBox.innerHTML += `<div class="message bot"><strong>Janine:</strong> Erro de conexão. Tente novamente! Vibrações Positivas!</div>`;
            }
            
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    print("Janine AI - Espaço para Festas Familiares")
    print("=" * 70)
    print("IA: Janine")  
    print("Local: Vargem Grande - Rio de Janeiro")
    print("Endereço: Estrada do Cabungui, 772")
    print("WhatsApp: 21 98124-6196 (Alexandre)")
    print("Capacidade: Até 100 convidados")
    print("Horários: Das 8h às 18h (sábado ou domingo)")
    print("Especialidade: Festas Familiares")
    print("Missão: Unir famílias com energia da natureza")
    print("=" * 70)
    
    # Carrega base de conhecimento
    try:
        carregar_conhecimento_especializado()
    except Exception as e:
        print(f"⚠️ Erro ao carregar conhecimento: {e}")
    
    # Status
    if verificar_ollama():
        print("✅ Ollama CONECTADO - Modo Híbrido")
    else:
        print("⚠️ Ollama offline - Modo Base Própria")
    
    print("MELHORIAS APLICADAS:")
    print("   ✅ NOVA FUNCIONALIDADE: Marcar Eventos")
    print("   ✅ Textos SIMPLIFICADOS e CLAROS")
    print("   ✅ Palavras fáceis de entender")
    print("   ✅ Frases mais diretas")
    print("   ✅ Reconhece várias formas de pedir evento:")
    print("      - 'Quero marcar um evento'")
    print("      - 'Vou querer um evento'")
    print("      - 'Preciso fazer uma festa'")
    print("      - 'Gostaria de agendar'")
    print("      - E muitas outras variações!")
    print("   ✅ Interface web atualizada")
    print("🔄 Auto-ping ativo (5min)")
    print("🌐 Interface web disponível em /")
    print("📊 Estatísticas em /estatisticas")
    print("🚀 Servidor iniciando na porta 5001...")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )