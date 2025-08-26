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

# Cache e dados
CACHE_RESPOSTAS = {}
KNOWLEDGE_BASE = {}
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

# Personalidade 
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
    """Analisa a intenção com MUITO mais variações e precisão"""
    p = pergunta.lower().strip()
    
    intencoes = {
        "instalacao": 0,
        "gameplay": 0,
        "problema": 0,
        "download": 0,
        "download_links": 0,
        "requisitos": 0,
        "contato": 0,
        "desenvolvedor": 0,
        "saudacao": 0,
        "despedida": 0,
        "elogio": 0,
        "opiniao": 0,
        "funcionamento": 0,
        "configuracao": 0,
        "doacao": 0,
        "geral": 0
    }
    
    # PALAVRAS-CHAVE MEGA EXPANDIDAS
    
    # Instalação - todas variações possíveis
    palavras_instalacao = [
        "instala", "instalacao", "instalar", "install", "como instalar", "instalando",
        "passo a passo", "tutorial instalacao", "instalo", "como instalo",
        "extrair", "executar", "administrador", "pasta do gta", "script hook",
        "openiv", "visual c++", "net framework", "pre requisitos", "como por"
    ]
    
    # Funcionamento - MEGA variações
    palavras_funcionamento = [
        "como funciona", "funciona", "funcionamento", "como que funciona",
        "como o modpack funciona", "como esse mod funciona", "explicar funcionamento",
        "funciona mesmo", "isso funciona", "funciona mrm", "esse modpack funciona",
        "modpack funciona", "ta funcionando", "funciona de verdade", "realmente funciona"
    ]
    
    # Gameplay 
    palavras_gameplay = [
        "jogar", "jogo", "como joga", "gameplay", "controles", "como usar",
        "trabalho", "emprego", "casa", "propriedade", "sistemas", "hud",
        "rp", "roleplay", "realista", "mecanicas", "funcionalidades", "como fica",
        "vida", "colete", "dinheiro", "melhorado"
    ]
    
    # Download Links - NOVO
    palavras_download_links = [
        "link", "links", "mediafire", "me manda", "manda o link", "link das partes",
        "link das 3 partes", "link do mediafire", "manda link", "passa o link",
        "cadê o link", "onde ta o link", "link pra baixar", "link download"
    ]
    
    # Download geral
    palavras_download = [
        "baixar", "download", "onde baixar", "partes", "arquivos", 
        "site oficial", "gratuito", "free", "baixa"
    ]
    
    # Opinião - MEGA variações  
    palavras_opiniao = [
        "vale pena", "é bom", "recomenda", "opiniao", "review", "como fica",
        "mt bom", "muito bom", "modpack é bom", "esse modpack é bom",
        "bom mesmo", "é bom mesmo", "modpack bom", "vale a pena",
        "recomenda mesmo", "ta bom", "ficou bom", "qualidade"
    ]
    
    # Desenvolvedor - TODAS variações do Natan
    palavras_desenvolvedor = [
        "natan", "borges", "desenvolvedor", "criador", "quem fez", "autor",
        "programador", "ntzinnn", "portfolio", "quem é", "dono", "quem é natan",
        "quem criou", "quem desenvolveu", "quem programou", "natan borges",
        "criador do modpack", "quem fez isso", "quem fez esse mod"
    ]
    
    # Doação - NOVO
    palavras_doacao = [
        "doacão", "doacao", "doar", "pix", "doação", "apoiar", "contribuir",
        "ajudar financeiramente", "mandar dinheiro", "como apoiar",
        "pagar", "contribuição", "suporte financeiro"
    ]
    
    # Configuração
    palavras_configuracao = [
        "configurar", "configuracao", "configuracoes", "deixar bom", "config",
        "melhor configuracao", "como configurar", "ajustar", "otimizar"
    ]
    
    # Problema
    palavras_problema = [
        "erro", "crash", "crashando", "problema", "nao funciona", "travando",
        "bugou", "nao abre", "nao roda", "fps baixo", "lag", "bug", "reportar"
    ]
    
    # Requisitos
    palavras_requisitos = [
        "requisitos", "specs", "meu pc", "roda", "compativel", "gtx", "ram",
        "processador", "pc fraco", "pc bom", "precisa de pc", "sistema", "windows"
    ]
    
    # Contato
    palavras_contato = [
        "contato", "falar", "whatsapp", "email", "instagram", "discord", "suporte", "ajuda"
    ]
    
    # Saudação
    palavras_saudacao = [
        "oi", "ola", "hey", "eai", "fala", "salve", "bom dia", "boa tarde",
        "boa noite", "tudo bem", "beleza", "como vai"
    ]
    
    # Despedida
    palavras_despedida = [
        "tchau", "bye", "flw", "falou", "ate mais", "ate logo", "nos vemos",
        "obrigado", "vlw", "valeu", "brigado", "foi bom falar"
    ]
    
    # Elogio
    palavras_elogio = [
        "legal", "top", "show", "incrivel", "otimo", "excelente", "perfeito",
        "massa", "da hora", "maneiro", "bacana", "gostei", "curti", "parabens", "fantastico"
    ]
    
    # CONTAGEM COM PESOS AJUSTADOS
    for palavra in palavras_funcionamento:
        if palavra in p:
            intencoes["funcionamento"] += 5
    
    for palavra in palavras_download_links:
        if palavra in p:
            intencoes["download_links"] += 5
    
    for palavra in palavras_opiniao:
        if palavra in p:
            intencoes["opiniao"] += 4
    
    for palavra in palavras_desenvolvedor:
        if palavra in p:
            intencoes["desenvolvedor"] += 5
    
    for palavra in palavras_doacao:
        if palavra in p:
            intencoes["doacao"] += 5
    
    for palavra in palavras_instalacao:
        if palavra in p:
            intencoes["instalacao"] += 3
    
    for palavra in palavras_configuracao:
        if palavra in p:
            intencoes["configuracao"] += 3
    
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
            intencoes["requisitos"] += 3
    
    for palavra in palavras_contato:
        if palavra in p:
            intencoes["contato"] += 2
    
    for palavra in palavras_saudacao:
        if palavra in p:
            intencoes["saudacao"] += 4
    
    for palavra in palavras_despedida:
        if palavra in p:
            intencoes["despedida"] += 4
    
    for palavra in palavras_elogio:
        if palavra in p:
            intencoes["elogio"] += 3
    
    # Retorna a intenção com maior score
    intencao_principal = max(intencoes, key=intencoes.get)
    score_principal = intencoes[intencao_principal]
    
    return intencao_principal if score_principal > 1 else "geral"

