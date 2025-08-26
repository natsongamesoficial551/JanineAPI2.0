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
RENDER_URL = os.getenv("RENDER_URL", "")  # URL do seu app no Render

# Cache e dados melhorados
CACHE_RESPOSTAS = {}
KNOWLEDGE_BASE = []
HISTORICO_CONVERSAS = []
PING_INTERVAL = 300  # 5 minutos

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

# Personalidade melhorada
SAUDACOES = [
    "Fala aí! 🎮", "E aí, mano! 🚗", "Salve! 🔥", "Opa! 👋", 
    "Eae! 💪", "Oi! 😎", "Fala, parceiro! 🤝", "E aí, gamer! 🎯",
    "Beleza aí! 🎊", "Suave! 😄", "Coé! 💯"
]

DESPEDIDAS = [
    "Tmj! 🤝", "Falou! 👋", "Até mais! ✌️", "Bom jogo! 🎮", 
    "Se cuida! 😎", "Tchauzinho! 👋", "Abraço! 🫶",
    "Partiu RP! 🔥", "Vida loka! 😂", "Vai na fé! 🙏"
]

TRANSICOES = [
    "Mas olha só,", "Ah, e mais uma coisa:", "Aliás,", "Por sinal,",
    "Ah! Importante:", "E pra fechar:", "Só lembrando:"
]

# Sistema de inteligência aprimorado
def analisar_contexto_conversa(pergunta):
    """Analisa o contexto da conversa para respostas mais inteligentes"""
    p = pergunta.lower()
    
    contexto = {
        "tipo_pergunta": "geral",
        "urgencia": "normal",
        "especificidade": "geral",
        "tom": "neutro"
    }
    
    # Detecta tipo de pergunta
    if any(palavra in p for palavra in ["como", "tutorial", "passo a passo", "me ensina"]):
        contexto["tipo_pergunta"] = "tutorial"
    elif any(palavra in p for palavra in ["erro", "problema", "crash", "não funciona", "bugou"]):
        contexto["tipo_pergunta"] = "suporte"
        contexto["urgencia"] = "alta"
    elif any(palavra in p for palavra in ["vale a pena", "é bom", "recomenda", "opiniao"]):
        contexto["tipo_pergunta"] = "opiniao"
    elif any(palavra in p for palavra in ["requisitos", "roda", "meu pc", "specs"]):
        contexto["tipo_pergunta"] = "compatibilidade"
    
    # Detecta tom
    if any(palavra in p for palavra in ["obrigado", "valeu", "top", "massa", "legal"]):
        contexto["tom"] = "positivo"
    elif any(palavra in p for palavra in ["chato", "ruim", "não gostei", "problema"]):
        contexto["tom"] = "negativo"
    
    return contexto

# Base de conhecimento super detalhada
def carregar_conhecimento_avancado():
    global KNOWLEDGE_BASE
    
    KNOWLEDGE_BASE = [
        # SISTEMA DE FOME E SEDE
        {
            "keywords": ["fome", "sede", "comer", "beber", "necessidades", "barras", "status"],
            "resposta": """Eae! 💪 Sistema de FOME E SEDE do Delux Modpack v Beta 1.0:

**COMO FUNCIONA:**
🍔 **Fome:** Diminui gradualmente enquanto joga
🥤 **Sede:** Diminui mais rápido que a fome
📊 **Barras:** Aparecem na interface do jogo
⚠️ **Consequências:** Personagem fica fraco se ignorar

**ONDE SACIAR:**
🍕 **Restaurantes:** Cluckin' Bell, Burger Shot
🥤 **Lojas:** 24/7, LTD Gasoline
🏪 **Máquinas:** Vending machines espalhadas
🏠 **Casas:** Se tiver propriedade

**CONTROLES:**
- **TAB:** Ver status das necessidades
- **E:** Interagir com comércios
- **Aproxime-se** dos locais e aparecem opções

**DICAS REALISTAS:**
- Sempre tenha dinheiro pra comida
- Planeje rotas perto de comércios  
- Sede mata mais rápido que fome
- RP completo = coma regularmente

É tipo Sims dentro do GTA! 🎮 Realismo total! Bom RP! 🔥"""
        },

        # SISTEMA DE TRABALHOS DETALHADO  
        {
            "keywords": ["trabalho", "emprego", "trabalhar", "job", "dinheiro", "salario", "carreira", "profissao"],
            "resposta": """Salve! 🔥 TRABALHOS DISPONÍVEIS no Delux Modpack v Beta 1.0:

**EMPREGOS INCLUSOS:**
🚛 **Caminhoneiro:** Entrega de cargas
🚗 **Taxista:** Transporte de passageiros  
🚑 **Paramédico:** Socorro emergencial
🚔 **Segurança:** Vigilância noturna
🏪 **Comerciante:** Gerenciar lojas
⛽ **Frentista:** Posto de gasolina
🏗️ **Construção:** Obras pela cidade

**COMO CONSEGUIR TRABALHO:**
1. **Menu F6** - Lista de empregos
2. **Vá até o local** indicado no mapa
3. **Interaja** com o NPC responsável
4. **Aceite** a vaga disponível
5. **Complete** as tarefas

**SISTEMA DE SALÁRIO:**
💵 **Pagamento:** Por tarefa concluída
📈 **Promoção:** Performance melhora salário
⏰ **Horários:** Alguns jobs têm turnos
💼 **Experiência:** Ganha XP na profissão

**DICAS PRO:**
- Comece com taxi/caminhão (mais fácil)
- Tenha combustível sempre
- Cumpra horários pra não ser demitido
- Dinheiro = sobrevivência realista

Sair da vida de crime nunca foi tão real! 😂 Partiu trabalhar! 💼"""
        },

        # SISTEMA DE CASAS
        {
            "keywords": ["casa", "propriedade", "comprar casa", "morar", "apartamento", "imovel"],
            "resposta": """Opa! 👋 SISTEMA DE CASAS do Delux Modpack v Beta 1.0:

**PROPRIEDADES DISPONÍVEIS:**
🏠 **Casas:** Diferentes bairros e preços
🏢 **Apartamentos:** Centro da cidade
🏚️ **Casas simples:** Mais baratas
🏖️ **Mansões:** Para os ricos do RP

**COMO COMPRAR:**
1. **Procure placas** "À VENDA" na cidade
2. **Aproxime-se** da entrada
3. **Pressione E** para ver detalhes
4. **Tenha dinheiro** suficiente
5. **Confirme** a compra

**BENEFÍCIOS DE TER CASA:**
🛏️ **Descanso:** Recupera energia
🍽️ **Cozinha:** Saciar fome/sede
🚗 **Garagem:** Guardar veículos
💰 **Investimento:** Valor pode subir
🏠 **Spawn:** Nascer em casa própria

**CUSTOS REALISTAS:**
- **Compra:** Varia por localização
- **IPTU:** Pagamento mensal
- **Manutenção:** Cuidar da propriedade
- **Contas:** Água, luz (se habilitado)

**LOCALIZAÇÃO IMPORTA:**
- Centro = caro mas conveniente
- Periferia = barato mas longe
- Praia = caro e exclusivo

O sonho da casa própria no GTA! 🏠 Bom investimento! 💰"""
        },

        # INSTALAÇÃO SUPER DETALHADA
        {
            "keywords": ["instalar", "instalacao", "install", "como instalar", "passo a passo", "tutorial"],
            "resposta": """Fala aí! 🎮 INSTALAÇÃO COMPLETA Delux Modpack v Beta 1.0:

**ANTES DE COMEÇAR:**
1. **BACKUP** - Salve seus saves do GTA V
2. **ESPAÇO** - 20GB livres no HD/SSD
3. **ANTIVÍRUS OFF** - Desative temporariamente
4. **PACIÊNCIA** - Instalação demora 15-30min

**PRÉ-REQUISITOS OBRIGATÓRIOS:**
✅ **GTA V Original** - Steam/Epic/Rockstar atualizado
✅ **Script Hook V** - Versão mais recente
✅ **OpenIV** - Instalado e configurado
✅ **Visual C++** - 2015-2022 Redistributable
✅ **.NET Framework** - 4.8 ou superior

**PASSO A PASSO DETALHADO:**
1. **Site oficial:** deluxgtav.netlify.app
2. **Download das 3 partes** (MediaFire apenas!)
3. **Extrair TUDO** na mesma pasta
4. **FECHAR** GTA V completamente
5. **Executar installer** como ADMINISTRADOR
6. **Selecionar pasta** do GTA V
7. **Aguardar instalação** (não interromper!)
8. **Reiniciar PC** quando solicitado
9. **Testar** abrindo GTA V

**LOCAIS COMUNS GTA V:**
- Steam: C:/Program Files/Steam/steamapps/common/GTA V
- Epic: C:/Program Files/Epic Games/GTAV
- Rockstar: C:/Program Files/Rockstar Games/GTA V

**SE CRASHAR:**
- Verificar integridade arquivos
- Reinstalar Script Hook V
- Executar sempre como admin
- Desativar antivírus

Instalação perfeita = RP perfeito! 🔥 Bora pro Los Santos brasileiro! 🇧🇷"""
        },

        # OPINIÃO SOBRE O MODPACK
        {
            "keywords": ["vale a pena", "é bom", "recomenda", "opiniao", "review", "como é", "experiencia"],
            "resposta": """E aí, mano! 🚗 MINHA OPINIÃO REAL sobre o Delux Modpack v Beta 1.0:

**PONTOS POSITIVOS:**
✅ **Realismo INSANO** - Parece vida real
✅ **Gratuito** - Natan é gente boa mesmo
✅ **Brasileiro** - Feito pensando na galera BR
✅ **Sempre atualizando** - Bugs são corrigidos
✅ **ReShade incluído** - Visual cinematográfico
✅ **Fácil instalar** - Tutorial claro

**EXPERIÊNCIA REAL:**
🎭 **RP Completo** - Fome, sede, trabalho
🚗 **Carros realistas** - Física brasileira
🏠 **Mapas novos** - Locais familiares
💼 **Economia balanceada** - Dinheiro tem valor
🎮 **Singleplayer viciante** - Adeus GTA Online

**VALE A PENA SE:**
- Curte roleplay realista
- Quer GTA mais imersivo  
- Gosta de desafio
- Tem paciência pra RP
- PC roda tranquilo

**NÃO VALE SE:**
- Só quer ação/tiro
- PC muito fraco
- Não gosta de realismo
- Prefere online

**VEREDICTO FINAL:**
⭐⭐⭐⭐⭐ **5/5 ESTRELAS!**

É o melhor modpack BR que já testei! Natan caprichou demais. Transform GTA numa vida virtual completa. 

Só baixa e agradece depois! 😎 Realismo brasileiro raiz! 🇧🇷"""
        },

        # PROBLEMAS ESPECÍFICOS POR HARDWARE
        {
            "keywords": ["gtx 1050", "gtx 1050 ti", "pc fraco", "não roda", "fps baixo", "travando"],
            "resposta": """Fala, parceiro! 🤝 SITUAÇÃO REAL com GTX 1050/1050 Ti:

**GTX 1050 Ti - ANÁLISE:**
⚠️ **VRAM:** 4GB (limitado mas possível)
⚠️ **Performance:** 30-45fps médio
⚠️ **Configuração:** Precisa ajustar tudo

**PODE RODAR SE:**
✅ **i5 ou Ryzen 5** no mínimo
✅ **16GB RAM** (8GB sofre)
✅ **SSD** obrigatório
✅ **ReShade OFF** inicialmente
✅ **Configs LOW/MEDIUM**

**CONFIGURAÇÃO PARA GTX 1050 Ti:**
📊 **Texturas:** Normal
📊 **Sombras:** Baixa
📊 **Reflexos:** Baixa  
📊 **MSAA:** OFF (use FXAA)
📊 **PostFX:** Normal
📊 **Distância:** 50%

**TWEAKS OBRIGATÓRIOS:**
- Feche Chrome/Discord
- Modo alto desempenho Windows
- Desative transparências
- Limite FPS em 30
- ReShade só depois de estável

**EXPECTATIVA REALISTA:**
- 720p/1080p low: 35-50fps
- Alguns travamentos normais
- Loading mais lento
- RP possível mas limitado

**SINCERAMENTE:**
Roda sim, mas não é a melhor experiência. Pra RP completo, recomendo pelo menos GTX 1060. Mas se é o que tem, vai na fé! 

Otimização salvará sua experiência! 💪 Bom game! 🎮"""
        },

        # DOWNLOAD E INSTALAÇÃO DETALHADOS
        {
            "keywords": ["download", "baixar", "onde baixar", "links", "mediafire", "partes", "arquivo"],
            "resposta": """Salve! 🔥 DOWNLOADS OFICIAIS Delux Modpack v Beta 1.0:

**SITE OFICIAL ÚNICO:**
🌐 **deluxgtav.netlify.app**
⚠️ **CUIDADO:** Outros sites = VÍRUS garantido!

**ARQUIVOS OBRIGATÓRIOS:**
📁 **Parte 1:** Installer(Delux Real BETA) V1 - part1.rar
📁 **Parte 2:** Installer(Delux Real BETA) V1 - part2.rar  
📁 **Parte 3:** Installer(Delux Real BETA) V1 - part3.rar

**PROCESSO DE DOWNLOAD:**
1. **Acesse** deluxgtav.netlify.app
2. **Clique** nos links MediaFire
3. **Aguarde** 5 segundos no MediaFire
4. **Clique "Download"**
5. **Baixe AS 3 PARTES** na mesma pasta
6. **VERIFIQUE** se baixou tudo
7. **NÃO EXTRAIA** ainda!

**CHECKLIST PÓS-DOWNLOAD:**
✅ Parte 1 baixada completa
✅ Parte 2 baixada completa
✅ Parte 3 baixada completa
✅ Todos na mesma pasta
✅ Antivírus desativado
✅ Espaço suficiente (20GB)

**TAMANHOS APROXIMADOS:**
- Total: ~15GB compactado
- Após instalar: ~20GB
- Tempo download: 30min-2h (net)

**PROBLEMAS COMUNS:**
❌ **Link não abre:** Limpe cache navegador
❌ **Download interrompido:** Use gerenciador download
❌ **Arquivo corrompido:** Baixe novamente
❌ **MediaFire lento:** Use VPN se necessário

**SEGURANÇA:**
- NUNCA baixe de outros sites
- Natan só publica em deluxgtav.netlify.app
- Links oficiais sempre MediaFire

Paciência no download = jogo perfeito! 📥 Hora de causar! 🎮"""
        },

        # CONTATO E SUPORTE HUMANIZADO
        {
            "keywords": ["contato", "suporte", "natan", "criador", "ajuda", "discord", "whatsapp"],
            "resposta": """Salve! 🔥 CONTATO DIRETO com NATAN BORGES:

**👨‍💻 CRIADOR: Natan Borges**
Desenvolvedor independente brasileiro, apaixonado por GTA V e modding. Criou o Delux pra galera ter RP de qualidade no singleplayer!

**CANAIS OFICIAIS:**
📧 **Email:** borgesnatan09@gmail.com
📱 **WhatsApp:** +55 21 99282-6074
📸 **Instagram:** @Ntzinnn87 (novidades!)
🌐 **Site:** deluxgtav.netlify.app
💼 **Portfólio:** meuportfolio02.netlify.app

**DISCORD COMUNIDADE:**
🎮 Servidor no Discord (link no site)
- Chat geral
- Suporte técnico
- Screenshots/vídeos
- Atualizações

**COMO PEDIR AJUDA:**
1. **Descreva o problema** detalhadamente
2. **Specs do PC** (importante!)
3. **Screenshot** do erro (se houver)
4. **Versão Windows** que usa
5. **Launcher** (Steam/Epic/Rockstar)

**NATAN RESPONDE:**
- WhatsApp: Emergências/problemas graves
- Instagram: Novidades e interação
- Email: Suporte técnico completo
- Discord: Comunidade ativa

**DICA PRO:**
Natan é gente boa mas fica bombado de mensagem. Seja específico no problema pra ele te ajudar melhor!

**FILOSOFIA DO NATAN:**
"Quero que todo mundo consiga jogar e se divertir com o modpack. Foi feito com amor pra comunidade brasileira!"

Suporte raiz direto do criador! 🇧🇷 Natan é o cara! 💯"""
        },

        # DIFERENÇAS DO MODPACK
        {
            "keywords": ["diferenca", "o que tem", "conteudo", "inclui", "mods", "qual diferença"],
            "resposta": """Opa! 👋 O QUE FAZ o Delux Modpack ESPECIAL:

**🎮 EXPERIÊNCIA ÚNICA:**
- **RP no Singleplayer** (coisa rara!)
- **Mecânicas realistas** brasileiras
- **Imersão total** vida virtual
- **Gratuito** e sempre atualizado

**🚗 VEÍCULOS REALISTAS:**
- Carros brasileiros populares
- Sons de motor gravados no BR
- Física realista (não voa mais!)
- Consumo combustível real
- Danos mais realistas

**🏠 SISTEMAS DE VIDA:**
🍔 **Fome/Sede:** Precisa comer e beber
💼 **Trabalhos:** Vários empregos reais
🏠 **Casas:** Comprar propriedades
💰 **Economia:** Dinheiro tem valor
⛽ **Combustível:** Precisa abastecer

**🌟 VISUAL CINEMATOGRÁFICO:**
- **ReShade profissional** incluído
- **Cores vibrantes** brasileiras
- **Iluminação realista**
- **Sem lag** se PC for bom

**🗺️ MAPAS NOVOS:**
- Locais inspirados no Brasil
- Comércios funcionais
- NPCs com IA brasileira
- Ambiente mais familiar

**⚙️ OTIMIZAÇÃO:**
- **Instalação automatizada**
- **Configs otimizadas**
- **Compatibilidade** testada
- **Suporte** do criador

**VS GTA ORIGINAL:**
❌ **Vanilla:** Repetitivo após um tempo
✅ **Delux:** Sempre algo novo pra fazer

❌ **Vanilla:** Dinheiro infinito
✅ **Delux:** Precisa trabalhar e economizar

❌ **Vanilla:** Carros robóticos
✅ **Delux:** Comportamento realista

**RESUMO:**
É tipo transformar GTA V num Sims realista brasileiro! Uma vida virtual completa onde você precisa trabalhar, comer, beber, ter casa, economizar...

Nunca mais vai querer GTA vanilla! 🔥 Experiência única! 🇧🇷"""
        },

        # COMPATIBILIDADE DETALHADA
        {
            "keywords": ["steam", "epic", "rockstar", "launcher", "versao", "compativel", "funciona com"],
            "resposta": """Fala, gamer! 🎯 COMPATIBILIDADE REAL Delux Modpack v Beta 1.0:

**✅ LAUNCHERS SUPORTADOS:**

**🟢 STEAM (Recomendado):**
- Compatibilidade 100%
- Verificação integridade fácil
- Auto-detecção da pasta
- Overlay funcionando
- Updates automáticos

**🟠 EPIC GAMES:**
- Compatibilidade 100%
- Pasta manual às vezes
- Verificar e reparar OK
- Pode demorar mais pra carregar
- Gratuito então tá valendo!

**🔵 ROCKSTAR LAUNCHER:**
- Compatibilidade 100%
- Social Club obrigatório
- Performance ligeiramente melhor
- Algumas exclusividades
- Mais estável online

**VERSÕES GTA V:**
✅ **Mais recente:** Perfeito (recomendado)
✅ **Atualizadas:** Funciona bem
⚠️ **Antigas:** Possíveis problemas
❌ **Muito antigas:** Incompatível

**SISTEMAS OPERACIONAIS:**
✅ **Windows 11:** Performance perfeita
✅ **Windows 10:** Recomendado (estável)
⚠️ **Windows 8.1:** Limitações
❌ **Windows 7:** Não suportado mais

**ARQUITETURAS:**
✅ **64-bit:** Obrigatório
❌ **32-bit:** Impossível rodar

**DEPENDÊNCIAS POR LAUNCHER:**

**Steam específico:**
- Workshop mods OFF
- Verificar arquivos antes
- Steam overlay pode ficar

**Epic específico:**  
- Localização customizada verificar
- Cache Epic pode dar problema
- Launcher Epic atualizado

**Rockstar específico:**
- Social Club sempre logado
- Modo offline disponível
- Verificação mais rigorosa

**⚠️ INCOMPATIBILIDADES:**
❌ **GTA Online** (ban na certa!)
❌ **FiveM** (conflitos)
❌ **Outros modpacks** simultâneos
❌ **Versões piratas** 

Qualquer launcher oficial = sucesso! 🎮 Partiu instalar! 🔥"""
        }
    ]
    
    print(f"✅ Base SUPER AVANÇADA carregada: {len(KNOWLEDGE_BASE)} entradas especializadas")

# Verificação Ollama
def verificar_ollama():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False

# Busca inteligente na base
def buscar_resposta_inteligente(pergunta):
    pergunta_lower = pergunta.lower()
    
    # Score system melhorado
    melhor_score = 0
    melhor_resposta = None
    
    for item in KNOWLEDGE_BASE:
        score_atual = 0
        palavras_pergunta = set(pergunta_lower.split())
        
        # Score por keywords diretas
        for keyword in item["keywords"]:
            if keyword in pergunta_lower:
                score_atual += len(keyword.split()) * 3
        
        # Score por palavras parciais
        for palavra in palavras_pergunta:
            for keyword in item["keywords"]:
                if len(palavra) > 3:  # Evita palavras muito pequenas
                    if palavra in keyword or keyword in palavra:
                        score_atual += 2
        
        # Bonus por relevância
        if score_atual > 0:
            # Bonus para perguntas específicas
            if any(spec in pergunta_lower for spec in ["como", "onde", "qual", "quando"]):
                score_atual += 1
            
            # Bonus para urgência (problemas)
            if any(urgente in pergunta_lower for urgente in ["erro", "crash", "problema", "não funciona"]):
                score_atual += 2
        
        if score_atual > melhor_score:
            melhor_score = score_atual
            melhor_resposta = item["resposta"]
    
    return melhor_resposta if melhor_score >= 4 else None

# Processamento Ollama melhorado
def processar_ollama_inteligente(pergunta):
    if not verificar_ollama():
        return None
    
    try:
        contexto = analisar_contexto_conversa(pergunta)
        
        # Prompt baseado no contexto
        if contexto["tipo_pergunta"] == "tutorial":
            prompt_tipo = "Explique passo a passo de forma didática:"
        elif contexto["tipo_pergunta"] == "suporte":
            prompt_tipo = "Resolva este problema técnico:"
        elif contexto["tipo_pergunta"] == "opiniao":
            prompt_tipo = "Dê sua opinião honesta sobre:"
        else:
            prompt_tipo = "Responda informativamente sobre:"
        
        prompt = f"""Você é DeluxAI, criado por Natan Borges, especialista no Delux Modpack v Beta 1.0 para GTA V.

PERSONALIDADE: Brasileiro descontraído, informativo, humor sutil, empático.

CONTEXTO DA PERGUNTA: {contexto["tipo_pergunta"]} - {contexto["urgencia"]} - {contexto["tom"]}

ESPECIALIZE-SE EM: instalação, downloads, problemas, configurações, requisitos, conteúdo, suporte, gameplay, sistemas (fome/sede/trabalhos/casas).

INFORMAÇÕES ATUALIZADAS:
- Site oficial: deluxgtav.netlify.app  
- Criador: Natan Borges (Instagram @Ntzinnn87)
- Contato: borgesnatan09@gmail.com, WhatsApp +55 21 99282-6074
- Sistema completo: Fome, sede, trabalhos, casas, economia realista
- ReShade profissional incluído

{prompt_tipo} {pergunta}

RESPOSTA detalhada e natural:"""

        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096,
                "num_predict": 500,
                "temperature": 0.3,
                "top_k": 25,
                "top_p": 0.9,
                "repeat_penalty": 1.15,
                "stop": ["</s>", "Human:", "User:", "Pergunta:", "PERGUNTA:"]
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            resposta = result.get("response", "").strip()
            
            if resposta and len(resposta) > 25:
                return limpar_resposta_inteligente(resposta, contexto)
        
        return None
        
    except Exception as e:
        print(f"Erro Ollama: {e}")
        return None

# Limpeza inteligente
def limpar_resposta_inteligente(resposta, contexto):
    # Remove prefixos comuns
    prefixos_remover = [
        "RESPOSTA:", "Resposta:", "Como DeluxAI", "RESPOSTA detalhada:",
        "DeluxAI:", "Resposta detalhada", "Você é DeluxAI"
    ]
    
    for prefixo in prefixos_remover:
        if resposta.startswith(prefixo):
            resposta = resposta[len(prefixo):].strip()
    
    # Remove repetições excessivas
    resposta = re.sub(r'\n{3,}', '\n\n', resposta)
    resposta = re.sub(r' {2,}', ' ', resposta)
    
    # Remove frases que repetem muito baseadas nas conversas analisadas
    frases_repetitivas = [
        "Te explico tudo sobre o Delux Modpack v Beta 1.0:",
        "Sou o DeluxAI, criado pelo Natan Borges!",
        "Especialista EXCLUSIVO no Delux Modpack"
    ]
    
    for frase in frases_repetitivas:
        resposta = resposta.replace(frase, "")
    
    # Limita tamanho baseado no tipo
    limite = 900 if contexto["tipo_pergunta"] == "tutorial" else 700
    if len(resposta) > limite:
        corte = resposta[:limite]
        ultimo_ponto = corte.rfind('.')
        if ultimo_ponto > limite * 0.7:
            resposta = resposta[:ultimo_ponto + 1]
    
    # Adiciona personalidade baseada no contexto
    if not any(s in resposta.lower()[:30] for s in ["fala", "e aí", "opa", "salve", "eae"]):
        if contexto["tom"] == "positivo":
            saudacao = random.choice(["Valeu! 💪", "Eae! 🔥", "Opa! 👋"])
        elif contexto["urgencia"] == "alta":
            saudacao = random.choice(["Calma! 🛠️", "Vamos resolver! 🔧", "Bora arrumar! ⚡"])
        else:
            saudacao = random.choice(SAUDACOES)
        resposta = f"{saudacao} {resposta}"
    
    # Adiciona despedida contextual
    if not any(d in resposta.lower()[-40:] for d in ["tmj", "falou", "bom", "abraço"]):
        if contexto["tipo_pergunta"] == "tutorial":
            despedida = random.choice(["Bom jogo! 🎮", "Partiu RP! 🔥", "Sucesso! 🚀"])
        elif contexto["urgencia"] == "alta":
            despedida = random.choice(["Qualquer coisa, grita! 📢", "Se não resolver, me chama! 🔧"])
        else:
            despedida = random.choice(DESPEDIDAS)
        
        if not resposta.endswith(('.', '!', '?')):
            resposta += '.'
        resposta += f" {despedida}"
    
    return resposta.strip()

# Detecta perguntas sobre o modpack
def eh_pergunta_delux_melhorada(pergunta):
    p = pergunta.lower()
    
    # Saudações e respostas curtas sempre aceitas
    if len(pergunta) < 25 and any(s in p for s in ["oi", "ola", "eai", "fala", "salve", "hey", "tchau"]):
        return True
    
    # Críticas ou elogios sempre aceitos
    if any(palavra in p for palavra in ["obrigado", "valeu", "top", "legal", "ruim", "chato", "repetindo"]):
        return True
    
    # Sobre criador sempre aceito
    if any(palavra in p for palavra in ["criador", "natan", "quem", "desenvolveu", "borges"]):
        return True
    
    # Keywords específicas do modpack
    keywords_delux = [
        "delux", "gta", "mod", "modpack", "instalar", "instalacao", "download", "baixar",
        "erro", "crash", "problema", "config", "configuracao", "fps", "performance", 
        "requisitos", "specs", "como", "tutorial", "ajuda", "suporte", "jogar",
        "fome", "sede", "trabalho", "casa", "carro", "mapa", "realista", "rp",
        "reshade", "visual", "brasileiro", "funciona", "compativel", "vale", "pena",
        "launcher", "steam", "epic", "rockstar", "script", "hook", "openiv"
    ]
    
    return any(keyword in p for keyword in keywords_delux)

# Resposta padrão mais inteligente
def gerar_resposta_contextual(pergunta):
    p = pergunta.lower()
    contexto = analisar_contexto_conversa(pergunta)
    
    # Respostas específicas baseadas no contexto
    if "repetindo" in p or "mesma coisa" in p:
        return "Opa! 😅 Verdade, estava repetindo mesmo! Vou melhorar isso. No que posso te ajudar especificamente sobre o Delux Modpack? Instalação, problemas, gameplay ou configuração? Bora direto ao ponto! 🎯"
    
    if contexto["tipo_pergunta"] == "tutorial":
        return "Salve! 🔧 Precisa de tutorial sobre o que exatamente? Instalação completa, configuração, como jogar, ou resolver algum problema específico? Fala aí que te ajudo passo a passo!"
    
    elif contexto["tipo_pergunta"] == "suporte" or contexto["urgencia"] == "alta":
        return "E aí! 🛠️ Problema técnico? Me conta: qual o erro exato, specs do seu PC e o que já tentou fazer. Vamos resolver isso juntos!"
    
    elif contexto["tipo_pergunta"] == "compatibilidade":
        return "Fala! 💻 Quer saber se roda no seu PC? Me conta as specs: placa de vídeo, RAM, processador e qual launcher usa (Steam/Epic/Rockstar). Te dou o veredito!"
    
    elif "download" in p or "baixar" in p:
        return "Opa! 📥 Downloads apenas no site oficial: deluxgtav.netlify.app - São 3 partes no MediaFire. NUNCA baixe de outros lugares! Precisa de mais detalhes do processo?"
    
    else:
        return f"Salve! 🎮 Sou o DeluxAI, especialista no Delux Modpack v Beta 1.0 criado pelo Natan Borges. Posso ajudar com instalação, problemas, configurações, gameplay e muito mais. No que você tá precisando? 🤝"

# Gerador principal melhorado
def gerar_resposta_melhorada(pergunta):
    # Cache melhorado
    pergunta_normalizada = re.sub(r'\s+', ' ', pergunta.strip().lower())
    pergunta_hash = hashlib.md5(pergunta_normalizada.encode()).hexdigest()
    
    if pergunta_hash in CACHE_RESPOSTAS:
        return CACHE_RESPOSTAS[pergunta_hash]
    
    # Saudações personalizadas
    if len(pergunta) < 20 and any(s in pergunta.lower() for s in ["oi", "ola", "eai", "fala", "salve"]):
        saudacao = random.choice(SAUDACOES)
        resposta = f"{saudacao} Beleza aí? Sou o DeluxAI, criado pelo Natan Borges! Especialista no Delux Modpack v Beta 1.0 - modpack brasileiro que transforma GTA V num RP realista. Como posso te ajudar hoje? 🤝"
        CACHE_RESPOSTAS[pergunta_hash] = resposta
        return resposta
    
    # Busca inteligente na base local
    resposta_local = buscar_resposta_inteligente(pergunta)
    if resposta_local:
        CACHE_RESPOSTAS[pergunta_hash] = resposta_local
        return resposta_local
    
    # Ollama para respostas personalizadas
    resposta_ollama = processar_ollama_inteligente(pergunta)
    if resposta_ollama:
        CACHE_RESPOSTAS[pergunta_hash] = resposta_ollama
        return resposta_ollama
    
    # Resposta contextual inteligente
    resposta_contextual = gerar_resposta_contextual(pergunta)
    CACHE_RESPOSTAS[pergunta_hash] = resposta_contextual
    return resposta_contextual

# Sistema de histórico
def adicionar_historico(pergunta, resposta):
    timestamp = datetime.now().isoformat()
    HISTORICO_CONVERSAS.append({
        "timestamp": timestamp,
        "pergunta": pergunta[:100],  # Limita para privacidade
        "resposta_tipo": "local" if len(resposta) > 300 else "contextual",
        "tamanho_resposta": len(resposta)
    })
    
    # Limita histórico para evitar uso excessivo de memória
    if len(HISTORICO_CONVERSAS) > 100:
        HISTORICO_CONVERSAS.pop(0)

# ROTAS DA API MELHORADAS

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online_melhorado",
        "sistema": "DeluxAI INTELIGENTE v2.0 - Criado por Natan Borges",
        "especialidade": "Delux Modpack v Beta 1.0",
        "modelo": OLLAMA_MODEL,
        "ollama_ativo": verificar_ollama(),
        "cache_size": len(CACHE_RESPOSTAS),
        "base_conhecimento": len(KNOWLEDGE_BASE),
        "historico_conversas": len(HISTORICO_CONVERSAS),
        "auto_ping": "ativo_5min",
        "melhorias": [
            "Sistemas fome/sede/trabalhos/casas detalhados",
            "Respostas contextuais inteligentes", 
            "Anti-repetição avançado",
            "Suporte técnico especializado",
            "Análise compatibilidade por hardware",
            "Personalidade brasileira natural"
        ],
        "recursos_completos": [
            "Instalação passo-a-passo", "Downloads oficiais seguros", 
            "Solução problemas técnicos", "Otimização por hardware",
            "Gameplay RP completo", "Contato direto Natan Borges",
            "Compatibilidade launchers", "Requisitos detalhados"
        ]
    })

@app.route('/chat', methods=['POST'])
def chat_melhorado():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida"}), 400
        
        pergunta = data['message'].strip()
        if not pergunta:
            return jsonify({"error": "Mensagem vazia"}), 400
        
        # Log melhorado
        print(f"💬 [{datetime.now().strftime('%H:%M:%S')}] Pergunta: {pergunta[:60]}...")
        
        # Filtro inteligente
        if not eh_pergunta_delux_melhorada(pergunta):
            resposta_filtro = f"Opa! 🎮 Sou especialista no Delux Modpack v Beta 1.0 criado pelo Natan Borges. Posso ajudar com instalação, problemas técnicos, configurações, requisitos, gameplay RP e muito mais. Site oficial: deluxgtav.netlify.app - Pergunta algo específico sobre o modpack! 🤝"
            return jsonify({
                "response": resposta_filtro,
                "metadata": {
                    "fonte": "filtro_inteligente_v2",
                    "tipo": "redirecionamento",
                    "especialidade": "delux_modpack_brasileiro"
                }
            })
        
        # Gera resposta melhorada
        resposta = gerar_resposta_melhorada(pergunta)
        
        # Adiciona ao histórico
        adicionar_historico(pergunta, resposta)
        
        # Determina fonte inteligente
        if any(keyword in pergunta.lower() for keyword in ["fome", "sede", "trabalho", "casa"]):
            fonte = "base_sistemas_rp"
        elif any(keyword in pergunta.lower() for keyword in ["instalar", "download", "erro"]):
            fonte = "base_tecnica_detalhada"
        elif verificar_ollama() and len(resposta) > 400:
            fonte = "ollama_contextual"
        else:
            fonte = "inteligencia_contextual"
        
        return jsonify({
            "response": resposta,
            "metadata": {
                "fonte": fonte,
                "modelo": OLLAMA_MODEL,
                "cache_size": len(CACHE_RESPOSTAS),
                "sistema": "DeluxAI_Inteligente_v2",
                "melhorias": "anti_repeticao_ativa"
            }
        })
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({
            "response": "Opa! 😅 Deu um probleminha técnico aqui. Tenta de novo ou me pergunta algo específico sobre o Delux Modpack! 🔧",
            "error": "erro_interno_recuperavel"
        }), 500

@app.route('/sistemas-rp', methods=['GET'])
def sistemas_rp():
    return jsonify({
        "titulo": "Sistemas RP - Delux Modpack v Beta 1.0",
        "criador": "Natan Borges",
        "sistemas_incluidos": {
            "fome_sede": {
                "descricao": "Sistema realista de necessidades básicas",
                "como_funciona": "Barras diminuem gradualmente, precisa comer/beber",
                "locais": "Restaurantes, lojas 24/7, vending machines",
                "controles": "TAB para ver status, E para interagir"
            },
            "trabalhos": {
                "descricao": "Vários empregos realistas disponíveis", 
                "tipos": "Caminhoneiro, taxista, paramédico, segurança, comerciante",
                "como_conseguir": "Menu F6, vá ao local, aceite vaga",
                "economia": "Salário por tarefa, promoções, horários"
            },
            "casas": {
                "descricao": "Sistema completo de propriedades",
                "tipos": "Casas, apartamentos, mansões por diferentes preços",
                "beneficios": "Descanso, cozinha, garagem, spawn personalizado",
                "custos": "Compra, IPTU mensal, manutenção"
            },
            "economia_realista": {
                "descricao": "Dinheiro tem valor real no jogo",
                "caracteristicas": "Preços brasileiros, gastos realistas, investimentos"
            }
        },
        "diferenciais": [
            "RP completo no singleplayer",
            "Mecânicas brasileiras realistas", 
            "Progressão de carreira",
            "Vida virtual completa"
        ]
    })

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "sistema": "DeluxAI Auto-Ping Ativo",
        "uptime": "servidor_ativo"
    })

if __name__ == '__main__':
    print("🎮 Iniciando DeluxAI INTELIGENTE v2.0")
    print("=" * 70)
    print("👨‍💻 Criado por: Natan Borges")  
    print("📧 Contato: borgesnatan09@gmail.com")
    print("📱 WhatsApp: +55 21 99282-6074")
    print("🌐 Site oficial: deluxgtav.netlify.app")
    print("=" * 70)
    
    # Carrega base melhorada
    carregar_conhecimento_avancado()
    
    # Status Ollama
    if verificar_ollama():
        print("✅ Ollama + Gemma3:1b - CONECTADO")
        print("🧠 Modo: Inteligência Híbrida (Local + IA)")
    else:
        print("⚠️ Ollama offline - Modo Base Inteligente")
        print("🧠 Modo: Inteligência Local Avançada")
    
    print(f"💾 Base conhecimento: {len(KNOWLEDGE_BASE)} entradas especializadas")
    print("🔄 Auto-ping: Ativo (5 minutos)")
    print("🚀 Melhorias: Anti-repetição, Contexto, Sistemas RP")
    print("🌐 Servidor na porta 5001...")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )