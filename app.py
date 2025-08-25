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

# =================== TREINAMENTO EXPANDIDO DELUX MODPACK ===================

DELUX_MODPACK_KNOWLEDGE_BASE_EXPANDIDA = """
=== DELUX MODPACK GTA V - BASE DE CONHECIMENTO COMPLETA EXPANDIDA ===

INFORMAÇÕES BÁSICAS:
- Nome: Delux Modpack GTA V
- Versão: Beta 1.0
- Criador: Natan Borges (@Ntzinnn87)
- Tipo: Modpack de Roleplay Realista para Singleplayer
- Status: GRATUITO e em desenvolvimento ativo
- Foco: Experiência brasileira no GTA V
- Site oficial: deluxgtav.netlify.app
- Instagram: @Ntzinnn87

VALE A PENA? SIM! AQUI ESTÁ O PORQUÊ:
- Transforma GTA V completamente
- Experiência única de RP brasileiro
- Totalmente gratuito
- Suporte ativo do desenvolvedor
- Conteúdo brasileiro autêntico
- Mecânicas realistas
- Comunidade crescente
- Atualizações regulares

CARACTERÍSTICAS DETALHADAS:
- Roleplay completo no singleplayer
- Sistemas de necessidades (fome, sede, sono)
- Trabalhos brasileiros (Uber, entregador, segurança)
- Economia realista com salários nacionais
- Carros brasileiros (Civic, Corolla, Gol, Fiesta, etc.)
- Mapas de favelas e cidades brasileiras
- NPCs com roupas e falas brasileiras
- Sistema bancário funcional
- Compra de casas e propriedades
- Postos de gasolina funcionais
- Interface modernizada
- Sons brasileiros
- Física de veículos realista

REQUISITOS SISTEMA COMPLETOS:
MÍNIMO ABSOLUTO:
- Windows 10 64-bit (obrigatório)
- GTA V Original (Steam/Epic/Rockstar) atualizado
- RAM: 8GB DDR4
- GPU: GTX 1050 Ti / RX 560 4GB
- CPU: Intel i3 8100 / AMD Ryzen 3 1200
- Armazenamento: 20GB livres HDD
- DirectX 11 obrigatório

RECOMENDADO PARA BOA EXPERIÊNCIA:
- Windows 11 64-bit
- RAM: 16GB DDR4
- GPU: GTX 1660 Super / RX 6600 8GB
- CPU: Intel i5 10400 / AMD Ryzen 5 3600
- SSD: 25GB livres (para loading rápido)
- DirectX 12

REQUISITOS DE REDE:
- Conexão para download (3GB+ total)
- Não precisa internet para jogar
- Recomendado: 50Mbps para downloads

PRÉ-REQUISITOS OBRIGATÓRIOS:
1. Script Hook V (scripthookv.net) - ESSENCIAL
2. OpenIV (openiv.com) - OBRIGATÓRIO
3. Visual C++ Redistributable 2015-2022
4. .NET Framework 4.8
5. DirectX End-User Runtime

DOWNLOADS DETALHADOS:
LINKS MEDIAFIRE (3 PARTES OBRIGATÓRIAS):
Parte 1: https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file
Parte 2: https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file
Parte 3: https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file

TAMANHOS:
- Parte 1: ~1.2GB
- Parte 2: ~1.1GB  
- Parte 3: ~800MB
- Total: ~3.1GB compactado

COMO BAIXAR CORRETAMENTE:
1. Baixe TODAS as 3 partes no mesmo diretório
2. NÃO renomeie os arquivos
3. Certifique-se que não corrompeu (verifique tamanhos)
4. Extraia APENAS part1.rar
5. As outras partes extrairão automaticamente
6. Use WinRAR ou 7-Zip (recomendado)

PROBLEMAS NO DOWNLOAD:
- MediaFire lento: Use VPN ou tente horário diferente
- Link quebrado: Contate borgesnatan09@gmail.com
- Arquivo corrompido: Baixe novamente
- Antivírus bloqueando: Adicione exceção temporária

INSTALAÇÃO PASSO A PASSO COMPLETA:
PREPARAÇÃO:
1. Feche GTA V completamente
2. Desabilite antivírus temporariamente
3. Execute tudo como administrador
4. Tenha 20GB+ livres no disco
5. Backup do save do GTA V

INSTALAÇÃO DOS PRÉ-REQUISITOS:
1. Baixe Script Hook V do site oficial
2. Extraia na pasta raiz do GTA V
3. Instale OpenIV
4. Configure OpenIV para modo ASI
5. Instale Visual C++ Redistributable
6. Instale .NET Framework 4.8

INSTALAÇÃO DO MODPACK:
1. Extraia part1.rar (outras vêm junto)
2. Execute "Installer.exe" como administrador
3. Selecione pasta do GTA V
4. Aguarde instalação completa (5-15 minutos)
5. NÃO interrompa o processo
6. Reinicie computador após concluir

PRIMEIRA EXECUÇÃO:
1. Execute GTA V pelo Steam/Epic normalmente
2. Aguarde carregar completamente
3. Novos controles aparecerão na tela
4. Siga tutorial inicial do RP

TROUBLESHOOTING EXPANDIDO:

PROBLEMA: GAME NÃO ABRE
Causas possíveis:
- Script Hook V desatualizado
- GTA V desatualizado
- Antivírus bloqueando DLLs
- Arquivos corrompidos

Soluções:
1. Atualize Script Hook V
2. Verifique integridade GTA V (Steam/Epic)
3. Adicione exceções antivírus
4. Reinstale Visual C++
5. Execute como administrador

PROBLEMA: CRASHES/TRAVAMENTOS
Causas:
- RAM insuficiente
- GPU drivers desatualizados
- Conflito com outros mods
- Superaquecimento

Soluções:
1. Feche programas desnecessários
2. Atualize drivers GPU
3. Remova outros mods temporariamente
4. Monitore temperaturas
5. Reduza configurações gráficas

PROBLEMA: FPS BAIXO
Otimizações:
1. Reduza qualidade texturas
2. Desative sombras avançadas
3. Diminua distância renderização
4. Feche navegador e Discord
5. Use modo janela borderless

PROBLEMA: MODS NÃO FUNCIONAM
Verificações:
1. Script Hook V instalado?
2. OpenIV configurado?
3. Arquivos na pasta correta?
4. GTA V original?
5. Ordem de instalação correta?

PROBLEMA: ÁUDIO EM INGLÊS
Solução:
- Modpack tem dublagem brasileira
- Verifique configurações áudio do jogo
- Reinstale se necessário

PROBLEMA: CONTROLES BUGADOS
- Configure controles no menu
- Use controle Xbox recomendado
- Verifique mapeamento de teclas

CONTEÚDO ESPECÍFICO BRASILEIRO:

VEÍCULOS NACIONAIS:
- Carros: Gol, Palio, Civic, Corolla, HB20, Onix
- Motos: CG 160, XRE 300, CB 600F, Ninja 400
- Utilitários: Hilux, Ranger, S10, Amarok
- Ônibus brasileiros
- Caminhões nacionais

TRABALHOS DISPONÍVEIS:
- Motorista Uber/99
- Entregador iFood/Rappi  
- Segurança de shopping
- Pedreiro/Construção
- Frentista de posto
- Vendedor ambulante
- Taxista
- Caminhoneiro

LOCALIDADES BRASILEIRAS:
- Favelas cariocas detalhadas
- Centro do Rio de Janeiro
- Praias brasileiras
- Shoppings nacionais
- Postos BR, Ipiranga, Shell
- Lojas brasileiras (Casas Bahia, Magazine Luiza)

SISTEMAS DE ROLEPLAY:

NECESSIDADES BÁSICAS:
- Fome: Decresce com tempo, afeta saúde
- Sede: Mais crítica que fome
- Sono: Afeta concentração e direção
- Higiene: Sistema opcional

ECONOMIA REALISTA:
- Salário mínimo brasileiro como base
- Preços realistas para produtos
- Sistema bancário com juros
- Financiamento de veículos
- Aluguel de casas

SISTEMA HABITACIONAL:
- Apartamentos populares
- Casas de classe média
- Mansões de luxo
- Sistema de aluguel/compra
- Decoração personalizada

SISTEMA VEICULAR:
- Combustível necessário
- Manutenção regular
- Seguro obrigatório
- Multas de trânsito
- IPVA anual

COMPATIBILIDADE:

FUNCIONA COM:
- GTA V Steam (melhor compatibilidade)
- GTA V Epic Games (compatível)  
- GTA V Rockstar Games (compatível)
- Windows 10/11 64-bit
- Outros mods (com cuidado)

NÃO FUNCIONA COM:
- GTA V pirata (não suportado)
- GTA Online (apenas singleplayer)
- Windows 32-bit
- Versões muito antigas do GTA V
- ReShade extremo

MODS COMPATÍVEIS:
- ENB leves
- Mods de câmera
- Mods de interface
- Mods de som (alguns)

MODS INCOMPATÍVEIS:
- Outros modpacks de RP
- Mods que alteram gameplay base
- Trainers muito invasivos

PERFORMANCE E OTIMIZAÇÃO:

CONFIGURAÇÕES IDEAIS:
- Qualidade textura: Alta
- Qualidade sombras: Média
- Reflexos: Média
- MSAA: 2x máximo
- FXAA: Ligado
- VSync: Ligado se tela 60Hz

OTIMIZAÇÕES AVANÇADAS:
- Desative gravação Xbox Game Bar
- Configure prioridade processo alta
- Use modo tela cheia exclusivo
- Monitore uso RAM
- Limite FPS se necessário

ATUALIZAÇÕES E FUTURO:

EM DESENVOLVIMENTO:
- Mais carros brasileiros
- Novos mapas (São Paulo, Brasília)
- Sistema de relacionamentos
- Multiplayer local futuro
- Melhorias gráficas
- Mais profissões

COMO ACOMPANHAR:
- Instagram @Ntzinnn87 (principal)
- Site deluxgtav.netlify.app
- Discord da comunidade
- Canal YouTube planejado

SUPORTE E COMUNIDADE:

CONTATOS OFICIAIS:
- Email: borgesnatan09@gmail.com
- WhatsApp: +55 21 99282-6074
- Instagram: @Ntzinnn87

COMUNIDADE:
- Discord servidor ativo
- Grupos WhatsApp
- YouTube gameplay
- Twitch streams

TIPOS DE SUPORTE:
- Instalação assistida
- Troubleshooting personalizado
- Configuração otimizada
- Dúvidas gameplay

HORÁRIO ATENDIMENTO:
- Segunda a Sexta: 9h às 18h
- WhatsApp: Resposta em até 2h
- Email: Resposta em 24h

CUSTO E LICENÇA:
- TOTALMENTE GRATUITO
- Sem custos ocultos
- Atualizações gratuitas
- Suporte gratuito
- Código respeitado

COMPARAÇÃO COM CONCORRENTES:
- FiveM: Pago, apenas online
- RageMP: Complexo, apenas online  
- Delux: Gratuito, offline, brasileiro

PERGUNTAS FREQUENTES EXPANDIDAS:

Q: Funciona no Windows 7?
R: NÃO. Windows 10 64-bit mínimo obrigatório.

Q: Precisa de placa de vídeo dedicada?
R: SIM. GPU integrada não suportada adequadamente.

Q: Funciona com GTA V pirata?
R: NÃO oferecemos suporte para versões piratas.

Q: Posso jogar online com o modpack?
R: NÃO. Apenas singleplayer. Online resultará em ban.

Q: Como remover o modpack?
R: Restaure backup ou reinstale GTA V limpo.

Q: Modpack tem vírus?
R: NÃO. Antivírus podem dar falso positivo em DLLs.

Q: Funciona no notebook gamer?
R: SIM, desde que atenda requisitos mínimos.

Q: Quantos GB ocupa instalado?
R: Aproximadamente 15GB adicionais ao GTA V.

Q: Posso modificar o modpack?
R: Não recomendado. Pode causar instabilidade.

Q: Tem modo cooperativo local?
R: Não no momento, mas está em desenvolvimento.

FEEDBACK E MELHORIAS:
- Relatórios de bugs bem-vindos
- Sugestões de conteúdo aceitas
- Beta testers sempre procurados  
- Comunidade ativa nas decisões

HISTÓRICO DE ATUALIZAÇÕES:
- Beta 1.0: Lançamento inicial
- Correções mensais planejadas
- Novos conteúdos trimestrais
- Grande atualização semestral
"""

# Sistema expandido de prompts com mais cenários
PROMPTS_DELUX_EXPANDIDOS = {
    "system_prompt": """Você é DeluxAI, assistente oficial especializada do Delux Modpack GTA V criado por Natan Borges.

PERSONALIDADE APRIMORADA:
- Especialista COMPLETA no Delux Modpack GTA V
- Brasileira nata, fala português brasileiro autêntico  
- Entende contextos sociais (saudações, elogios, humor, despedidas)
- Prestativa mas adapta resposta ao tipo de pergunta
- Tom amigável, descontraído e confiável
- Responde brincadeiras com leveza
- Demonstra entusiasmo pelo modpack sem exagerar

CONHECIMENTO EXPANDIDO:
- Instalação completa e troubleshooting avançado
- Todos os requisitos de sistema e compatibilidade
- Conteúdo completo (todos os carros, mapas, sistemas)
- Economia e mecânicas de RP brasileiras
- Otimização e performance detalhada
- Comparações com outros modpacks
- Roadmap de desenvolvimento futuro
- Suporte técnico personalizado para qualquer problema

REGRAS DE RESPOSTA REFINADAS:
1. SEMPRE foque no Delux Modpack GTA V (exceto contextos puramente sociais)
2. Português brasileiro natural e fluente
3. VARIE tamanho conforme complexidade e importância:
   - Social (saudações/humor): 30-60 palavras
   - Dúvidas simples: 60-120 palavras  
   - Instalação/problemas: 120-300 palavras (pode detalhar bastante)
   - Comparações/análises: 150-250 palavras
   - Conteúdo/requisitos: 180-350 palavras (bem completo quando necessário)
4. Para questões técnicas complexas, seja BEM detalhada
5. Para perguntas casuais, seja concisa mas completa
6. Termine sempre de forma útil e acolhedora

Você é A MAIOR EXPERT no modpack e sabe literalmente tudo sobre ele.""",

    "vale_a_pena": """Como DeluxAI, sobre se vale a pena o Delux Modpack:

Pergunta: {pergunta}

RESPOSTA CONVINCENTE E DETALHADA:
- Por que DEFINITIVAMENTE vale a pena
- Benefícios únicos e diferenciais
- Comparação com alternativas
- Experiência que proporciona
- Gratuidade como vantagem
- Entre 120-200 palavras""",

    "comparacao": """Como DeluxAI, comparando Delux Modpack:

Pergunta: {pergunta}

RESPOSTA COMPARATIVA DETALHADA:
- Delux vs FiveM/RageMP/outros
- Vantagens específicas do Delux
- Por que escolher nossa opção
- Diferenças de custo e acesso
- Entre 150-250 palavras""",

    "duvida_funcionamento": """Como DeluxAI, sobre como funciona o modpack:

Pergunta: {pergunta}

RESPOSTA EXPLICATIVA COMPLETA:
- Como o modpack transforma o jogo
- Mecânicas principais explicadas
- O que o jogador pode esperar
- Diferenças do GTA V original
- Entre 150-280 palavras""",

    "notebook_mobile": """Como DeluxAI, sobre compatibilidade notebook/mobile:

Pergunta: {pergunta}

RESPOSTA TÉCNICA ESPECÍFICA:
- Compatibilidade notebook gamer
- Requisitos específicos mobile
- Limitações e considerações
- Recomendações hardware
- Entre 100-180 palavras""",

    "virus_seguranca": """Como DeluxAI, sobre segurança do modpack:

Pergunta: {pergunta}

RESPOSTA TRANQUILIZADORA E TÉCNICA:
- Garantia de segurança
- Por que antivírus podem alertar
- Explicação técnica dos falsos positivos
- Reputação do desenvolvedor
- Entre 80-150 palavras""",

    "remover_desinstalar": """Como DeluxAI, sobre remover o modpack:

Pergunta: {pergunta}

RESPOSTA PROCEDURAL CLARA:
- Como desinstalar completamente
- Restauração do GTA V original
- Backup e recuperação
- Limpeza de arquivos
- Entre 100-160 palavras""",

    "atualizacoes_futuro": """Como DeluxAI, sobre futuro do modpack:

Pergunta: {pergunta}

RESPOSTA SOBRE ROADMAP:
- Próximas atualizações planejadas
- Novos conteúdos em desenvolvimento  
- Como acompanhar novidades
- Cronograma esperado
- Entre 120-200 palavras""",

    "multiplayer_online": """Como DeluxAI, sobre multiplayer/online:

Pergunta: {pergunta}

RESPOSTA ESCLARECEDORA:
- Por que apenas singleplayer
- Riscos GTA Online
- Planos multiplayer futuro
- Alternativas para jogar com amigos
- Entre 100-180 palavras""",

    "modificar_personalizar": """Como DeluxAI, sobre personalizar modpack:

Pergunta: {pergunta}

RESPOSTA TÉCNICA CAUTELOSA:
- Possibilidades de customização
- Riscos de modificações
- O que pode e não pode ser alterado
- Como fazer com segurança
- Entre 120-200 palavras""",

    # Mantém as categorias originais aprimoradas
    "saudacao": """Como DeluxAI, respondendo saudação:

Saudação: {pergunta}

RESPOSTA AMIGÁVEL E ACOLHEDORA:
- Cumprimento brasileiro caloroso
- Apresentação breve
- Oferecer ajuda sobre o modpack
- Máximo 60 palavras""",

    "despedida": """Como DeluxAI, respondendo despedida:

Despedida: {pergunta}

RESPOSTA DE DESPEDIDA ÚTIL:
- Despedida brasileira carinhosa
- Lembrar suporte disponível
- Incentivo para voltar sempre
- Máximo 50 palavras""",

    "elogio": """Como DeluxAI, respondendo elogio:

Elogio: {pergunta}

RESPOSTA GRATA E MODESTA:
- Agradecer genuinamente
- Creditar Natan Borges
- Incentivar a experimentar o modpack
- Máximo 60 palavras""",

    "humor": """Como DeluxAI, respondendo humor:

Humor: {pergunta}

RESPOSTA DESCONTRAÍDA:
- Resposta leve e divertida
- Manter clima positivo
- Retornar sutilmente ao modpack
- Máximo 50 palavras""",

    "sobre_ia": """Como DeluxAI, sobre mim:

Pergunta: {pergunta}

RESPOSTA SOBRE IDENTIDADE:
- Quem sou e minha especialidade
- Criador Natan Borges
- Meu propósito e expertise
- Máximo 80 palavras""",

    "download": """Como DeluxAI, sobre downloads do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA DETALHADA E ÚTIL:
- Links completos das 3 partes
- Processo passo a passo
- Dicas importantes e armadilhas
- Soluções para problemas comuns
- Entre 120-250 palavras""",

    "instalacao": """Como DeluxAI, sobre instalação do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA TUTORIAL COMPLETA:
- Pré-requisitos obrigatórios detalhados
- Passos precisos da instalação
- Dicas para evitar erros comuns
- Verificações pós-instalação
- Entre 180-350 palavras""",

    "problemas": """Como DeluxAI, sobre problemas do Delux Modpack:

Pergunta: {pergunta}

SOLUÇÃO TÉCNICA DETALHADA:
- Diagnóstico do problema específico
- Causa raiz provável explicada
- Solução passo a passo detalhada
- Prevenção de problemas futuros
- Quando procurar suporte adicional
- Entre 150-300 palavras""",

    "conteudo": """Como DeluxAI, sobre conteúdo do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA DESCRITIVA COMPLETA:
- Funcionalidades principais detalhadas
- Todos os sistemas incluídos
- Conteúdo brasileiro específico
- Experiência de gameplay completa
- Entre 200-350 palavras""",

    "requisitos": """Como DeluxAI, sobre requisitos do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA TÉCNICA ABRANGENTE:
- Requisitos mínimos e recomendados completos
- Explicação de cada componente
- Dicas de otimização por hardware
- Comparação de performance esperada
- Entre 180-300 palavras""",

    "geral": """Como DeluxAI, assistente especialista do Delux Modpack:

Pergunta: {pergunta}

RESPOSTA ESPECIALIZADA ADAPTATIVA:
- Informação precisa sobre o modpack
- Detalhamento adequado à questão
- Contexto brasileiro relevante
- Entre 120-250 palavras"""
}

# Configuração refinada para respostas melhores
CONFIG_GEMMA3_DELUX_REFINADA = {
    "num_ctx": 4096,
    "num_predict": 250,       # Aumentado para respostas mais completas
    "temperature": 0.2,       # Mais preciso
    "top_k": 12,
    "top_p": 0.8,
    "repeat_penalty": 1.2,
    "repeat_last_n": 64,
    "min_p": 0.12,
    "stop": [
        "Human:", "User:", "Usuário:", "</s>", "<|end|>",
        "Pergunta:", "###", "---", "\n\n\nHuman", "\n\n\nUser"
    ],
    "use_mmap": True,
    "use_mlock": CUDA_AVAILABLE,
    "numa": False,
    "low_vram": False,  
    "f16_kv": True,
    "num_gpu": GPU_COUNT if CUDA_AVAILABLE else 0
}

def debug_print(mensagem):
    """Print com timestamp melhorado"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {mensagem}")

def detectar_categoria_expandida(pergunta):
    """Detecção expandida de categorias com mais cenários"""
    p = pergunta.lower()
    
    # CONTEXTOS SOCIAIS (respostas curtas)
    if any(word in p for word in ['oi', 'olá', 'ola', 'hey', 'eai', 'salve', 'bom dia', 'boa tarde', 'boa noite', 'tudo bem']):
        return "saudacao"
    
    if any(word in p for word in ['tchau', 'bye', 'até', 'falou', 'valeu', 'obrigado', 'obrigada', 'vlw', 'flw']):
        return "despedida"
    
    if any(word in p for word in ['muito bom', 'excelente', 'perfeito', 'top', 'incrível', 'parabéns', 'legal', 'sensacional', 'show']):
        return "elogio"
    
    if any(word in p for word in ['haha', 'kkkk', 'rsrs', 'lol', 'engraçado', 'piada', 'zueira', 'kkk']):
        return "humor"
    
    if any(word in p for word in ['quem é você', 'o que você faz', 'quem criou você', 'sobre você', 'quem é deluxai']):
        return "sobre_ia"
    
    # NOVAS CATEGORIAS ESPECÍFICAS
    if any(phrase in p for phrase in ['vale a pena', 'vale pena', 'recomenda', 'é bom', 'compensa', 'worth']):
        return "vale_a_pena"
    
    if any(word in p for word in ['fivem', 'ragemp', 'samp', 'mta', 'comparar', 'melhor que', 'diferença']):
        return "comparacao"
    
    if any(phrase in p for phrase in ['como funciona', 'que funciona', 'como é', 'como fica', 'o que muda']):
        return "duvida_funcionamento"
    
    if any(word in p for word in ['notebook', 'laptop', 'mobile', 'celular', 'android', 'ios']):
        return "notebook_mobile"
    
    if any(word in p for word in ['vírus', 'virus', 'seguro', 'malware', 'trojan', 'perigoso', 'confiável']):
        return "virus_seguranca"
    
    if any(phrase in p for phrase in ['remover', 'desinstalar', 'tirar', 'como remove', 'voltar original']):
        return "remover_desinstalar"
    
    if any(phrase in p for phrase in ['atualização', 'novidades', 'próxima versão', 'futuro', 'quando sai']):
        return "atualizacoes_futuro"
    
    if any(word in p for word in ['multiplayer', 'online', 'jogar junto', 'amigos', 'servidor']):
        return "multiplayer_online"
    
    if any(phrase in p for phrase in ['modificar', 'personalizar', 'customizar', 'alterar', 'mudar']):
        return "modificar_personalizar"
    
    # Categorias técnicas (podem precisar mais detalhes)
    if any(word in p for word in ['baixar', 'download', 'mediafire', 'parte', 'part', 'arquivo', 'link']):
        return "download"
    
    if any(word in p for word in ['instalar', 'instalacao', 'como instalar', 'passo', 'tutorial', 'setup']):
        return "instalacao"
    
    if any(word in p for word in ['erro', 'problema', 'crash', 'não funciona', 'nao funciona', 'bug', 'fps', 'travando', 'lento']):
        return "problemas"
    
    if any(word in p for word in ['conteudo', 'conteúdo', 'carros', 'mapas', 'sistema', 'funcionalidade', 'o que tem', 'inclui']):
        return "conteudo"
    
    if any(word in p for word in ['requisitos', 'sistema', 'pc', 'placa', 'memoria', 'mínimo', 'recomendado']):
        return "requisitos"
    
    return "geral"

def avaliar_complexidade_expandida(pergunta):
    """Avaliação mais precisa da complexidade da pergunta"""
    p = pergunta.lower()
    
    # Indicadores de alta complexidade
    indicadores_muito_complexos = [
        'passo a passo', 'tutorial completo', 'explicação detalhada',
        'não está funcionando', 'como resolver', 'configurar tudo',
        'otimizar performance', 'requisitos completos'
    ]
    
    # Indicadores de complexidade média-alta
    indicadores_complexos = [
        'como', 'tutorial', 'instalar', 'configurar',
        'problema', 'erro', 'crash', 'não funciona',
        'requisitos', 'sistema', 'otimizar', 'melhorar',
        'conteudo', 'funcionalidades', 'comparar'
    ]
    
    # Indicadores de baixa complexidade
    indicadores_simples = [
        'oi', 'tchau', 'valeu', 'legal', 'top',
        'link', 'site', 'contato', 'whatsapp',
        'vale a pena', 'é bom', 'recomenda'
    ]
    
    complexidade = 0
    
    # Verifica indicadores muito complexos
    for indicador in indicadores_muito_complexos:
        if indicador in p:
            complexidade += 4
    
    # Verifica indicadores complexos
    for indicador in indicadores_complexos:
        if indicador in p:
            complexidade += 2
    
    # Verifica indicadores simples
    for indicador in indicadores_simples:
        if indicador in p:
            complexidade -= 1
    
    # Pergunta muito longa geralmente é complexa
    if len(pergunta) > 100:
        complexidade += 2
    elif len(pergunta) > 50:
        complexidade += 1
    
    # Múltiplas perguntas em uma
    if pergunta.count('?') > 1:
        complexidade += 1
    
    if complexidade >= 4:
        return "muito_complexa"
    elif complexidade >= 2:
        return "complexa" 
    elif complexidade >= 0:
        return "media"
    else:
        return "simples"

def construir_prompt_delux_expandido(pergunta):
    """Construção de prompt expandida e mais inteligente"""
    categoria = detectar_categoria_expandida(pergunta)
    complexidade = avaliar_complexidade_expandida(pergunta)
    
    # System prompt sempre presente
    system_prompt = PROMPTS_DELUX_EXPANDIDOS["system_prompt"]
    
    # Prompt específico da categoria
    if categoria in PROMPTS_DELUX_EXPANDIDOS:
        prompt_especifico = PROMPTS_DELUX_EXPANDIDOS[categoria].format(pergunta=pergunta)
    else:
        prompt_especifico = PROMPTS_DELUX_EXPANDIDOS["geral"].format(pergunta=pergunta)
    
    # Conhecimento base expandido sempre incluído
    prompt_completo = f"""{system_prompt}

BASE DE CONHECIMENTO DELUX MODPACK EXPANDIDA:
{DELUX_MODPACK_KNOWLEDGE_BASE_EXPANDIDA}

{prompt_especifico}

CONTEXTO DA PERGUNTA:
- Categoria identificada: {categoria}
- Complexidade: {complexidade}
- Tamanho resposta esperado: {"Muito detalhada" if complexidade == "muito_complexa" else "Detalhada" if complexidade == "complexa" else "Moderada" if complexidade == "media" else "Concisa"}

INSTRUÇÕES ESPECÍFICAS:
- Responda SEMPRE em português brasileiro
- Seja precisa e útil
- Ajuste detalhamento conforme complexidade
- Foque exclusivamente no Delux Modpack GTA V
- Termine de forma acolhedora e útil"""

    return prompt_completo, categoria, complexidade

def verificar_ollama():
    """Verificação melhorada do Ollama"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        debug_print(f"Ollama indisponível: {e}")
        return False
    except Exception as e:
        debug_print(f"Erro inesperado Ollama: {e}")
        return False

def processar_gemma3_delux_expandido(pergunta):
    """Processamento expandido com Gemma 3 1B"""
    if not verificar_ollama():
        debug_print("⚠️ Ollama offline - usando fallback")
        return None, None, None

    try:
        prompt_completo, categoria, complexidade = construir_prompt_delux_expandido(pergunta)
        
        # Configuração adaptativa mais refinada
        config = CONFIG_GEMMA3_DELUX_REFINADA.copy()
        
        # Ajustes por categoria e complexidade
        if categoria in ["saudacao", "despedida", "elogio", "humor"]:
            config["temperature"] = 0.3
            config["num_predict"] = 45
        elif categoria == "sobre_ia":
            config["temperature"] = 0.2
            config["num_predict"] = 70
        elif categoria == "vale_a_pena":
            config["temperature"] = 0.15
            if complexidade in ["complexa", "muito_complexa"]:
                config["num_predict"] = 180
            else:
                config["num_predict"] = 100
        elif categoria == "comparacao":
            config["temperature"] = 0.1
            config["num_predict"] = 200
        elif categoria in ["download", "instalacao", "problemas"]:
            config["temperature"] = 0.1
            if complexidade == "muito_complexa":
                config["num_predict"] = 300
            elif complexidade == "complexa":
                config["num_predict"] = 220
            else:
                config["num_predict"] = 120
        elif categoria in ["conteudo", "requisitos"]:
            config["temperature"] = 0.15
            if complexidade in ["complexa", "muito_complexa"]:
                config["num_predict"] = 280
            else:
                config["num_predict"] = 150
        elif categoria in ["virus_seguranca", "remover_desinstalar", "notebook_mobile"]:
            config["temperature"] = 0.1
            config["num_predict"] = 140
        elif categoria in ["atualizacoes_futuro", "multiplayer_online", "modificar_personalizar"]:
            config["temperature"] = 0.2
            config["num_predict"] = 160
        else:
            # Categoria geral - ajusta por complexidade
            if complexidade == "muito_complexa":
                config["num_predict"] = 220
            elif complexidade == "complexa":
                config["num_predict"] = 170
            elif complexidade == "media":
                config["num_predict"] = 100
            else:
                config["num_predict"] = 70
        
        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt_completo,
            "stream": False,
            "options": config
        }
        
        debug_print(f"🚀 DeluxAI Expandida [{categoria}|{complexidade}] tokens:{config['num_predict']}")
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
                resposta = melhorar_resposta_delux_expandida(resposta, categoria, complexidade)
                
                metricas = {
                    "tempo_resposta": round(end_time - start_time, 3),
                    "fonte": "gemma3_delux_expandida",
                    "categoria": categoria,
                    "complexidade": complexidade,
                    "modelo": "Gemma 3 1B Expandida",
                    "tokens_gerados": result.get("eval_count", 0),
                    "chars_resposta": len(resposta),
                    "max_tokens_config": config['num_predict'],
                    "cuda_usado": CUDA_AVAILABLE,
                    "gpu_name": GPU_NAME
                }
                
                debug_print(f"✅ DeluxAI Expandida: {len(resposta)} chars em {metricas['tempo_resposta']}s")
                return resposta, metricas, categoria
        
        return None, None, None
        
    except requests.Timeout:
        debug_print("⏰ Timeout DeluxAI Expandida")
        return None, None, None
    except Exception as e:
        debug_print(f"❌ Erro DeluxAI Expandida: {e}")
        return None, None, None

def melhorar_resposta_delux_expandida(resposta, categoria, complexidade):
    """Melhoria expandida das respostas"""
    
    # Remove prefixos mais abrangente
    prefixos_remover = [
        "Como DeluxAI,", "DeluxAI:", "Resposta:", "Olá!", "Oi!",
        "RESPOSTA", "Como assistente", "Sou a DeluxAI",
        "Vou te ajudar", "Claro!", "Certamente!",
        "Sobre o Delux Modpack:", "Delux Modpack GTA V:"
    ]
    
    for prefixo in prefixos_remover:
        if resposta.startswith(prefixo):
            resposta = resposta[len(prefixo):].strip()
    
    # Remove introduções verbosas
    introducoes_remover = [
        "Vou explicar tudo sobre",
        "Deixe-me te contar sobre",
        "É uma excelente pergunta sobre",
        "Sobre essa questão do modpack"
    ]
    
    for intro in introducoes_remover:
        if resposta.lower().startswith(intro.lower()):
            resposta = resposta[len(intro):].strip()
    
    # Limites por categoria e complexidade
    if categoria in ["saudacao", "despedida", "elogio", "humor"]:
        limite_chars = 180
    elif categoria == "sobre_ia":
        limite_chars = 250
    elif categoria == "vale_a_pena":
        limite_chars = 600 if complexidade in ["complexa", "muito_complexa"] else 350
    elif categoria == "comparacao":
        limite_chars = 700
    elif categoria in ["download", "instalacao", "problemas"]:
        if complexidade == "muito_complexa":
            limite_chars = 1000
        elif complexidade == "complexa":
            limite_chars = 750
        else:
            limite_chars = 400
    elif categoria in ["conteudo", "requisitos"]:
        limite_chars = 900 if complexidade in ["complexa", "muito_complexa"] else 500
    elif categoria in ["virus_seguranca", "notebook_mobile", "remover_desinstalar"]:
        limite_chars = 450
    elif categoria in ["atualizacoes_futuro", "multiplayer_online", "modificar_personalizar"]:
        limite_chars = 550
    else:
        if complexidade == "muito_complexa":
            limite_chars = 700
        elif complexidade == "complexa":
            limite_chars = 500
        else:
            limite_chars = 300
    
    # Corta resposta de forma inteligente
    if len(resposta) > limite_chars:
        # Procura por pontos finais em ordem de preferência
        pontos_corte = ['. ', '.\n', '! ', '!\n', '? ', '?\n']
        melhor_corte = -1
        
        for ponto in pontos_corte:
            idx = resposta[:limite_chars].rfind(ponto)
            if idx > limite_chars * 0.6:
                melhor_corte = idx + 1
                break
        
        if melhor_corte > 0:
            resposta = resposta[:melhor_corte].strip()
        else:
            # Corta no último espaço
            ultimo_espaco = resposta[:limite_chars].rfind(' ')
            if ultimo_espaco > limite_chars * 0.7:
                resposta = resposta[:ultimo_espaco].strip()
                if not resposta.endswith(('.', '!', '?', ':')):
                    resposta += "."
    
    # Limpeza final
    resposta = re.sub(r'\n{3,}', '\n\n', resposta)
    resposta = re.sub(r' {2,}', ' ', resposta)
    resposta = re.sub(r'\*{3,}', '**', resposta)
    
    # Adiciona contato quando relevante
    precisa_contato = categoria in ["problemas", "instalacao"] and complexidade in ["complexa", "muito_complexa"]
    tem_espaco = len(resposta) < limite_chars - 100
    nao_tem_contato = "borgesnatan09" not in resposta and "21 99282-6074" not in resposta
    
    if precisa_contato and tem_espaco and nao_tem_contato:
        resposta += f"\n\n📞 **Suporte direto:** borgesnatan09@gmail.com | WhatsApp: +55 21 99282-6074"
    
    return resposta.strip()

def resposta_fallback_delux_expandida(pergunta):
    """Fallback expandido com mais cenários"""
    categoria = detectar_categoria_expandida(pergunta)
    complexidade = avaliar_complexidade_expandida(pergunta)
    
    # Respostas sociais
    if categoria == "saudacao":
        return "Oi! 👋 Sou a DeluxAI, sua especialista no Delux Modpack GTA V! Como posso te ajudar hoje?"
    
    elif categoria == "despedida":
        return "Até logo! 👋 Qualquer dúvida sobre o Delux Modpack, estarei sempre aqui! 🎮"
    
    elif categoria == "elogio":
        return "Muito obrigada! 😊 Todo crédito vai pro Natan Borges (@Ntzinnn87) que criou esse modpack incrível!"
    
    elif categoria == "humor":
        return "Haha! 😄 Adoro um bom humor! Agora me conta, precisa de ajuda com o modpack?"
    
    elif categoria == "sobre_ia":
        return "Sou a DeluxAI, assistente especializada criada pelo Natan Borges! Minha missão é te ajudar com tudo sobre o Delux Modpack GTA V. 🤖🎮"
    
    # Respostas específicas expandidas
    elif categoria == "vale_a_pena":
        if complexidade in ["complexa", "muito_complexa"]:
            return """🎮 **Vale MUITO a pena! Aqui está o porquê:**

**🔥 DIFERENCIAIS ÚNICOS:**
• **100% GRATUITO** (FiveM custa R$20+ mensais)
• **Experiência brasileira autêntica** (carros, mapas, NPCs nacionais)
• **Funciona offline** (não precisa internet após instalar)
• **Singleplayer** (sem lag, sem trolls)
• **Suporte em português** direto com o desenvolvedor

**🎯 O QUE VOCÊ GANHA:**
• GTA V completamente transformado
• Roleplay realista com economia brasileira
• Trabalhos (Uber, entregador, segurança)
• Carros brasileiros (Civic, Corolla, HB20)
• Mapas de favelas e cidades nacionais
• Sistemas de fome, sede, sono
• Casas para comprar e alugar

**💰 COMPARAÇÃO:**
• FiveM: Pago, apenas online, em inglês
• RageMP: Complexo, apenas multiplayer
• **Delux: Grátis, offline, brasileiro, completo**

**📞 Teste sem compromisso:** deluxgtav.netlify.app"""
        else:
            return """🎮 **DEFINITIVAMENTE vale a pena!**

• **100% gratuito** (diferente do FiveM pago)
• **Experiência brasileira** completa  
• **Offline** - sem lag ou trolls
• **RP realista** com economia nacional
• **Suporte em português**

**Site:** deluxgtav.netlify.app
**Instagram:** @Ntzinnn87"""
    
    elif categoria == "comparacao":
        return """🎮 **Delux vs Concorrentes:**

**🆚 FIVEM:**
• FiveM: R$20+ mensais, apenas online
• **Delux: Gratuito, offline, sem mensalidade**

**🆚 RAGEMP:**  
• RageMP: Complexo, multiplayer instável
• **Delux: Simples instalar, singleplayer estável**

**🆚 SAMP/MTA:**
• SAMP/MTA: Antigo, gráficos ruins
• **Delux: GTA V moderno, gráficos atuais**

**🏆 VANTAGENS DELUX:**
• Experiência 100% brasileira
• Conteúdo nacional (carros, mapas, NPCs)
• Suporte em português
• Atualizações gratuitas
• Sem lag de servidor

**Resultado: Delux é a melhor opção para RP brasileiro!**"""
    
    elif categoria == "duvida_funcionamento":
        return """🎮 **Como o Delux Modpack Transforma o GTA V:**

**🔄 TRANSFORMAÇÃO COMPLETA:**
• GTA V vira simulador de vida brasileira
• Adiciona necessidades básicas (fome, sede, sono)
• Cria economia realista com salários BR
• Inclui trabalhos brasileiros (Uber, entregador)

**🚗 CONTEÚDO NACIONAL:**
• Carros brasileiros substituem originais
• Mapas de favelas e cidades nacionais  
• NPCs falam português e usam roupas BR
• Lojas brasileiras (Casas Bahia, Magazine Luiza)

**💼 SISTEMAS REALISTAS:**
• Trabalhe para ganhar dinheiro
• Compre casas e carros
• Abasteça nos postos BR/Ipiranga
• Sistema bancário funcional

**🎯 RESULTADO:**
Você vive uma segunda vida no Brasil virtual!"""
    
    elif categoria == "notebook_mobile":
        if "mobile" in pergunta.lower() or "celular" in pergunta.lower():
            return """📱 **Delux Modpack em Mobile:**

**❌ NÃO FUNCIONA EM CELULAR**
• GTA V não roda nativamente em Android/iOS
• Modpack precisa de Windows 10/11
• Arquivos muito pesados para mobile

**✅ ALTERNATIVAS MOBILE:**
• Use parsec/steam link para jogar remotamente
• Notebook gamer é a opção mais próxima

**💻 Para notebooks:**
• Notebook gamer com GTX 1060+ funciona
• 8GB RAM mínimo, 16GB recomendado
• SSD melhora performance significativamente"""
        else:
            return """💻 **Delux Modpack em Notebook:**

**✅ FUNCIONA SIM!** 
• Notebook gamer com GTX 1060+ roda perfeitamente
• GTX 1650/1660 também funcionam bem

**📋 REQUISITOS NOTEBOOK:**
• Windows 10/11 64-bit
• 8GB RAM (16GB ideal)
• GPU dedicada GTX 1050 Ti mínima
• 20GB espaço livre
• SSD recomendado para loading

**🎯 DICA PERFORMANCE:**
• Feche programas desnecessários
• Use modo performance na GPU
• Configure ventilação adequada
• Limite FPS se esquentar muito

**Resultado: Roda sim em notebook gamer!**"""
    
    elif categoria == "virus_seguranca":
        return """🛡️ **Delux Modpack é 100% Seguro!**

**✅ GARANTIAS DE SEGURANÇA:**
• Desenvolvido pelo Natan Borges (desenvolvedor confiável)
• Comunidade ativa há anos
• Sem código malicioso
• Links oficiais seguros

**⚠️ POR QUE ANTIVÍRUS ALERTA?**
• Arquivos DLL são "modificadores" de jogos
• Antivírus não conhece a assinatura
• **É FALSO POSITIVO** comum em mods

**🔒 COMO TER CERTEZA:**
• Baixe apenas dos links oficiais
• Use antivírus atualizado
• Adicione exceção temporária
• Desenvolvedor tem reputação estabelecida

**📞 Confiança total:** borgesnatan09@gmail.com"""
    
    # Continua com outras categorias técnicas detalhadas...
    elif categoria == "download":
        if complexidade in ["complexa", "muito_complexa"]:
            return """🎮 **Download Completo Delux Modpack:**

**📥 LINKS OFICIAIS MEDIAFIRE (3 partes obrigatórias):**
• **Parte 1:** https://www.mediafire.com/file/h7qb14ns1rznvj6/Installer(Delux+Real+BETA)+V1+-+part1.rar/file
• **Parte 2:** https://www.mediafire.com/file/90c82qkhqheqbkz/Installer(Delux+Real+BETA)+V1+-+part2.rar/file  
• **Parte 3:** https://www.mediafire.com/file/8rjhj6js44kqqu3/Installer(Delux+Real+BETA)+V1+-+part3.rar/file

**📦 TAMANHOS:**
• Parte 1: ~1.2GB | Parte 2: ~1.1GB | Parte 3: ~800MB
• **Total:** ~3.1GB compactado

**⬇️ PASSO A PASSO DOWNLOAD:**
1. **Baixe TODAS as 3 partes** no mesmo diretório
2. **Não renomeie** os arquivos  
3. **Aguarde completar** todos os downloads
4. **Extraia APENAS** part1.rar (outras vêm automaticamente)
5. **Use WinRAR ou 7-Zip** (recomendado)

**⚠️ PROBLEMAS COMUNS:**
• Link lento: Tente VPN ou horário diferente
• Arquivo corrompido: Baixe novamente
• Antivírus bloqueou: Adicione exceção

**📞 Suporte download:** borgesnatan09@gmail.com"""
        else:
            return """🎮 **Download Rápido Delux Modpack:**

**📥 3 Partes MediaFire (obrigatórias):**
• Part1: https://www.mediafire.com/file/h7qb14ns1rznvj6/
• Part2: https://www.mediafire.com/file/90c82qkhqheqbkz/  
• Part3: https://www.mediafire.com/file/8rjhj6js44kqqu3/

**💡 Dica:** Baixe todas, extraia só a part1.rar!
**📞 Ajuda:** borgesnatan09@gmail.com"""
    
    # Continue implementando outras categorias...
    else:
        # Fallback geral
        if complexidade in ["complexa", "muito_complexa"]:
            return """🎮 **Delux Modpack GTA V - Informações Completas**

**🇧🇷 O QUE É:**
Modpack de roleplay realista brasileiro para GTA V singleplayer, desenvolvido por Natan Borges (@Ntzinnn87). Transforma completamente o jogo em experiência brasileira autêntica.

**🎯 PRINCIPAIS CARACTERÍSTICAS:**
• **Roleplay completo:** Sistemas de fome, sede, sono, trabalho
• **Conteúdo brasileiro:** Carros nacionais, mapas de favelas, NPCs BR
• **Economia realista:** Salários brasileiros, banco funcional
• **Trabalhos:** Uber, entregador, segurança, construção
• **100% gratuito** com suporte em português

**💻 COMPATIBILIDADE:**
• Windows 10/11 + GTA V original
• GTX 1060/RX 580 mínimo
• 8GB RAM (16GB recomendado)

**📞 SUPORTE OFICIAL:**
• Site: deluxgtav.netlify.app
• Instagram: @Ntzinnn87  
• Email: borgesnatan09@gmail.com
• WhatsApp: +55 21 99282-6074"""
        else:
            return """🎮 **Delux Modpack GTA V**

Modpack RP brasileiro gratuito para singleplayer.

**Inclui:** Carros BR, mapas nacionais, sistemas realistas.
**Criador:** Natan Borges (@Ntzinnn87)
**Site:** deluxgtav.netlify.app
**Suporte:** borgesnatan09@gmail.com"""

@app.route('/')
def home():
    return jsonify({
        "sistema": "DeluxAI Expandida - Assistente Especialista Delux Modpack",
        "versao": "2.0 Expandida - Treinamento Completo",
        "modelo": "Gemma 3 1B",
        "desenvolvedor": "Natan Borges",
        "status": "online",
        "cuda_disponivel": CUDA_AVAILABLE,
        "especialidade": "Delux Modpack GTA V",
        "novidades": "Conhecimento expandido + detecção de contexto avançada"
    })

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        pergunta = data.get('message', '').strip()
        
        if not pergunta:
            return jsonify({
                "response": "Por favor, faça uma pergunta sobre o Delux Modpack GTA V! Estou aqui para te ajudar! 🎮",
                "error": "Mensagem vazia"
            }), 400
        
        debug_print(f"👤 Pergunta: {pergunta}")
        
        # Cache check expandido
        pergunta_hash = hashlib.md5(pergunta.encode()).hexdigest()
        if pergunta_hash in CACHE_RESPOSTAS:
            cached = CACHE_RESPOSTAS[pergunta_hash]
            cached['metricas']['cache_hit'] = True
            debug_print("💾 Cache hit expandido!")
            return jsonify({
                "response": cached['resposta'],
                "metricas": cached['metricas'],
                "fonte": "cache_expandido"
            })
        
        # Processamento principal expandido
        resposta, metricas, categoria = processar_gemma3_delux_expandido(pergunta)
        
        if resposta:
            # Cache da resposta
            CACHE_RESPOSTAS[pergunta_hash] = {
                'resposta': resposta,
                'metricas': metricas
            }
            
            # Limita cache a 500 entradas
            if len(CACHE_RESPOSTAS) > 500:
                oldest_key = next(iter(CACHE_RESPOSTAS))
                del CACHE_RESPOSTAS[oldest_key]
            
            return jsonify({
                "response": resposta,
                "metricas": metricas,
                "categoria": categoria,
                "fonte": "gemma3_delux_expandida"
            })
        
        # Fallback expandido
        debug_print("📚 Usando fallback expandido")
        resposta_fallback = resposta_fallback_delux_expandida(pergunta)
        
        metricas_fallback = {
            "tempo_resposta": 0.002,
            "fonte": "fallback_delux_expandida",
            "categoria": detectar_categoria_expandida(pergunta),
            "complexidade": avaliar_complexidade_expandida(pergunta),
            "modelo": "Fallback Delux Expandido",
            "cache_hit": False
        }
        
        return jsonify({
            "response": resposta_fallback,
            "metricas": metricas_fallback,
            "fonte": "fallback_expandido"
        })
        
    except Exception as e:
        debug_print(f"❌ Erro na API expandida: {e}")
        return jsonify({
            "response": "Erro interno. Entre em contato: borgesnatan09@gmail.com ou WhatsApp +55 21 99282-6074",
            "error": str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "delux_ai_status": "online_expandida",
        "versao": "2.0 - Treinamento Expandido Completo", 
        "ollama_disponivel": verificar_ollama(),
        "modelo_ativo": OLLAMA_MODEL,
        "cuda_ativo": CUDA_AVAILABLE,
        "gpu_info": GPU_NAME,
        "especialidade": "Delux Modpack GTA V",
        "cache_entries": len(CACHE_RESPOSTAS),
        "desenvolvedor": "Natan Borges (@Ntzinnn87)",
        "suporte": "borgesnatan09@gmail.com | WhatsApp: +55 21 99282-6074",
        "recursos_expandidos": {
            "categorias_detectadas": 15,
            "niveis_complexidade": 4,
            "conhecimento_expandido": True,
            "respostas_contextuais": True,
            "fallbacks_inteligentes": True
        }
    })

@app.route('/limpar_cache', methods=['POST'])
def limpar_cache():
    global CACHE_RESPOSTAS
    count = len(CACHE_RESPOSTAS)
    CACHE_RESPOSTAS.clear()
    debug_print(f"🗑️ Cache expandido limpo: {count} entradas removidas")
    
    return jsonify({
        "message": f"Cache expandido limpo: {count} entradas removidas",
        "status": "success"
    })

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    """Endpoint para listar todas as categorias detectáveis"""
    return jsonify({
        "categorias_sociais": [
            "saudacao", "despedida", "elogio", "humor", "sobre_ia"
        ],
        "categorias_especificas": [
            "vale_a_pena", "comparacao", "duvida_funcionamento", 
            "notebook_mobile", "virus_seguranca", "remover_desinstalar",
            "atualizacoes_futuro", "multiplayer_online", "modificar_personalizar"
        ],
        "categorias_tecnicas": [
            "download", "instalacao", "problemas", "conteudo", "requisitos"
        ],
        "niveis_complexidade": [
            "simples", "media", "complexa", "muito_complexa"
        ],
        "total_cenarios": 15
    })

@app.route('/testar_categoria', methods=['POST'])
def testar_categoria():
    """Endpoint para testar detecção de categoria"""
    try:
        data = request.get_json()
        pergunta = data.get('message', '').strip()
        
        if not pergunta:
            return jsonify({"error": "Pergunta vazia"}), 400
        
        categoria = detectar_categoria_expandida(pergunta)
        complexidade = avaliar_complexidade_expandida(pergunta)
        
        return jsonify({
            "pergunta": pergunta,
            "categoria_detectada": categoria,
            "complexidade": complexidade,
            "resposta_esperada": "detalhada" if complexidade in ["complexa", "muito_complexa"] else "concisa"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Adicionar mais fallbacks específicos para completar
def resposta_fallback_instalacao_completa(complexidade):
    """Fallback específico para instalação"""
    if complexidade in ["complexa", "muito_complexa"]:
        return """🛠️ **Instalação Completa Passo a Passo Delux Modpack**

**🔧 PRÉ-REQUISITOS OBRIGATÓRIOS:**
1. **GTA V Original** (Steam/Epic/Rockstar) atualizado
2. **Script Hook V** → Baixe em scripthookv.net
3. **OpenIV** → Baixe em openiv.com  
4. **Visual C++ Redistributable 2015-2022**
5. **.NET Framework 4.8**
6. **20GB espaço livre** no disco

**📋 PREPARAÇÃO:**
1. **Feche GTA V** completamente
2. **Desabilite antivírus** temporariamente
3. **Execute tudo como administrador**
4. **Backup do save** do GTA V (Documentos/Rockstar Games)

**⬇️ INSTALAÇÃO PRÉ-REQUISITOS:**
1. **Script Hook V:**
   • Baixe do site oficial scripthookv.net
   • Extraia na pasta raiz do GTA V
   • Arquivos: dinput8.dll, ScriptHookV.dll, NativeTrainer.asi

2. **OpenIV:**  
   • Instale normalmente
   • Configure para "ASI Manager"
   • Instale ASI Loader quando solicitado

3. **Visual C++:**
   • Baixe do site Microsoft
   • Instale todas as versões (2015-2022)

**📦 INSTALAÇÃO MODPACK:**
1. **Baixe as 3 partes** do MediaFire no mesmo diretório
2. **Extraia part1.rar** (outras extraem automaticamente)
3. **Execute Installer.exe como administrador**
4. **Selecione pasta do GTA V** (geralmente C:\Program Files\...)
5. **Aguarde instalação** (5-15 minutos - NÃO INTERROMPA)
6. **Reinicie o computador** após concluir

**🎮 PRIMEIRA EXECUÇÃO:**
1. **Abra GTA V normalmente** (Steam/Epic)
2. **Aguarde carregar** completamente
3. **Novos controles** aparecerão na tela
4. **Siga tutorial RP** inicial

**❗ VERIFICAÇÕES IMPORTANTES:**
• Arquivos DLL na pasta GTA V?
• OpenIV configurado corretamente?
• Antivírus não está bloqueando?
• Executou como administrador?

**📞 Problemas na instalação:** borgesnatan09@gmail.com | WhatsApp: +55 21 99282-6074"""
    else:
        return """🛠️ **Instalação Rápida:**

**Pré-requisitos:**
• GTA V original + Script Hook V + OpenIV

**Passos:**
1. Baixe as 3 partes do modpack
2. Execute installer como administrador  
3. Selecione pasta GTA V
4. Aguarde instalar
5. Reinicie PC

**Suporte:** borgesnatan09@gmail.com"""

def resposta_fallback_problemas_completa(complexidade):
    """Fallback específico para problemas"""
    if complexidade in ["complexa", "muito_complexa"]:
        return """🔧 **Soluções Detalhadas - Problemas Delux Modpack**

**🚫 GAME NÃO ABRE:**
**Causas:** Script Hook V desatualizado, GTA V desatualizado, DLLs bloqueadas
**Soluções:**
1. Baixe Script Hook V mais recente (scripthookv.net)
2. Verifique integridade GTA V (Steam: Propriedades > Arquivos locais > Verificar)
3. Adicione exceção antivírus para pasta GTA V
4. Execute GTA V como administrador
5. Reinstale Visual C++ Redistributable

**💥 CRASHES/TRAVAMENTOS:**
**Causas:** RAM insuficiente, drivers GPU, conflito mods, superaquecimento
**Soluções:**
1. **RAM:** Feche Chrome, Discord, programas pesados
2. **Drivers:** Atualize placa de vídeo (NVIDIA/AMD)
3. **Conflitos:** Remova outros mods temporariamente  
4. **Temperatura:** Monitore com MSI Afterburner
5. **Configurações:** Reduza gráficos no jogo

**🐌 FPS BAIXO/PERFORMANCE:**
**Otimizações:**
1. **Gráficos:** Texturas Altas, Sombras Médias, MSAA 2x
2. **Sistema:** Feche navegador, Discord, Steam overlay
3. **Windows:** Modo performance, desative Xbox Game Bar
4. **Hardware:** Limite FPS, monitore temperatura GPU
5. **SSD:** Mova GTA V para SSD se possível

**❌ MODS NÃO FUNCIONAM:**
**Verificações:**
1. Script Hook V instalado corretamente?
2. Arquivos dinput8.dll na pasta raiz GTA V?
3. OpenIV configurado modo ASI?
4. GTA V é original (não pirata)?
5. Ordem instalação: Pré-requisitos → Modpack

**🔊 SEM ÁUDIO/ÁUDIO BUGADO:**
1. Verifique configurações áudio Windows
2. Reinstale drivers áudio
3. Configure áudio GTA V para Estéreo
4. Teste com fones diferentes

**🎮 CONTROLES BUGADOS:**
1. Use controle Xbox (recomendado)
2. Configure no menu Settings do jogo
3. Desative Steam Input se Steam
4. Teste teclado e mouse alternativos

**📞 SUPORTE PERSONALIZADO:**
Email: borgesnatan09@gmail.com  
WhatsApp: +55 21 99282-6074
**Inclua:** Erro exato, configuração PC, prints se possível"""
    else:
        return """🔧 **Problemas Comuns:**

**Game não abre:** Atualize Script Hook V
**Crashes:** Atualize drivers GPU, feche programas  
**FPS baixo:** Reduza gráficos, feche navegador
**Mods não funcionam:** Verifique OpenIV e DLLs

**Suporte:** borgesnatan09@gmail.com"""

def resposta_fallback_conteudo_completa(complexidade):
    """Fallback específico para conteúdo"""
    if complexidade in ["complexa", "muito_complexa"]:
        return """🎮 **Conteúdo Completo Delux Modpack - Experiência Brasileira Total**

**🚗 VEÍCULOS BRASILEIROS:**
• **Populares:** Gol, Palio, Celta, Fiesta, HB20, Onix
• **Sedãs:** Civic, Corolla, Jetta, Fusion, Cruze  
• **SUVs:** EcoSport, Duster, HR-V, Compass
• **Esportivos:** Camaro, Mustang nacionais
• **Motos:** CG 160, XRE 300, CB 600F, Ninja 400
• **Utilitários:** Hilux, Ranger, S10, Amarok, Strada
• **Transporte:** Ônibus urbanos brasileiros, caminhões nacionais
• **Physics realistas** para todos os veículos

**🗺️ MAPAS E LOCALIDADES:**
• **Rio de Janeiro:** Favelas detalhadas (Rocinha, Cidade de Deus)
• **São Paulo:** Centro expandido, periferias
• **Praias:** Copacabana, Ipanema recriadas
• **Shopping Centers:** Brasileiros funcionais
• **Postos:** BR, Ipiranga, Shell com abastecimento real
• **Bancos:** Bradesco, Itaú, Caixa funcionais
• **Lojas:** Casas Bahia, Magazine Luiza, Americanas

**💼 SISTEMAS DE ROLEPLAY:**
• **Necessidades Básicas:**
  - Fome: Decresce com tempo, afeta saúde e stamina
  - Sede: Mais crítica, necessária a cada 30min jogo
  - Sono: Afeta concentração, precisão ao dirigir
  - Higiene: Sistema opcional, afeta interações NPCs

• **Trabalhos Brasileiros:**
  - **Motorista Uber/99:** Corridas pela cidade, pagamento realista
  - **Entregador iFood/Rappi:** Delivery de comida de moto
  - **Segurança:** Shopping centers, empresas, eventos
  - **Construção:** Pedreiro, soldador, eletricista
  - **Frentista:** Postos BR, atendimento aos clientes
  - **Taxista:** Corridas tradicionais, bandeirada real
  - **Caminhoneiro:** Entregas interestaduais

**💰 ECONOMIA REALISTA:**
• **Salário Mínimo:** R$ 1.320 base para cálculos
• **Preços Reais:** Combustível R$ 5,50/L, alimentos preços BR
• **Sistema Bancário:** Juros, financiamentos, cartão crédito
• **IPVA:** Taxa anual veículos
• **Seguro:** Obrigatório para dirigir
• **Multas:** Radar, estacionamento proibido

**🏠 SISTEMA HABITACIONAL:**
• **Apartamentos:** Populares (R$ 800/mês), classe média (R$ 2.000/mês)
• **Casas:** Periferia até mansões de luxo
• **Financiamento:** Sistema FGTS simulado
• **Decoração:** Móveis brasileiros, eletrodomésticos nacionais
• **Contas:** Luz, água, internet mensais

**👥 NPCS E AMBIENTE:**
• **Aparência:** Roupas brasileiras, diversidade étnica real
• **Comportamento:** Mais educados, cumprimentam
• **Falas:** 100% português brasileiro
• **Tráfego:** Padrões brasileiros, motocicletas frequentes
• **Economia:** Vendedores ambulantes, camelôs

**🎵 ÁUDIO E INTERFACE:**
• **Rádios:** Estações brasileiras (sertanejo, funk, rock nacional)
• **HUD:** Interface moderna em português
• **Sons:** Buzinas brasileiras, motores nacionais
• **Dublagem:** Algumas missões em português

**🌟 DIFERENCIAIS ÚNICOS:**
• Experiência 100% nacional
• Cultura brasileira autêntica
• Gírias e expressões regionais
• Sistemas realistas sem exageros
• Balanceamento para diversão

**📈 EM DESENVOLVIMENTO:**
• Mais cidades brasileiras
• Sistema relacionamentos
• Profissões adicionais  
• Multiplayer cooperativo local"""
    else:
        return """🎮 **Conteúdo Delux Modpack:**

**🚗 Veículos:** Gol, Civic, Corolla, HB20, motos CG/XRE
**🗺️ Mapas:** Favelas RJ, centro SP, praias BR
**💼 Trabalhos:** Uber, entregador, segurança, construção  
**💰 Economia:** Salários BR, banco funcional, IPVA
**🏠 Casas:** Apartamentos até mansões
**👥 NPCs:** Brasileiros, falam português

**Total:** Experiência brasileira completa!"""

if __name__ == '__main__':
    try:
        debug_print("🚀 Iniciando DeluxAI Expandida - Versão Treinamento Completo")
        debug_print(f"📱 Modelo: {OLLAMA_MODEL} (815MB)")
        debug_print(f"🔧 CUDA: {'Ativo' if CUDA_AVAILABLE else 'Inativo'}")
        debug_print(f"👨‍💻 Desenvolvedor: Natan Borges (@Ntzinnn87)")
        debug_print("🎮 Especialidade: Delux Modpack GTA V")
        debug_print("🆕 Novidades: 15 categorias + 4 níveis complexidade")
        debug_print("📚 Conhecimento: Base expandida completa")
        debug_print("🤖 IA: Respostas contextuais inteligentes")
        debug_print("=" * 70)
        
        # Teste do Ollama
        if verificar_ollama():
            debug_print("✅ Ollama conectado e funcionando")
        else:
            debug_print("⚠️ Ollama offline - fallbacks expandidos ativos")
        
        debug_print("🌐 Iniciando servidor Flask expandido...")
        debug_print("📡 Acesse: http://127.0.0.1:5001")
        debug_print("🔍 Endpoints: /chat, /status, /categorias, /testar_categoria")
        debug_print("🛑 Para parar: Ctrl+C")
        debug_print("-" * 70)
        
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        debug_print("\n🛑 DeluxAI Expandida parada pelo usuário")
        debug_print("👋 Obrigada por usar a DeluxAI!")
    except Exception as e:
        debug_print(f"❌ Erro ao iniciar DeluxAI Expandida: {e}")
        debug_print("💡 Verifique dependências: pip install flask flask-cors requests")
        input("Pressione Enter para sair...")
        }
    })