# Base de conhecimento CORRIGIDA E EXPANDIDA
def carregar_conhecimento_especializado():
    global KNOWLEDGE_BASE
    
    KNOWLEDGE_BASE = {
        "funcionamento": {
            "resposta": """Opa! 👋 **COMO FUNCIONA O DELUX MODPACK v Beta 1.0:**

**🎮 CONCEITO PRINCIPAL:**
O Delux Modpack transforma o **GTA V singleplayer** numa experiência de **roleplay realista completa**, simulando a vida real dentro do jogo!

**🔧 COMO FUNCIONA:**
- **Substitui scripts** originais por sistemas realistas
- **Adiciona mecânicas** de sobrevivência e economia
- **Implementa economia** realista com trabalhos
- **Modifica física** dos veículos para realismo
- **Inclui mapas brasileiros** e sons nacionais
- **Melhora HUD** com vida, colete e dinheiro aprimorados

**⚙️ SISTEMAS PRINCIPAIS:**

**💼 ECONOMIA REALISTA:**
- Sistema de trabalhos: Taxista, Caminhoneiro, Paramédico
- Salários baseados no desempenho
- Dinheiro necessário para tudo (comida, casa, combustível)

**🏠 PROPRIEDADES:**
- Casas à venda espalhadas por Los Santos
- Sistema de aluguel e compra
- Garagens funcionais e pontos de spawn

**🚗 VEÍCULOS REALISTAS:**
- Sistema de combustível obrigatório
- Danos mais realistas
- Sons brasileiros nos carros
- Física modificada para mais realismo

**🇧🇷 TOQUE BRASILEIRO:**
- Mapas de cidades brasileiras
- Sons de carros nacionais
- Lojas com nomes brasileiros
- Comunidade 100% em português

**📊 HUD MELHORADO:**
- Interface de vida, colete e dinheiro aprimorada
- Indicadores realistas de status
- Visual mais imersivo e funcional

**💻 TECNICAMENTE:**
Usa **Script Hook V** e **OpenIV** para modificar arquivos do GTA V, criando uma experiência totalmente nova mantendo a base do jogo original.

**SIM, FUNCIONA PERFEITAMENTE!** 🔥 É como ter um GTA V completamente novo com foco em RP realista! Tmj! 🤝""",
            "keywords": ["como funciona", "funcionamento", "funciona mesmo", "isso funciona"]
        },
        
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
            "keywords": ["instala", "instalacao", "instalar", "install", "passo", "tutorial"]
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
            "keywords": ["baixar", "download", "onde baixar", "site", "oficial", "gratuito"]
        },
        
        "download_links": {
            "resposta": """Opa! 🔗 **LINKS DIRETOS DAS 3 PARTES:**

**📥 MEDIAFIRE LINKS:**

**PARTE 1:**
https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file

**PARTE 2:**
https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file

**PARTE 3:**
https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file

**🚨 IMPORTANTE:**
- Baixe **TODAS AS 3 PARTES** na mesma pasta
- **NÃO EXTRAIA** separadamente 
- Total: ~20GB
- **100% GRATUITO e SEGURO**

**💾 APÓS BAIXAR:**
1. Todas as 3 partes na mesma pasta
2. Extraia JUNTAS
3. Execute o installer como ADMINISTRADOR
4. Selecione pasta do GTA V
5. Aguarde instalação

**🌐 SITE OFICIAL:** deluxgtav.netlify.app
⚠️ **Só baixe desses links!** Outros = vírus!

**Aí estão os links!** 🔥 Tmj! 🤝""",
            "keywords": ["link", "links", "mediafire", "me manda", "manda o link", "link das partes"]
        },
        
        "gameplay": {
            "resposta": """E aí! 🎮 **COMO JOGAR Delux Modpack v Beta 1.0:**

**🚀 PRIMEIROS PASSOS:**
1. **Abra GTA V** normalmente
2. **Selecione "Story Mode"**
3. **Aguarde carregar** (demora mais agora)
4. **Explore as novidades!**

**⭐ SISTEMAS PRINCIPAIS:**

**📊 HUD MELHORADO:**
- Interface de **vida, colete e dinheiro** aprimorada
- **TAB:** Verificar status detalhado
- Visual mais realista e imersivo
- Indicadores mais precisos

**💼 TRABALHOS:**
- **F6:** Menu de empregos
- Disponíveis: **Taxista, Caminhoneiro, Paramédico**
- Vá ao local indicado no mapa
- Ganhe dinheiro realisticamente

**🏠 CASAS E PROPRIEDADES:**
- Procure placas **"À VENDA"**
- **E:** Ver detalhes da propriedade
- Compre com dinheiro do trabalho
- Benefícios: Spawn, garagem, descanso

**🚗 CARROS REALISTAS:**
- **Sistema de combustível** obrigatório
- Abasteça em postos de gasolina
- **Sons brasileiros** nos veículos
- **Danos mais realistas**
- **Física modificada** para mais realismo

**🎯 CONTROLES ESPECIAIS:**
- **TAB:** Status geral (vida, colete, dinheiro)
- **F6:** Menu de trabalhos
- **E:** Interações gerais
- **M:** Mapa com locais importantes

**🇧🇷 DIFERENCIAIS BRASILEIROS:**
- **Mapas inspirados no Brasil**
- **Sons de carros nacionais**
- **Lojas com nomes brasileiros**
- **Comunidade 100% português**

**💡 DICAS PRO:**
1. **Comece arranjando um emprego** para ter dinheiro
2. **Sempre abasteça** o carro quando precisar
3. **Economize dinheiro** para casa própria
4. **Explore os mapas brasileiros** inclusos
5. **Faça RP realista** sempre!

**É uma experiência de vida virtual completa!** 🇧🇷 Bom RP! 🔥""",
            "keywords": ["jogar", "jogo", "como joga", "gameplay", "controles", "sistemas", "rp"]
        },
        
        "configuracao": {
            "resposta": """Salve! ⚙️ **MELHORES CONFIGURAÇÕES Delux Modpack v Beta 1.0:**

**🎮 CONFIGURAÇÕES DE JOGO RECOMENDADAS:**

**📊 GRÁFICOS (60 FPS estável):**
- **Qualidade de Textura:** Alta/Muito Alta
- **Qualidade dos Shaders:** Alta  
- **Qualidade da Sombra:** Alta
- **Reflexos:** Alta
- **Qualidade da Água:** Muito Alta
- **Partículas:** Alta
- **Grama:** Alta
- **Efeitos Pós-Processamento:** Normal

**⚡ CONFIGURAÇÕES AVANÇADAS:**
- **MSAA:** Desligado (use FXAA)
- **FXAA:** Ligado
- **VSync:** Desligado
- **Densidade Populacional:** 70-80%
- **Densidade de Veículos:** 70-80%
- **Distância de Renderização:** Máximo

**🔧 CONFIGURAÇÕES DO SISTEMA:**
- **Modo Tela Cheia Exclusivo:** Ativado
- **Limite de FPS:** 60 ou 75 (conforme seu monitor)
- **Modo Alto Desempenho:** Windows + NVIDIA/AMD

**💻 OTIMIZAÇÕES PC:**
- **Feche programas** desnecessários
- **Modo Jogador:** Ativado no Windows
- **Atualize drivers** gráficos
- **16GB RAM** recomendado (8GB mínimo)

**🎯 CONFIGURAÇÕES ESPECÍFICAS MODPACK:**
- **ReShade:** Pode deixar ativado (opcional)
- **ENB:** Desative se tiver FPS baixo
- **Distância LOD:** Máximo para melhor visual

**⚠️ SE FPS BAIXAR:**
1. **Diminua MSAA** primeiro
2. **Sombras:** Medium
3. **Reflexos:** Medium  
4. **Densidade populacional:** 50%

**🔥 RESULTADO:**
Com essas configurações você terá:
- **Visual incrível** e realista
- **60 FPS estáveis** na maioria dos PCs
- **Experiência RP imersiva**

**Configuração perfeita = diversão garantida!** 🎮 Tmj! 🤝""",
            "keywords": ["configurar", "configuracao", "deixar bom", "config", "otimizar"]
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

**⚠️ RESPOSTA DIRETA: "PRECISA PC MUITO BOM?"**
**NÃO!** O modpack roda bem em PCs medianos. GTX 1060 + 16GB RAM + i5 já é suficiente para boa experiência!

**PC FRACO? DICAS:**
- Feche outros programas
- Modo Alto Performance
- Limite FPS em 30
- Texturas baixas primeiro

**Seu PC roda? Me fala as specs!** 🎯 Tmj! 🤝""",
            "keywords": ["requisitos", "specs", "meu pc", "roda", "pc bom", "pc fraco"]
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

**📧 EMAIL PRINCIPAL:**
**borgesnatan09@gmail.com**

**📱 WHATSAPP DIRETO:**
**+55 21 99282-6074**
(Clique: wa.me/5521992826074)

**📸 INSTAGRAM:**
**@Ntzinnn87**
Siga para novidades!

**💬 DISCORD:**
Servidor disponível no site

**🐛 REPORTAR BUGS:**
Site: deluxgtav.netlify.app (seção Bugs)

**⏰ HORÁRIO ATENDIMENTO:**
- WhatsApp: 9h às 22h
- Email: 24-48h resposta

**Entre em contato sem medo! Natan sempre ajuda!** 🤝""",
            "keywords": ["contato", "falar", "whatsapp", "email", "instagram", "suporte"]
        },
        
        "desenvolvedor": {
            "resposta": """E aí! 👨‍💻 **SOBRE NATAN BORGES:**

**🔥 QUEM É NATAN BORGES:**
- **Desenvolvedor Independente Brasileiro**
- **Criador do Delux Modpack v Beta 1.0**
- **Especialista em Modding GTA V**
- **Apaixonado por RP e simulação realista**

**🎮 HISTÓRIA:**
Natan sempre foi fã de GTA V e roleplay. Vendo a falta de um modpack brasileiro completo para singleplayer, decidiu criar o **Delux Modpack** - um projeto que transforma GTA V numa experiência de vida real.

**💼 TRABALHO:**
- **Programação:** Desenvolvedor autodidata
- **Foco:** Experiências realistas e imersivas  
- **Missão:** Trazer RP de qualidade para comunidade brasileira
- **Filosofia:** Sempre gratuito e com suporte direto

**🌟 CARACTERÍSTICAS:**
- **Comunicativo:** Sempre responde a comunidade
- **Dedicado:** Trabalha constantemente no modpack
- **Brasileiro:** Foca no público nacional
- **Generoso:** Tudo gratuito, sem monetização

**📱 CONTATOS:**
- **Instagram:** @Ntzinnn87
- **Email:** borgesnatan09@gmail.com  
- **WhatsApp:** +55 21 99282-6074
- **Portfólio:** meuportfolio02.netlify.app

**🚀 VISÃO:**
Natan quer fazer do Delux Modpack o **melhor modpack de RP brasileiro**, sempre melhorando com atualizações e ouvindo a comunidade.

**Um cara que faz a diferença na comunidade brasileira de GTA V!** 🇧🇷 Tmj! 🔥""",
            "keywords": ["natan", "borges", "desenvolvedor", "criador", "quem é", "dono", "autor"]
        },
        
        "doacao": {
            "resposta": """Opa! 💰 **SOBRE DOAÇÕES PRO NATAN BORGES:**

**🎁 O MODPACK É GRATUITO:**
O **Delux Modpack v Beta 1.0** é e sempre será **100% GRATUITO!** Natan faz questão de não cobrar nada da comunidade.

**❤️ QUER APOIAR MESMO ASSIM?**
Se você quiser **apoiar o trabalho** do Natan e ajudar no desenvolvimento:

**📱 CONTATO DIRETO:**
- **WhatsApp:** +55 21 99282-6074
- **Email:** borgesnatan09@gmail.com
- **Instagram:** @Ntzinnn87

**💬 FALE COM ELE:**
Entre em contato diretamente pelo WhatsApp ou Instagram para perguntar sobre formas de apoio. Ele sempre responde!

**🔥 MELHOR APOIO:**
- **Divulgar** o modpack para amigos
- **Seguir** no Instagram @Ntzinnn87
- **Reportar bugs** no site deluxgtav.netlify.app
- **Dar feedback** construtivo

**🌟 FILOSOFIA DO NATAN:**
"Faço isso por amor à comunidade brasileira de GTA V. O importante é todo mundo poder jogar!"

**Entre em contato com ele pra saber mais!** 🤝 Tmj! 🔥""",
            "keywords": ["doacao", "doar", "pix", "apoiar", "contribuir", "pagar"]
        },
        
        "opiniao": {
            "resposta": """Opa! 🔥 **MINHA OPINIÃO SINCERA SOBRE O DELUX MODPACK:**

**🌟 É SENSACIONAL, CARA!**

O **Delux Modpack v Beta 1.0** é simplesmente **o melhor modpack brasileiro** de RP para GTA V! 

**✅ PONTOS FORTES:**
- **100% Gratuito** - Zero cobrança, tudo liberado
- **RP Realista Completo** - Trabalhos, economia, propriedades
- **Instalação Simples** - Tutorial detalhado incluído  
- **Comunidade BR** - Feito por brasileiro para brasileiros
- **Suporte Ativo** - Natan sempre disponível
- **Qualidade Profissional** - Parece modpack pago
- **HUD Melhorado** - Interface vida/colete/dinheiro top

**🎮 EXPERIÊNCIA:**
Transforma **GTA V singleplayer** numa **vida virtual completa**! Você:
- Trabalha de verdade (Taxista/Caminhoneiro/Paramédico)
- Compra casa própria com dinheiro ganho
- Usa sistema de combustível realista
- Vive roleplay 24/7 sem precisar de servidor
- Aproveita mapas e sons brasileiros

**🇧🇷 DIFERENCIAL BRASILEIRO:**
- Sons brasileiros nos carros
- Mapas inspirados no Brasil
- Comunidade falando português
- Suporte em português sempre

**💯 VALE A PENA?**
**SIM, DEMAIS!** É **obrigatório** para quem curte:
- GTA V singleplayer
- Roleplay realista
- Simulação de vida real
- Comunidade brasileira

**🔥 NOTA: 10/10**
Qualidade de modpack pago, **totalmente gratuito**. Natan fez um trabalho excepcional!

**FUNCIONA PERFEITAMENTE e é BOM DEMAIS!** 🚀 Recomendo para TODOS! 🎯""",
            "keywords": ["vale pena", "é bom", "opiniao", "como fica", "mt bom", "modpack bom", "bom mesmo"]
        },
        
        "saudacao": {
            "resposta": """Salve! 🔥 

**Beleza aí? Sou o DeluxAI, criado pelo Natan Borges!**

Especialista no **Delux Modpack v Beta 1.0** - o modpack brasileiro que transforma GTA V num **RP realista completo!**

**🎮 Posso te ajudar com:**
📖 **Instalação** passo a passo completo
📥 **Downloads** oficiais seguros + links diretos
🛠️ **Problemas** técnicos e bugs
💻 **Requisitos** do sistema
🎯 **Gameplay** e sistemas RP
⚙️ **Configurações** e otimização
🔧 **Como funciona** o modpack
📞 **Contato** direto com Natan Borges
💰 **Informações sobre doações**
🌟 **Opinião** sobre o modpack
🐛 **Reportar bugs** no site

**🌐 Site oficial:** deluxgtav.netlify.app

**No que posso ajudar hoje?** 🤝""",
            "keywords": ["oi", "ola", "eai", "fala", "salve", "hey", "bom dia", "tudo bem"]
        },
        
        "despedida": {
            "resposta": random.choice(DESPEDIDAS),
            "keywords": ["tchau", "bye", "flw", "falou", "ate mais", "obrigado", "vlw", "valeu", "foi bom"]
        },
        
        "elogio": {
            "resposta": random.choice(ELOGIOS_RESPOSTAS),
            "keywords": ["legal", "top", "show", "incrivel", "massa", "da hora", "bom", "gostei"]
        }
    }
    
    print(f"✅ Base SUPER MELHORADA carregada: {len(KNOWLEDGE_BASE)} categorias")

# Busca resposta especializada MELHORADA
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

# Processamento Ollama MELHORADO
def processar_ollama_focado(pergunta, intencao):
    if not verificar_ollama():
        return None
    
    try:
        # Prompts específicos SUPER MELHORADOS
        prompts = {
            "funcionamento": "Explique detalhadamente como funciona o Delux Modpack, confirmando que SIM funciona perfeitamente:",
            "instalacao": "Explique detalhadamente como instalar o Delux Modpack passo a passo:",
            "gameplay": "Ensine como jogar e usar todos os sistemas do Delux Modpack (sem fome/sede):",
            "configuracao": "Explique as melhores configurações para o Delux Modpack:",
            "problema": "Resolva este problema técnico do Delux Modpack:",
            "download": "Explique como baixar o Delux Modpack com segurança:",
            "download_links": "Forneça os links diretos das 3 partes do MediaFire:",
            "requisitos": "Analise os requisitos de sistema do Delux Modpack (confirme que NÃO precisa PC muito bom):",
            "contato": "Forneça informações de contato do desenvolvedor Natan Borges:",
            "desenvolvedor": "Fale sobre Natan Borges, desenvolvedor do Delux Modpack:",
            "doacao": "Explique sobre doações e apoio ao Natan Borges:",
            "opiniao": "Confirme que o modpack é BOM e FUNCIONA PERFEITAMENTE:",
            "saudacao": "Responda educadamente e apresente o DeluxAI:",
            "despedida": "Responda educadamente à despedida:",
            "elogio": "Responda positivamente ao elogio sobre o modpack:",
            "geral": "Responda sobre o Delux Modpack:"
        }
        
        prompt_base = prompts.get(intencao, prompts["geral"])
        
        # Informações CORRIGIDAS dos MODS (SEM fome/sede)
        mods_info = """
MODS INCLUSOS NO DELUX MODPACK (CORRETO):
- 01_Hud_Melhorado: Interface de vida/colete/dinheiro melhorada
- 03_Dinheiro_Banco: Sistema bancário realista
- 05_Empregos_Dinamicos: Sistema de trabalhos (Taxista/Caminhoneiro/Paramédico)
- 06_Casas: Sistema de propriedades e imóveis
- 07_Inventario_De_Armas: Inventário de armas realista
- 08_Veiculos_Realistas: Carros com física real e combustível
- 09_Policia_Avancada: IA policial melhorada
- 10_Gangue: Sistema de gangues
- 11_TransportePublico: Ônibus e transporte público
- 12_Clima: Sistema climático realista
- 15_Reshade: Melhorias visuais
- 16_Tempo_Real: Tempo sincronizado
- 18_IA_Realista_De_Pedestres: NPCs mais inteligentes
- 19_Sistema_De_Ferimento: Danos mais realistas
- 21_Sistema_De_CNH: Carteira de motorista
- 22_Sistema_De_CPF_RG: Documentos brasileiros
- 23_Sistema_De_Prisao: Sistema carcerário
- 24_Venda_De_Drogas: Economia ilegal
- 27_Roubo_Ao_Banco: Assaltos realistas
- 29_Concessionarias: Lojas de carros
- 30_Sistema_De_Assalto: Crimes diversos
- 31_Salvar_Veiculos: Garagem persistente
- 32_Street_Races: Corridas de rua

IMPORTANTE: NÃO TEM SISTEMA DE FOME/SEDE no modpack!
"""
        
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

LINKS DIRETOS MEDIAFIRE:
Part1: https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file
Part2: https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file  
Part3: https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file

{mods_info}

CORREÇÕES IMPORTANTES PARA RESPOSTAS:
1. "Como funciona/Funciona mesmo": SIM! Funciona perfeitamente! Explicar sistemas RP, economia, trabalhos
2. "Precisa PC bom": NÃO! Roda em PCs medianos, GTX 1060+ é suficiente
3. "Quem é Natan": Desenvolvedor brasileiro independente, criador do modpack, programador autodidata
4. "É gratuito": SIM! 100% gratuito sempre
5. "Como fica/É bom": SIM! É BOM DEMAIS! Transformação completa em RP realista, experiência incrível
6. "Links": Fornecer links diretos do MediaFire quando pedido
7. "Doação": Modpack é gratuito, mas pode entrar em contato com Natan para apoiar
8. "Configurações": Dar dicas específicas de gráficos e otimização
9. "Vale a pena": SIM! Melhor modpack RP brasileiro

IMPORTANTE: NUNCA mencionar fome/sede - NÃO EXISTE no modpack!
SEMPRE responda TUDO que souber sobre o assunto perguntado. Seja completo e detalhado.

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

# Limpeza focada MANTIDA
def limpar_resposta_focada(resposta):
    # Remove prefixos desnecessários
    prefixos = [
        "Resposta completa e detalhada:", "DeluxAI:", "Como DeluxAI",
        "RESPOSTA:", "Resposta:", "FOCO:", "Olá!", "Oi!", "E aí!",
        "Fala aí!", "Salve!", "Opa!"
    ]
    
    for prefixo in prefixos:
        if resposta.startswith(prefixo):
            resposta = resposta[len(prefixo):].strip()
    
    # Limita tamanho mas mantém informação importante
    if len(resposta) > 1200:
        corte = resposta[:1200]
        ultimo_ponto = corte.rfind('.')
        if ultimo_ponto > 1000:
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

# Verificação SUPER MELHORADA - aceita MUITO mais variações
def eh_pergunta_delux_focada(pergunta):
    p = pergunta.lower().strip()
    
    # SEMPRE aceita saudações, despedidas e elogios (mais amplo)
    if len(pergunta) < 50:
        # Saudações
        if any(s in p for s in ["oi", "ola", "eai", "e ai", "fala", "salve", "hey", "bom dia", "boa tarde", "boa noite", "tudo bem", "beleza", "como vai", "opa", "ae"]):
            return True
        # Despedidas  
        if any(d in p for d in ["tchau", "bye", "flw", "falou", "ate", "obrigado", "vlw", "valeu", "foi bom", "brigado", "tmj"]):
            return True
        # Elogios simples
        if any(e in p for e in ["legal", "top", "show", "massa", "bom", "boa", "otimo", "incrivel", "mt bom", "muito bom", "da hora", "maneiro", "bacana"]):
            return True
    
    # Keywords MEGA AMPLAS - aceita quase TUDO relacionado
    keywords_aceitas = [
        # Sobre o modpack - MAIS VARIAÇÕES
        "delux", "modpack", "mod", "gta", "v", "beta", "1.0", "esse modpack", "isso",
        
        # Ações técnicas - EXPANDIDO
        "instalar", "instalacao", "install", "baixar", "download", "rodar", "executar",
        "funciona", "funcionamento", "como funciona", "funciona mesmo", "isso funciona", "funciona mrm",
        
        # Problemas - MAIS OPÇÕES
        "erro", "crash", "problema", "bug", "nao funciona", "travando", "fps", "lag", "bugou",
        
        # Sistema - EXPANDIDO
        "requisitos", "pc", "placa", "ram", "processador", "windows", "specs", "configurar", "roda",
        "pc bom", "pc fraco", "precisa pc", "meu pc",
        
        # Gameplay - MAIS VARIAÇÕES
        "jogar", "jogo", "gameplay", "como", "usar", "sistemas", "controles", "como joga",
        "trabalho", "casa", "propriedade", "rp", "roleplay", "hud", "vida", "colete", "dinheiro",
        
        # Pessoas e contato - EXPANDIDO
        "natan", "borges", "desenvolvedor", "criador", "contato", "whatsapp", "quem", "quem é",
        "email", "instagram", "suporte", "ajuda", "dono", "quem fez", "quem criou",
        
        # Downloads - MAIS OPÇÕES
        "site", "oficial", "mediafire", "link", "gratuito", "free", "seguro", "links",
        "me manda", "manda o link", "link das partes", "parte", "partes",
        
        # Opiniões - MEGA EXPANDIDO
        "opiniao", "vale", "pena", "recomenda", "bom", "ruim", "review", "como fica",
        "é bom", "bom mesmo", "mt bom", "muito bom", "modpack é bom", "esse modpack é bom",
        "ta bom", "ficou bom", "qualidade", "vale a pena", "recomenda mesmo",
        
        # Doação - NOVO
        "doacao", "doar", "pix", "apoiar", "contribuir", "pagar", "dinheiro", "ajudar",
        
        # Palavras gerais - MAIS AMPLAS
        "como", "onde", "quando", "porque", "qual", "quem", "quanto", "melhor", "esse", "isso",
        
        # Confirmações - NOVO
        "mesmo", "mrm", "de verdade", "realmente", "certeza", "confirma"
    ]
    
    # Se tem QUALQUER palavra relacionada, aceita
    if any(keyword in p for keyword in keywords_aceitas):
        return True
    
    # Se tem números relacionados (partes, versão, etc)
    if any(num in p for num in ["1", "2", "3", "parte", "beta", "v1"]):
        return True
        
    return False

# Gerador principal MELHORADO
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
    
    # Resposta de fallback SUPER MELHORADAS
    fallbacks = {
        "funcionamento": "Opa! 🎮 SIM, o Delux Modpack FUNCIONA PERFEITAMENTE! Transforma GTA V singleplayer numa experiência RP realista completa! Sistemas de trabalhos (Taxista/Caminhoneiro/Paramédico), casas para comprar, economia real, HUD melhorado. É como viver uma vida virtual no GTA! Site: deluxgtav.netlify.app 🔥",
        
        "instalacao": "Fala aí! 🎮 Para instalar: 1) Acesse deluxgtav.netlify.app 2) Baixe as 3 partes 3) Extraia juntas 4) Execute como admin. Precisa do GTA V original e Script Hook V! Tutorial completo no site! Tmj! 🤝",
        
        "download": "Salve! 🔥 Baixe APENAS no site oficial: deluxgtav.netlify.app - São 3 partes no MediaFire, totalmente GRATUITO e seguro! Outros sites = vírus garantido! 📥",
        
        "download_links": "Opa! 🔗 LINKS DIRETOS: Part1: https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file | Part2: https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file | Part3: https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file - Baixe todas na mesma pasta! 🔥",
        
        "gameplay": "E aí! 🎮 No Delux você trabalha (F6), gerencia dinheiro/vida/colete no HUD melhorado, compra casas, abastece carros. É RP completo no singleplayer com sistemas brasileiros! Uma vida virtual realista! 🇧🇷",
        
        "configuracao": "Salve! ⚙️ Configurações recomendadas: Texturas Alta, Sombras Alta, FXAA ligado, MSAA desligado, Densidade 70-80%. Com GTX 1060+ roda liso em High! Tmj! 🎯",
        
        "problema": "Opa! 🛠️ Para problemas: 1) Verificar integridade GTA V 2) Reinstalar Script Hook V 3) Executar como admin 4) Reportar bugs no site deluxgtav.netlify.app. Me fala o erro específico! 🔧",
        
        "requisitos": "Fala! 💻 RESPOSTA DIRETA: NÃO precisa PC muito bom! GTX 1060 + 16GB RAM + i5 já roda bem. Mínimo: GTX 1060/RX 580, 8GB RAM, Windows 10/11. Roda na maioria dos PCs! 🎯",
        
        "contato": "E aí! 📞 Contato Natan Borges: borgesnatan09@gmail.com, WhatsApp +55 21 99282-6074, Instagram @Ntzinnn87. Ele sempre responde e ajuda! 🤝",
        
        "desenvolvedor": "Opa! 👨‍💻 Natan Borges é o desenvolvedor brasileiro independente que criou o Delux Modpack. Programador autodidata, apaixonado por RP, sempre ativo na comunidade. Um cara que fez a diferença! 🇧🇷",
        
        "doacao": "Opa! 💰 O modpack é 100% GRATUITO sempre! Quer apoiar? Fale direto com Natan: WhatsApp +55 21 99282-6074 ou Instagram @Ntzinnn87. Melhor apoio é divulgar e dar feedback! 🤝",
        
        "opiniao": "🔥 MINHA OPINIÃO: É SENSACIONAL! SIM, É BOM DEMAIS e FUNCIONA PERFEITAMENTE! Melhor modpack RP brasileiro, 100% gratuito, qualidade profissional. Transforma GTA V numa experiência completa de vida real. RECOMENDO 1000%! Vale muito a pena! 🎯",
        
        "funcionamento": "Opa! 🎮 SIM, o Delux Modpack FUNCIONA PERFEITAMENTE! Transforma GTA V singleplayer numa experiência RP realista completa! Sistemas de trabalhos (Taxista/Caminhoneiro/Paramédico), casas para comprar, economia real, HUD melhorado. É como viver uma vida virtual no GTA! Site: deluxgtav.netlify.app 🔥",
        
        "geral": "Opa! 👋 Sou DeluxAI, especialista no Delux Modpack v Beta 1.0 criado pelo Natan Borges! Modpack brasileiro de RP realista para GTA V. Site: deluxgtav.netlify.app 🎮"
    }
    
    resposta_fallback = fallbacks.get(intencao, fallbacks["geral"])
    
    CACHE_RESPOSTAS[pergunta_hash] = resposta_fallback
    print("⚠️ Resposta fallback contextual melhorada")
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
        "status": "online_super_melhorado",
        "sistema": "DeluxAI SUPER MELHORADO v6.0 - Criado por Natan Borges",
        "especialidade": "Delux Modpack v Beta 1.0",
        "modelo": OLLAMA_MODEL,
        "ollama_ativo": verificar_ollama(),
        "cache_size": len(CACHE_RESPOSTAS),
        "categorias": list(KNOWLEDGE_BASE.keys()) if KNOWLEDGE_BASE else [],
        "melhorias_v6": [
            "Detecção de intenção MEGA expandida com todas variações",
            "Links diretos do MediaFire incluídos",
            "Informações sobre doações adicionadas", 
            "Resposta 'FUNCIONA MESMO': SIM, PERFEITAMENTE!",
            "Resposta 'É BOM MESMO': SIM, É SENSACIONAL!",
            "Variações do 'Quem é Natan' super expandidas",
            "Correção: SEM fome/sede - apenas HUD melhorado",
            "Fallbacks super melhorados por categoria",
            "Filtro aceita muito mais variações de perguntas",
            "Base corrigida com mods reais da imagem"
        ]
    })

@app.route('/chat', methods=['POST'])
def chat_super_melhorado():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida"}), 400
        
        pergunta = data['message'].strip()
        if not pergunta:
            return jsonify({"error": "Mensagem vazia"}), 400
        
        print(f"💬 [{datetime.now().strftime('%H:%M:%S')}] Pergunta: {pergunta}")
        
        # Filtro SUPER MELHORADO - aceita MUITO mais relacionado
        if not eh_pergunta_delux_focada(pergunta):
            resposta_filtro = "Opa! 🎮 Sou o DeluxAI, especialista no Delux Modpack v Beta 1.0 criado pelo Natan Borges. Posso ajudar com TUDO sobre o modpack: como funciona (SIM, funciona perfeitamente!), instalação, downloads + links diretos, problemas, requisitos, gameplay RP, configurações, contatos, doações, opiniões. Site oficial: deluxgtav.netlify.app - Pergunta qualquer coisa! 🤝"
            return jsonify({
                "response": resposta_filtro,
                "metadata": {
                    "fonte": "filtro_super_melhorado", 
                    "tipo": "redirecionamento_completo"
                }
            })
        
        # Gera resposta SUPER MELHORADA
        resposta = gerar_resposta_otimizada(pergunta)
        
        # Determina fonte mais precisa
        intencao = analisar_intencao(pergunta)
        if intencao in KNOWLEDGE_BASE:
            fonte = f"base_super_melhorada_{intencao}"
        elif verificar_ollama():
            fonte = f"ollama_melhorado_{intencao}"
        else:
            fonte = f"fallback_melhorado_{intencao}"
        
        return jsonify({
            "response": resposta,
            "metadata": {
                "fonte": fonte,
                "intencao": intencao,
                "modelo": OLLAMA_MODEL,
                "sistema": "DeluxAI_v6_Super_Melhorado",
                "site_oficial": "deluxgtav.netlify.app",
                "links_diretos_incluidos": True
            }
        })
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({
            "response": "Eae! 😅 Deu um probleminha aqui, mas já volto! Me pergunta sobre como funciona (SIM, funciona perfeitamente!), instalação, downloads + links diretos, gameplay, problemas, contatos, doações ou qualquer coisa do Delux Modpack! Site: deluxgtav.netlify.app 🔧",
            "error": "erro_temporario"
        }), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "sistema": "DeluxAI v6.0 - SUPER MELHORADO - Auto-Ping Ativo"
    })

if __name__ == '__main__':
    print("🎮 Iniciando DeluxAI SUPER MELHORADO v6.0")
    print("=" * 80)
    print("👨‍💻 Criado por: Natan Borges")  
    print("📧 Contato: borgesnatan09@gmail.com")
    print("📱 WhatsApp: +55 21 99282-6074")
    print("📸 Instagram: @Ntzinnn87")
    print("🌐 Site: deluxgtav.netlify.app")
    print("💼 Portfólio: meuportfolio02.netlify.app")
    print("=" * 80)
    
    # Carrega base SUPER MELHORADA
    carregar_conhecimento_especializado()
    
    # Status
    if verificar_ollama():
        print("✅ Ollama CONECTADO - Modo Híbrido Super Melhorado")
    else:
        print("⚠️ Ollama offline - Modo Base Super Melhorada")
    
    print("🔧 SUPER MELHORIAS APLICADAS:")
    print("   - Detecção 'funciona mesmo/isso funciona': SIM, PERFEITAMENTE!")
    print("   - Links diretos MediaFire incluídos nas respostas")
    print("   - 'Quem é Natan' com TODAS variações possíveis")
    print("   - Informações sobre doações adicionadas")
    print("   - 'É bom mesmo/vale a pena': SIM, É SENSACIONAL!")
    print("   - Correção: SEM fome/sede (apenas HUD melhorado)")
    print("   - Filtro aceita muito mais variações de perguntas")
    print("   - Fallbacks contextuais super detalhados")
    print("   - Base com mods corretos da imagem")
    print("   - Análise de intenção mega expandida")
    print("🔄 Auto-ping ativo (5min)")
    print("🚀 Servidor iniciando na porta 5001...")
    print("=" * 80)
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )