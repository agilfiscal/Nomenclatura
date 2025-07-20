from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
from typing import List, Dict
import io
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, select
import os
import re

app = FastAPI()

# Liberar CORS para o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "service": "nomenclatura-api", "version": "1.0"}

@app.get("/health")
async def health_check():
    """Endpoint de health check para monitoramento"""
    try:
        # Testar conexão com banco
        async with SessionLocal() as session:
            await session.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint otimizado para upload de arquivos com processamento em lotes"""
    from sqlalchemy.future import select
    
    # Verificar tamanho do arquivo (limite de 50MB)
    if file.size and file.size > 50 * 1024 * 1024:
        return JSONResponse(
            status_code=413, 
            content={"error": "Arquivo muito grande. Tamanho máximo: 50MB"}
        )
    
    try:
        # Buscar dados do banco uma única vez
        async with SessionLocal() as session:
            # Buscar listas do banco com timeout
            marcas = [m.nome for m in (await session.execute(select(Marca))).scalars().all()]
            tipos = [t.nome for t in (await session.execute(select(Tipo))).scalars().all()]
            particularidades = [p.nome for p in (await session.execute(select(Particularidade))).scalars().all()]
            volumes = [v.nome for v in (await session.execute(select(Volume))).scalars().all()]
            abreviacoes = [{"abreviacao": a.abreviacao, "palavra_completa": a.palavra_completa} 
                          for a in (await session.execute(select(Abreviacao))).scalars().all()]

        # Ler o arquivo enviado (CSV ou XLSX)
        content = await file.read()
        filename = file.filename or ''
        
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))

        # Verificar se as colunas necessárias existem
        if not set(['nome', 'ean']).issubset(df.columns.str.lower()):
            return JSONResponse(
                status_code=400, 
                content={"error": "A planilha deve conter as colunas 'nome' e 'ean'"}
            )

        # Normalizar nomes das colunas
        df.columns = [c.lower() for c in df.columns]
        
        # Limitar número de produtos (máximo 10.000)
        if len(df) > 10000:
            return JSONResponse(
                status_code=413, 
                content={"error": "Muitos produtos. Máximo permitido: 10.000"}
            )

        # Processar produtos em lotes para melhor performance
        sugestoes = []
        batch_size = 100  # Processar 100 produtos por vez
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            for _, row in batch.iterrows():
                nome = str(row['nome'])
                ean = str(row['ean'])
                
                # Expandir abreviações antes de processar
                nome_expandido = expandir_abreviacoes(nome, abreviacoes)
                sugestao, mapeamento = sugerir_tmpv(nome_expandido, tipos, marcas, particularidades, volumes)
                
                sugestoes.append({
                    "nome_original": nome,
                    "ean": ean,
                    "sugestao_tmpv": sugestao,
                    **mapeamento
                })

        return {
            "produtos": sugestoes,
            "total_processados": len(sugestoes),
            "status": "sucesso"
        }
        
    except Exception as e:
        # Log do erro para debugging
        print(f"Erro no upload: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Erro interno do servidor. Tente novamente."}
        )


def expandir_abreviacoes(texto: str, abreviacoes: list) -> str:
    """Expande abreviações no texto"""
    texto_expandido = texto.upper()
    for abrev in abreviacoes:
        # Usar regex para substituir apenas palavras completas
        pattern = r'\b' + re.escape(abrev['abreviacao']) + r'\b'
        texto_expandido = re.sub(pattern, abrev['palavra_completa'], texto_expandido)
    return texto_expandido

def buscar_tipo_inteligente(nome: str, tipos: list) -> str:
    """
    Busca tipo de forma inteligente, priorizando tipos compostos
    """
    # Ordenar tipos por comprimento (mais longos primeiro)
    tipos_ordenados = sorted(tipos, key=len, reverse=True)
    
    # Primeiro, tentar encontrar tipos compostos (mais específicos)
    for tipo in tipos_ordenados:
        if re.search(rf'\b{re.escape(tipo)}\b', nome):
            return tipo
    
    # Se não encontrou nenhum tipo, retornar vazio
    return ""

def corrigir_erros_ortografia(texto: str) -> str:
    """
    Corrige erros de ortografia comuns em nomes de produtos
    """
    correcoes = {
        # Palavras compostas sem espaço
        'FRUTASVERMELHAS': 'FRUTAS VERMELHAS',
        'FRUTASVERMELHA': 'FRUTAS VERMELHA',
        'FRUTASVERDE': 'FRUTAS VERDE',
        'FRUTASVERDES': 'FRUTAS VERDES',
        'FRUTASAMARELA': 'FRUTAS AMARELA',
        'FRUTASAMARELAS': 'FRUTAS AMARELAS',
        'FRUTASLARANJA': 'FRUTAS LARANJA',
        'FRUTASROXA': 'FRUTAS ROXA',
        'FRUTASROXAS': 'FRUTAS ROXAS',
        'FRUTASROSA': 'FRUTAS ROSA',
        'FRUTASROSAS': 'FRUTAS ROSAS',
        'FRUTASPRETA': 'FRUTAS PRETA',
        'FRUTASPRETAS': 'FRUTAS PRETAS',
        'FRUTASBRANCA': 'FRUTAS BRANCA',
        'FRUTASBRANCAS': 'FRUTAS BRANCAS',
        'FRUTASCINZA': 'FRUTAS CINZA',
        'FRUTASCINZAS': 'FRUTAS CINZAS',
        'FRUTASMARROM': 'FRUTAS MARROM',
        'FRUTASMARROMS': 'FRUTAS MARROMS',
        'FRUTASDOURADA': 'FRUTAS DOURADA',
        'FRUTASDOURADAS': 'FRUTAS DOURADAS',
        'FRUTASPRATEADA': 'FRUTAS PRATEADA',
        'FRUTASPRATEADAS': 'FRUTAS PRATEADAS',
        
        # Outras palavras compostas comuns
        'SUCOFRUTAS': 'SUCO FRUTAS',
        'SUCOFRUTA': 'SUCO FRUTA',
        'AGUAMINERAL': 'AGUA MINERAL',
        'AGUAGASIFICADA': 'AGUA GASIFICADA',
        'AGUANATURAL': 'AGUA NATURAL',
        'CAFESOLUVEL': 'CAFE SOLUVEL',
        'CAFEMOIDO': 'CAFE MOIDO',
        'CAFETORRADO': 'CAFE TORRADO',
        'CHOCOLATEBRANCO': 'CHOCOLATE BRANCO',
        'CHOCOLATEPRETO': 'CHOCOLATE PRETO',
        'CHOCOLATEAMARGO': 'CHOCOLATE AMARGO',
        'CHOCOLATEMEIOAMARGO': 'CHOCOLATE MEIO AMARGO',
        'CHOCOLATEAOLEITE': 'CHOCOLATE AO LEITE',
        'BISCOITOSALGADO': 'BISCOITO SALGADO',
        'BISCOITOSALGADOS': 'BISCOITOS SALGADOS',
        'BISCOITODOÇE': 'BISCOITO DOÇE',
        'BISCOITODOÇES': 'BISCOITOS DOÇES',
        'BISCOITORELLENO': 'BISCOITO RELLENO',
        'BISCOITORELLENOS': 'BISCOITOS RELLENOS',
        'BISCOITOCREAM': 'BISCOITO CREAM',
        'BISCOITOCREAMS': 'BISCOITOS CREAMS',
        'BISCOITOWAFER': 'BISCOITO WAFER',
        'BISCOITOWAFERS': 'BISCOITOS WAFERS',
        'BISCOITOSANDWICH': 'BISCOITO SANDWICH',
        'BISCOITOSANDWICHS': 'BISCOITOS SANDWICHS',
        'BISCOITOMARIA': 'BISCOITO MARIA',
        'BISCOITOMARIAS': 'BISCOITOS MARIAS',
        'BISCOITOMORENA': 'BISCOITO MORENA',
        'BISCOITOMORENAS': 'BISCOITOS MORENAS',
        'BISCOITOCREAMCRACKER': 'BISCOITO CREAM CRACKER',
        'BISCOITOCREAMCRACKERS': 'BISCOITOS CREAM CRACKERS',
        'BISCOITOSALTINE': 'BISCOITO SALTINE',
        'BISCOITOSALTINES': 'BISCOITOS SALTINES',
        'BISCOITOCLUB': 'BISCOITO CLUB',
        'BISCOITOCLUBS': 'BISCOITOS CLUBS',
        'BISCOITOPOLVILHO': 'BISCOITO POLVILHO',
        'BISCOITOPOLVILHOS': 'BISCOITOS POLVILHOS',
        'BISCOITOSEMGLUTEN': 'BISCOITO SEM GLUTEN',
        'BISCOITOSEMGLUTENS': 'BISCOITOS SEM GLUTENS',
        'BISCOITOINTEGRAL': 'BISCOITO INTEGRAL',
        'BISCOITOINTEGRAIS': 'BISCOITOS INTEGRAIS',
        'BISCOITOORGANICO': 'BISCOITO ORGANICO',
        'BISCOITOORGANICOS': 'BISCOITOS ORGANICOS',
        'BISCOITOVEGANO': 'BISCOITO VEGANO',
        'BISCOITOVEGANOS': 'BISCOITOS VEGANOS',
        'BISCOITOSEMLACTOSE': 'BISCOITO SEM LACTOSE',
        'BISCOITOSEMLACTOSES': 'BISCOITOS SEM LACTOSES',
        'BISCOITOSEMACUCAR': 'BISCOITO SEM ACUCAR',
        'BISCOITOSEMACUCARS': 'BISCOITOS SEM ACUCARS',
        'BISCOITOSEMGORDURA': 'BISCOITO SEM GORDURA',
        'BISCOITOSEMGORDURAS': 'BISCOITOS SEM GORDURAS',
        'BISCOITOSEMSODIO': 'BISCOITO SEM SODIO',
        'BISCOITOSEMSODIOS': 'BISCOITOS SEM SODIOS',
        'BISCOITOSEMCOLESTEROL': 'BISCOITO SEM COLESTEROL',
        'BISCOITOSEMCOLESTEROIS': 'BISCOITOS SEM COLESTEROIS',
        'BISCOITOSEMTRANS': 'BISCOITO SEM TRANS',
        'BISCOITOSEMTRANS': 'BISCOITOS SEM TRANS',
    }
    
    texto_corrigido = texto.upper()
    for erro, correcao in correcoes.items():
        texto_corrigido = texto_corrigido.replace(erro, correcao)
    
    return texto_corrigido


def sugerir_tmpv(nome: str, tipos, marcas, particularidades, volumes):
    # Corrigir erros de ortografia antes de processar
    nome_corrigido = corrigir_erros_ortografia(nome)
    nome_up = nome_corrigido.upper()
    
    # Buscar tipo de forma inteligente (priorizar tipos compostos)
    tipo = buscar_tipo_inteligente(nome_up, tipos)
    
    marcas_ordenadas = sorted(marcas, key=len, reverse=True)
    marca = next((m for m in marcas_ordenadas if re.search(rf'\b{re.escape(m)}\b', nome_up)), "")
    
    # Buscar volume cadastrado primeiro (priorizar volumes mais longos)
    volumes_ordenados = sorted(volumes, key=len, reverse=True)
    volume = next((v for v in volumes_ordenados if re.search(rf'\b{re.escape(v)}\b', nome_up)), "")
    
    # Se não encontrou volume cadastrado, tentar identificar possíveis volumes
    if not volume:
        possiveis_volumes = identificar_possiveis_volumes(nome_up, tipo, marca, "")
        if possiveis_volumes:
            volume = possiveis_volumes[0]  # Pegar o primeiro volume identificado
    
    # Buscar TODAS as particularidades encontradas no nome
    partes_usadas = [tipo, marca, volume]
    particularidade = buscar_todas_particularidades(nome_up, particularidades, partes_usadas)
    
    # Identificar sugestões para campos não encontrados
    sugestoes_particularidades = []
    sugestoes_tipos = []
    sugestoes_marcas = []
    sugestoes_volumes = []
    
    # Se não encontrou particularidade cadastrada, tentar identificar possíveis particularidades
    if not particularidade:
        sugestoes_particularidades = identificar_possiveis_particularidades(nome_up, tipo, marca, volume)
    
    # Se não encontrou tipo cadastrado, tentar identificar possíveis tipos
    if not tipo:
        sugestoes_tipos = identificar_possiveis_tipos(nome_up, marca, particularidade, volume)
    
    # Se não encontrou marca cadastrada, tentar identificar possíveis marcas
    if not marca:
        sugestoes_marcas = identificar_possiveis_marcas(nome_up, tipo, particularidade, volume)
    
    # Se não encontrou volume cadastrado, tentar identificar possíveis volumes para sugestões
    if not volume:
        sugestoes_volumes = identificar_possiveis_volumes(nome_up, tipo, marca, particularidade)
    else:
        sugestoes_volumes = []  # Se volume já foi identificado, não mostrar sugestões
    
    # Calcular confiabilidade baseada em campos identificados
    campos_identificados = 0
    total_campos = 0
    
    # Contar campos identificados
    if tipo:
        campos_identificados += 1
    total_campos += 1
    
    if marca:
        campos_identificados += 1
    total_campos += 1
    
    if particularidade:
        campos_identificados += 1
        total_campos += 1  # Só conta se particularidade foi identificada
    
    if volume:
        campos_identificados += 1
    total_campos += 1
    
    # Calcular confiabilidade base inicial
    confiabilidade_base = (campos_identificados / total_campos) * 100 if total_campos > 0 else 0
    
    # Calcular confiabilidade final com fatores adicionais
    resultado_confiabilidade = calcular_confiabilidade_avancada(nome_up, tipo, marca, particularidade, volume, confiabilidade_base)
    confiabilidade = resultado_confiabilidade['confiabilidade']
    detalhes_confiabilidade = resultado_confiabilidade['detalhes']
    
    # Montar sugestão TMPV
    campos = [tipo, marca, particularidade, volume]
    campos_unicos = []
    for c in campos:
        if c and c not in campos_unicos:
            campos_unicos.append(c)
    sugestao = " ".join(campos_unicos).replace("  ", " ").strip()
    
    # Determinar padrão baseado nos campos identificados
    if tipo and marca and particularidade and volume:
        padrao = "TMPV"
    elif tipo and marca and volume:
        padrao = "TMV"
    else:
        padrao = "INCOMPLETO"
    
    return sugestao, {
        "tipo": tipo, 
        "marca": marca, 
        "particularidade": particularidade, 
        "volume": volume,
        "confiabilidade": confiabilidade,
        "padrao": padrao,
        "sugestoes_tipos": sugestoes_tipos,
        "sugestoes_marcas": sugestoes_marcas,
        "sugestoes_particularidades": sugestoes_particularidades,
        "sugestoes_volumes": sugestoes_volumes,
        "detalhes_confiabilidade": detalhes_confiabilidade
    }


def calcular_confiabilidade_avancada(nome_original: str, tipo: str, marca: str, particularidade: str, volume: str, confiabilidade_base: float):
    """
    Calcula confiabilidade avançada considerando:
    1. Quantidade de caracteres do nome original vs sugestão
    2. Quantidade de palavras repetidas
    3. Cobertura de informações do nome original
    """
    # Montar sugestão para comparação
    campos = [tipo, marca, particularidade, volume]
    campos_unicos = []
    for c in campos:
        if c and c not in campos_unicos:
            campos_unicos.append(c)
    sugestao = " ".join(campos_unicos).replace("  ", " ").strip()
    
    # Se não há sugestão válida, retornar confiabilidade baixa
    if not sugestao:
        return {
            'confiabilidade': 0.0,
            'detalhes': {
                'base': confiabilidade_base,
                'fator_chars': 0,
                'fator_palavras_perdidas': 0,
                'fator_palavras_adicionadas': 0,
                'fator_cobertura': 0,
                'fator_estrutura': 0,
                'palavras_perdidas': [],
                'palavras_adicionadas': [],
                'razao_chars': 0
            }
        }
    
    # Fator 1: Comparação de caracteres
    chars_original = len(nome_original.replace(" ", ""))
    chars_sugestao = len(sugestao.replace(" ", ""))
    
    if chars_original > 0:
        razao_chars = chars_sugestao / chars_original
        if razao_chars < 0.5:
            fator_chars = -20  # Penalidade alta se sugestão muito menor
        elif razao_chars < 0.7:
            fator_chars = -10  # Penalidade média
        elif razao_chars < 0.9:
            fator_chars = -5   # Penalidade baixa
        elif razao_chars <= 1.2:
            fator_chars = 0    # Ideal
        else:
            fator_chars = -5   # Penalidade se sugestão muito maior
    else:
        fator_chars = 0
    
    # Fator 2: Análise de palavras perdidas e adicionadas
    palavras_original = set(nome_original.split())
    palavras_sugestao = set(sugestao.split())
    
    # Palavras que aparecem no original mas não na sugestão (informação perdida)
    palavras_perdidas = palavras_original.difference(palavras_sugestao)
    # Palavras que aparecem na sugestão mas não no original (informação adicionada)
    palavras_adicionadas = palavras_sugestao.difference(palavras_original)
    
    # Filtrar palavras importantes perdidas (ignorar artigos, preposições, etc.)
    palavras_importantes_perdidas = []
    palavras_ignoradas = {'DE', 'DA', 'DO', 'DAS', 'DOS', 'COM', 'PARA', 'POR', 'EM', 'NA', 'NO', 'NAS', 'NOS', 'A', 'O', 'AS', 'OS', 'UM', 'UMA', 'E', 'OU', 'MAS', 'SE', 'QUE', 'QUAL', 'QUAIS'}
    
    for palavra in palavras_perdidas:
        if len(palavra) >= 3 and palavra not in palavras_ignoradas:
            palavras_importantes_perdidas.append(palavra)
    
    # Penalizar palavras importantes perdidas (informação importante não capturada)
    fator_palavras_perdidas = -len(palavras_importantes_perdidas) * 8
    
    # Penalizar palavras adicionadas (não deveria adicionar informações)
    fator_palavras_adicionadas = -len(palavras_adicionadas) * 3
    
    # Fator 3: Cobertura de informações importantes
    palavras_importantes = []
    palavras_ignoradas_cobertura = {'PARA', 'COM', 'DE', 'DA', 'DO', 'DAS', 'DOS', 'MAIS', 'SABOR', 'TEMPERO', 'KITANO', 'NORDESTINO'}
    
    for palavra in palavras_original:
        if len(palavra) >= 3 and palavra not in palavras_ignoradas_cobertura:
            palavras_importantes.append(palavra)
    
    palavras_cobertas = 0
    for palavra in palavras_importantes:
        # Verificar se a palavra está na sugestão ou em algum campo identificado
        palavra_coberta = False
        if palavra in sugestao:
            palavra_coberta = True
        else:
            for campo in [tipo, marca, particularidade, volume]:
                if campo and palavra in campo:
                    palavra_coberta = True
                    break
        
        if palavra_coberta:
            palavras_cobertas += 1
    
    if palavras_importantes:
        cobertura = palavras_cobertas / len(palavras_importantes)
        # Penalizar mais severamente baixa cobertura
        if cobertura < 0.5:
            fator_cobertura = -20  # Penalidade alta para baixa cobertura
        elif cobertura < 0.7:
            fator_cobertura = -10  # Penalidade média
        elif cobertura < 0.9:
            fator_cobertura = -5   # Penalidade baixa
        else:
            fator_cobertura = 0    # Boa cobertura
    else:
        fator_cobertura = 0
    
    # Fator 4: Qualidade da estrutura
    fator_estrutura = 0
    if tipo and marca and volume:  # Estrutura básica completa
        fator_estrutura += 5  # Reduzido de 10 para 5
    if particularidade:  # Estrutura avançada
        fator_estrutura += 3  # Reduzido de 5 para 3
    
    # Calcular confiabilidade final
    confiabilidade_final = confiabilidade_base + fator_chars + fator_palavras_perdidas + fator_palavras_adicionadas + fator_cobertura + fator_estrutura
    
    # Limitar entre 0 e 100
    confiabilidade_final = max(0, min(100, confiabilidade_final))
    
    # Retornar confiabilidade e detalhes dos fatores
    return {
        'confiabilidade': round(confiabilidade_final, 1),
        'detalhes': {
            'base': round(confiabilidade_base, 1),
            'fator_chars': fator_chars,
            'fator_palavras_perdidas': fator_palavras_perdidas,
            'fator_palavras_adicionadas': fator_palavras_adicionadas,
            'fator_cobertura': fator_cobertura,
            'fator_estrutura': fator_estrutura,
            'palavras_perdidas': list(palavras_perdidas),
            'palavras_importantes_perdidas': palavras_importantes_perdidas,
            'palavras_adicionadas': list(palavras_adicionadas),
            'razao_chars': round(razao_chars, 2) if chars_original > 0 else 0,
            'cobertura_percentual': round(cobertura * 100, 1) if palavras_importantes else 0
        }
    }


def buscar_particularidade_composta(nome: str, particularidades: list, partes_usadas: list):
    """
    Busca particularidades no nome, incluindo palavras compostas
    Prioriza palavras compostas mais longas sobre palavras individuais
    """
    if not particularidades:
        return ""
    
    # Ordenar particularidades por comprimento (mais longas primeiro)
    # Isso garante que "FARINHA LACTEA" seja encontrada antes de "FARINHA"
    particularidades_ordenadas = sorted(particularidades, key=len, reverse=True)
    
    for particularidade in particularidades_ordenadas:
        # Verificar se a particularidade não está nas partes já usadas
        if particularidade in partes_usadas:
            continue
            
        # Verificar se a particularidade está no nome
        if re.search(rf'\b{re.escape(particularidade)}\b', nome):
            return particularidade
    
    return ""


def buscar_todas_particularidades(nome: str, particularidades: list, partes_usadas: list):
    """
    Busca TODAS as particularidades encontradas no nome
    Retorna uma string com todas as particularidades encontradas, separadas por espaço
    """
    if not particularidades:
        return ""
    
    # Ordenar particularidades por comprimento (mais longas primeiro)
    # Isso garante que "FARINHA LACTEA" seja encontrada antes de "FARINHA"
    particularidades_ordenadas = sorted(particularidades, key=len, reverse=True)
    
    particularidades_encontradas = []
    nome_restante = nome  # Vamos marcar as partes já encontradas para evitar sobreposições
    
    for particularidade in particularidades_ordenadas:
        # Verificar se a particularidade não está nas partes já usadas
        if particularidade in partes_usadas:
            continue
            
        # Verificar se a particularidade está no nome restante
        if re.search(rf'\b{re.escape(particularidade)}\b', nome_restante):
            particularidades_encontradas.append(particularidade)
            
            # Marcar a parte encontrada no nome restante para evitar sobreposições
            # Substituir por espaços para não interferir com outras buscas
            nome_restante = re.sub(rf'\b{re.escape(particularidade)}\b', ' ' * len(particularidade), nome_restante)
    
    # Retornar todas as particularidades encontradas, separadas por espaço
    return " ".join(particularidades_encontradas)


def identificar_possiveis_particularidades(nome: str, tipo: str, marca: str, volume: str):
    """
    Identifica possíveis particularidades no nome do produto que não estão cadastradas
    Inclui suporte para palavras compostas
    """
    # Palavras que devem ser ignoradas (artigos, preposições, etc.)
    palavras_ignoradas = {
        'DE', 'DA', 'DO', 'DAS', 'DOS', 'COM', 'PARA', 'POR', 'EM', 'NA', 'NO', 'NAS', 'NOS',
        'A', 'O', 'AS', 'OS', 'UM', 'UMA', 'E', 'OU', 'MAS', 'SE', 'QUE', 'QUAL', 'QUAIS',
        'MAIS', 'SABOR', 'TEMPERO', 'KITANO', 'NORDESTINO'  # Palavras comuns que não são particularidades
    }
    
    possiveis_particularidades = []
    
    # 1. Buscar palavras compostas (2-4 palavras consecutivas)
    palavras = nome.split()
    for i in range(len(palavras)):
        # Tentar combinações de 2 a 4 palavras
        for j in range(2, min(5, len(palavras) - i + 1)):
            combinacao = ' '.join(palavras[i:i+j])
            
            # Verificar se a combinação é válida
            if (len(combinacao) >= 3 and 
                combinacao not in [tipo, marca, volume] and
                not any(palavra in palavras_ignoradas for palavra in combinacao.split()) and
                not re.match(r'^\d+[A-Z]*$', combinacao)):
                
                possiveis_particularidades.append(combinacao)
    
    # 2. Buscar palavras individuais (mantém lógica original)
    palavras_individuais = re.findall(r'\b[A-Z]+\b', nome)
    
    for palavra in palavras_individuais:
        palavra_limpa = palavra.strip()
        
        # Ignorar palavras muito curtas (menos de 3 letras)
        if len(palavra_limpa) < 3:
            continue
            
        # Ignorar palavras já usadas (tipo, marca, volume)
        if palavra_limpa in [tipo, marca, volume]:
            continue
            
        # Ignorar palavras na lista de ignoradas
        if palavra_limpa in palavras_ignoradas:
            continue
            
        # Ignorar números e medidas
        if re.match(r'^\d+[A-Z]*$', palavra_limpa):
            continue
            
        # Se passou por todos os filtros, pode ser uma particularidade
        possiveis_particularidades.append(palavra_limpa)
    
    # Remover duplicatas e ordenar por comprimento (mais longas primeiro)
    possiveis_unicas = list(set(possiveis_particularidades))
    return sorted(possiveis_unicas, key=len, reverse=True)


def identificar_possiveis_tipos(nome: str, marca: str, particularidade: str, volume: str):
    """
    Identifica possíveis tipos no nome do produto que não estão cadastrados
    """
    # Palavras que devem ser ignoradas (artigos, preposições, etc.)
    palavras_ignoradas = {
        'DE', 'DA', 'DO', 'DAS', 'DOS', 'COM', 'PARA', 'POR', 'EM', 'NA', 'NO', 'NAS', 'NOS',
        'A', 'O', 'AS', 'OS', 'UM', 'UMA', 'E', 'OU', 'MAS', 'SE', 'QUE', 'QUAL', 'QUAIS',
        'MAIS', 'SABOR', 'TEMPERO', 'KITANO', 'NORDESTINO', 'PREMIUM', 'TRADICIONAL'
    }
    
    possiveis_tipos = []
    
    # 1. Buscar palavras compostas (2-3 palavras consecutivas)
    palavras = nome.split()
    for i in range(len(palavras)):
        # Tentar combinações de 2 a 3 palavras
        for j in range(2, min(4, len(palavras) - i + 1)):
            combinacao = ' '.join(palavras[i:i+j])
            
            # Verificar se a combinação é válida
            if (len(combinacao) >= 3 and 
                combinacao not in [marca, particularidade, volume] and
                not any(palavra in palavras_ignoradas for palavra in combinacao.split()) and
                not re.match(r'^\d+[A-Z]*$', combinacao)):
                
                possiveis_tipos.append(combinacao)
    
    # 2. Buscar palavras individuais
    palavras_individuais = re.findall(r'\b[A-Z]+\b', nome)
    
    for palavra in palavras_individuais:
        palavra_limpa = palavra.strip()
        
        # Ignorar palavras muito curtas (menos de 3 letras)
        if len(palavra_limpa) < 3:
            continue
            
        # Ignorar palavras já usadas (marca, particularidade, volume)
        if palavra_limpa in [marca, particularidade, volume]:
            continue
            
        # Ignorar palavras na lista de ignoradas
        if palavra_limpa in palavras_ignoradas:
            continue
            
        # Ignorar números e medidas
        if re.match(r'^\d+[A-Z]*$', palavra_limpa):
            continue
            
        # Se passou por todos os filtros, pode ser um tipo
        possiveis_tipos.append(palavra_limpa)
    
    # Remover duplicatas e ordenar por comprimento (mais longas primeiro)
    possiveis_unicos = list(set(possiveis_tipos))
    return sorted(possiveis_unicos, key=len, reverse=True)


def identificar_possiveis_marcas(nome: str, tipo: str, particularidade: str, volume: str):
    """
    Identifica possíveis marcas no nome do produto que não estão cadastradas
    """
    # Palavras que devem ser ignoradas (artigos, preposições, etc.)
    palavras_ignoradas = {
        'DE', 'DA', 'DO', 'DAS', 'DOS', 'COM', 'PARA', 'POR', 'EM', 'NA', 'NO', 'NAS', 'NOS',
        'A', 'O', 'AS', 'OS', 'UM', 'UMA', 'E', 'OU', 'MAS', 'SE', 'QUE', 'QUAL', 'QUAIS',
        'MAIS', 'SABOR', 'TEMPERO', 'PREMIUM', 'TRADICIONAL', 'INTEGRAL', 'ORGANICO'
    }
    
    possiveis_marcas = []
    
    # 1. Buscar palavras compostas (2-3 palavras consecutivas)
    palavras = nome.split()
    for i in range(len(palavras)):
        # Tentar combinações de 2 a 3 palavras
        for j in range(2, min(4, len(palavras) - i + 1)):
            combinacao = ' '.join(palavras[i:i+j])
            
            # Verificar se a combinação é válida
            if (len(combinacao) >= 3 and 
                combinacao not in [tipo, particularidade, volume] and
                not any(palavra in palavras_ignoradas for palavra in combinacao.split()) and
                not re.match(r'^\d+[A-Z]*$', combinacao)):
                
                possiveis_marcas.append(combinacao)
    
    # 2. Buscar palavras individuais
    palavras_individuais = re.findall(r'\b[A-Z]+\b', nome)
    
    for palavra in palavras_individuais:
        palavra_limpa = palavra.strip()
        
        # Ignorar palavras muito curtas (menos de 3 letras)
        if len(palavra_limpa) < 3:
            continue
            
        # Ignorar palavras já usadas (tipo, particularidade, volume)
        if palavra_limpa in [tipo, particularidade, volume]:
            continue
            
        # Ignorar palavras na lista de ignoradas
        if palavra_limpa in palavras_ignoradas:
            continue
            
        # Ignorar números e medidas
        if re.match(r'^\d+[A-Z]*$', palavra_limpa):
            continue
            
        # Se passou por todos os filtros, pode ser uma marca
        possiveis_marcas.append(palavra_limpa)
    
    # Remover duplicatas e ordenar por comprimento (mais longas primeiro)
    possiveis_unicas = list(set(possiveis_marcas))
    return sorted(possiveis_unicas, key=len, reverse=True)


def identificar_possiveis_volumes(nome: str, tipo: str, marca: str, particularidade: str):
    """
    Identifica possíveis volumes no nome do produto que não estão cadastrados
    """
    possiveis_volumes = []
    
    # Buscar padrões de volume (números + unidades) incluindo decimais
    # Agora também captura volumes sem espaço (ex: FERTIL150G)
    padroes_volume = [
        r'\b\d+[,.]?\d*\s*ML\b',  # 350ML, 500 ML, 1,2ML, 2.5ML
        r'\b\d+[,.]?\d*\s*L\b',   # 1L, 2 L, 1,2L, 2.5L
        r'\b\d+[,.]?\d*\s*G\b',   # 90G, 500 G, 1,5G, 2.5G, 37,5G
        r'\b\d+[,.]?\d*\s*KG\b',  # 1KG, 2 KG, 1,5KG, 2.5KG
        r'\b\d+[,.]?\d*\s*MG\b',  # 100MG, 500 MG, 1,5MG, 2.5MG
        r'\b\d+[,.]?\d*\s*CL\b',  # 33CL, 50 CL, 1,5CL, 2.5CL
        # Padrões sem espaço (ex: FERTIL150G, PRODUTO500ML)
        r'\b[A-Z]+\d+[,.]?\d*[A-Z]+\b',  # FERTIL150G, PRODUTO500ML
    ]
    
    for padrao in padroes_volume:
        matches = re.findall(padrao, nome, re.IGNORECASE)
        for match in matches:
            # Para padrões sem espaço, extrair apenas a parte do volume
            if re.match(r'^[A-Z]+\d+[,.]?\d*[A-Z]+$', match, re.IGNORECASE):
                # Extrair a parte numérica + unidade
                volume_match = re.search(r'\d+[,.]?\d*[A-Z]+$', match, re.IGNORECASE)
                if volume_match:
                    volume_limpo = volume_match.group().upper()
                else:
                    continue
            else:
                volume_limpo = match.strip().upper()
            
            if volume_limpo not in [tipo, marca, particularidade]:
                possiveis_volumes.append(volume_limpo)
    
    # Buscar volumes que não seguem padrão exato mas podem ser válidos
    palavras = nome.split()
    for palavra in palavras:
        palavra_limpa = palavra.strip().upper()
        
        # Verificar se parece ser um volume (incluindo decimais)
        if (re.match(r'^\d+[,.]?\d*[A-Z]+$', palavra_limpa) and
            palavra_limpa not in [tipo, marca, particularidade] and
            len(palavra_limpa) >= 2):
            
            possiveis_volumes.append(palavra_limpa)
    
    # Remover duplicatas e ordenar por comprimento (mais longas primeiro)
    possiveis_unicos = list(set(possiveis_volumes))
    return sorted(possiveis_unicos, key=len, reverse=True)

DATABASE_URL = "sqlite+aiosqlite:///./nomenclatura.db"
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,  # Desabilitar logs SQL em produção
    pool_size=10,  # Pool de conexões
    max_overflow=20,  # Conexões extras permitidas
    pool_pre_ping=True,  # Verificar conexões antes de usar
    pool_recycle=3600,  # Reciclar conexões a cada hora
    connect_args={"timeout": 30}  # Timeout de conexão
)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Modelos
class Marca(Base):
    __tablename__ = 'marcas'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)

class Tipo(Base):
    __tablename__ = 'tipos'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)

class Particularidade(Base):
    __tablename__ = 'particularidades'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)

class Volume(Base):
    __tablename__ = 'volumes'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)

class Abreviacao(Base):
    __tablename__ = 'abreviacoes'
    id = Column(Integer, primary_key=True, index=True)
    abreviacao = Column(String, unique=True, index=True)
    palavra_completa = Column(String, index=True)

# Inicializar banco
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Função utilitária para adicionar itens
async def add_item(session, model, nome):
    nome = nome.strip().upper()
    if not nome:
        return None
    
    try:
        # Verificar se já existe
        existing = await session.execute(select(model).where(model.nome == nome))
        if existing.scalar_one_or_none():
            return existing.scalar_one()  # Retorna o item existente
        
        # Se não existe, criar novo
        obj = model(nome=nome)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj
    except Exception as e:
        await session.rollback()
        # Em caso de erro, tentar buscar o item existente novamente
        try:
            existing = await session.execute(select(model).where(model.nome == nome))
            if existing.scalar_one_or_none():
                return existing.scalar_one()
        except:
            pass
        # Se ainda não conseguiu encontrar, retorna None
        return None

# Função utilitária para importar TXT
async def import_txt(session, model, file: UploadFile):
    content = await file.read()
    linhas = content.decode('utf-8').splitlines()
    adicionados = []
    ja_existiam = []
    
    for linha in linhas:
        linha_limpa = linha.strip()
        if not linha_limpa:
            continue
            
        # Verificar se já existe
        existing = await session.execute(select(model).where(model.nome == linha_limpa.upper()))
        if existing.scalar_one_or_none():
            ja_existiam.append(linha_limpa.upper())
        else:
            # Se não existe, adicionar
            obj = model(nome=linha_limpa.upper())
            session.add(obj)
            try:
                await session.commit()
                await session.refresh(obj)
                adicionados.append(obj.nome)
            except Exception:
                await session.rollback()
                # Se falhou, provavelmente já existe
                ja_existiam.append(linha_limpa.upper())
    
    return {
        "adicionados": adicionados,
        "ja_existiam": ja_existiam,
        "total_processados": len(linhas)
    }

# Endpoints para cada entidade
from fastapi import Depends

async def get_session():
    """Dependency para gerenciar sessões do banco de dados"""
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()  # Fechar sessão adequadamente

@app.get("/marcas/")
async def listar_marcas(session: AsyncSession = Depends(get_session)):
    """Lista marcas com cache e otimização"""
    try:
        result = await session.execute(select(Marca.nome))
        return [m for m in result.scalars().all()]
    except Exception as e:
        print(f"Erro ao listar marcas: {e}")
        return []

@app.post("/marcas/")
async def adicionar_marca(nome: str = Form(...), session: AsyncSession = Depends(get_session)):
    obj = await add_item(session, Marca, nome)
    return {"adicionado": obj.nome if obj else None, "status": "adicionado" if obj else "já_existia"}

@app.post("/marcas/importar/")
async def importar_marcas(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    resultado = await import_txt(session, Marca, file)
    return resultado

# Repetir para tipos, particularidades e volumes
@app.get("/tipos/")
async def listar_tipos(session: AsyncSession = Depends(get_session)):
    """Lista tipos com cache e otimização"""
    try:
        result = await session.execute(select(Tipo.nome))
        return [t for t in result.scalars().all()]
    except Exception as e:
        print(f"Erro ao listar tipos: {e}")
        return []

@app.post("/tipos/")
async def adicionar_tipo(nome: str = Form(...), session: AsyncSession = Depends(get_session)):
    obj = await add_item(session, Tipo, nome)
    return {"adicionado": obj.nome if obj else None, "status": "adicionado" if obj else "já_existia"}

@app.post("/tipos/importar/")
async def importar_tipos(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    resultado = await import_txt(session, Tipo, file)
    return resultado

@app.get("/particularidades/")
async def listar_particularidades(session: AsyncSession = Depends(get_session)):
    """Lista particularidades com cache e otimização"""
    try:
        result = await session.execute(select(Particularidade.nome))
        return [p for p in result.scalars().all()]
    except Exception as e:
        print(f"Erro ao listar particularidades: {e}")
        return []

@app.post("/particularidades/")
async def adicionar_particularidade(nome: str = Form(...), session: AsyncSession = Depends(get_session)):
    obj = await add_item(session, Particularidade, nome)
    return {"adicionado": obj.nome if obj else None, "status": "adicionado" if obj else "já_existia"}

@app.post("/particularidades/importar/")
async def importar_particularidades(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    resultado = await import_txt(session, Particularidade, file)
    return resultado

@app.get("/volumes/")
async def listar_volumes(session: AsyncSession = Depends(get_session)):
    """Lista volumes com cache e otimização"""
    try:
        result = await session.execute(select(Volume.nome))
        return [v for v in result.scalars().all()]
    except Exception as e:
        print(f"Erro ao listar volumes: {e}")
        return []

@app.post("/volumes/")
async def adicionar_volume(nome: str = Form(...), session: AsyncSession = Depends(get_session)):
    obj = await add_item(session, Volume, nome)
    return {"adicionado": obj.nome if obj else None, "status": "adicionado" if obj else "já_existia"}

@app.post("/volumes/importar/")
async def importar_volumes(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    resultado = await import_txt(session, Volume, file)
    return resultado

# Endpoints para abreviações
@app.get("/abreviacoes/")
async def listar_abreviacoes(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Abreviacao))
    return [{"id": a.id, "abreviacao": a.abreviacao, "palavra_completa": a.palavra_completa} for a in result.scalars().all()]

@app.post("/abreviacoes/")
async def adicionar_abreviacao(abreviacao: str = Form(...), palavra_completa: str = Form(...), session: AsyncSession = Depends(get_session)):
    abreviacao_upper = abreviacao.strip().upper()
    palavra_completa_upper = palavra_completa.strip().upper()
    
    if not abreviacao_upper or not palavra_completa_upper:
        return {"adicionado": None, "status": "erro", "mensagem": "Campos não podem estar vazios"}
    
    # Verificar se já existe
    existing = await session.execute(select(Abreviacao).where(Abreviacao.abreviacao == abreviacao_upper))
    if existing.scalar_one_or_none():
        return {"adicionado": None, "status": "já_existia", "mensagem": "Abreviação já existe"}
    
    # Criar nova abreviação
    obj = Abreviacao(abreviacao=abreviacao_upper, palavra_completa=palavra_completa_upper)
    session.add(obj)
    try:
        await session.commit()
        await session.refresh(obj)
        return {"adicionado": {"abreviacao": obj.abreviacao, "palavra_completa": obj.palavra_completa}, "status": "adicionado"}
    except Exception:
        await session.rollback()
        return {"adicionado": None, "status": "erro", "mensagem": "Erro ao adicionar abreviação"}

@app.delete("/abreviacoes/{abreviacao_id}")
async def remover_abreviacao(abreviacao_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Abreviacao).where(Abreviacao.id == abreviacao_id))
    obj = result.scalar_one_or_none()
    if not obj:
        return {"status": "erro", "mensagem": "Abreviação não encontrada"}
    
    try:
        await session.delete(obj)
        await session.commit()
        return {"status": "removido", "mensagem": "Abreviação removida com sucesso"}
    except Exception:
        await session.rollback()
        return {"status": "erro", "mensagem": "Erro ao remover abreviação"}

@app.post("/abreviacoes/inicializar/")
async def inicializar_abreviacoes(session: AsyncSession = Depends(get_session)):
    """Inicializa com abreviações comuns"""
    abreviacoes_padrao = [
        ("CERV", "CERVEJA"),
        ("C/", "COM"),
        ("REFRIG", "REFRIGERANTE"),
        ("CHOC", "CHOCOLATE"),
        ("CERVEJ", "CERVEJA"),
        ("REFRIGER", "REFRIGERANTE"),
        ("CHOCOL", "CHOCOLATE"),
        ("ACUC", "ACUCAR"),
        ("ARRO", "ARROZ"),
        ("FEIJ", "FEIJAO"),
        ("CAF", "CAFE"),
        ("CAFE", "CAFE"),
        ("LT", "LATA"),
        ("ML", "MILILITROS"),
        ("KG", "QUILOGRAMA"),
        ("G", "GRAMA")
    ]
    
    adicionadas = 0
    ja_existiam = 0
    
    for abrev, palavra in abreviacoes_padrao:
        # Verificar se já existe
        existing = await session.execute(select(Abreviacao).where(Abreviacao.abreviacao == abrev))
        if existing.scalar_one_or_none():
            ja_existiam += 1
            continue
        
        # Adicionar nova abreviação
        obj = Abreviacao(abreviacao=abrev, palavra_completa=palavra)
        session.add(obj)
        try:
            await session.commit()
            await session.refresh(obj)
            adicionadas += 1
        except Exception:
            await session.rollback()
            ja_existiam += 1
    
    return {
        "adicionadas": adicionadas,
        "ja_existiam": ja_existiam,
        "total_processadas": len(abreviacoes_padrao)
    }


@app.post("/particularidades/sugerir/")
async def cadastrar_particularidade_sugerida(nome: str = Form(...), session: AsyncSession = Depends(get_session)):
    """Cadastra uma particularidade sugerida pelo sistema"""
    nome_upper = nome.strip().upper()
    
    if not nome_upper:
        return {"status": "erro", "mensagem": "Nome não pode estar vazio"}
    
    # Verificar se já existe
    existing = await session.execute(select(Particularidade).where(Particularidade.nome == nome_upper))
    if existing.scalar_one_or_none():
        return {"status": "já_existia", "mensagem": "Particularidade já existe no banco"}
    
    # Cadastrar nova particularidade
    obj = Particularidade(nome=nome_upper)
    session.add(obj)
    try:
        await session.commit()
        await session.refresh(obj)
        return {
            "status": "adicionado", 
            "mensagem": "Particularidade cadastrada com sucesso",
            "particularidade": obj.nome
        }
    except Exception as e:
        await session.rollback()
        return {"status": "erro", "mensagem": f"Erro ao cadastrar particularidade: {str(e)}"}


@app.post("/tipos/sugerir/")
async def cadastrar_tipo_sugerido(nome: str = Form(...), session: AsyncSession = Depends(get_session)):
    """Cadastra um tipo sugerido pelo sistema"""
    nome_upper = nome.strip().upper()
    
    if not nome_upper:
        return {"status": "erro", "mensagem": "Nome não pode estar vazio"}
    
    # Verificar se já existe
    existing = await session.execute(select(Tipo).where(Tipo.nome == nome_upper))
    if existing.scalar_one_or_none():
        return {"status": "já_existia", "mensagem": "Tipo já existe no banco"}
    
    # Cadastrar novo tipo
    obj = Tipo(nome=nome_upper)
    session.add(obj)
    try:
        await session.commit()
        await session.refresh(obj)
        return {
            "status": "adicionado", 
            "mensagem": "Tipo cadastrado com sucesso",
            "tipo": obj.nome
        }
    except Exception as e:
        await session.rollback()
        return {"status": "erro", "mensagem": f"Erro ao cadastrar tipo: {str(e)}"}


@app.post("/marcas/sugerir/")
async def cadastrar_marca_sugerida(nome: str = Form(...), session: AsyncSession = Depends(get_session)):
    """Cadastra uma marca sugerida pelo sistema"""
    nome_upper = nome.strip().upper()
    
    if not nome_upper:
        return {"status": "erro", "mensagem": "Nome não pode estar vazio"}
    
    # Verificar se já existe
    existing = await session.execute(select(Marca).where(Marca.nome == nome_upper))
    if existing.scalar_one_or_none():
        return {"status": "já_existia", "mensagem": "Marca já existe no banco"}
    
    # Cadastrar nova marca
    obj = Marca(nome=nome_upper)
    session.add(obj)
    try:
        await session.commit()
        await session.refresh(obj)
        return {
            "status": "adicionado", 
            "mensagem": "Marca cadastrada com sucesso",
            "marca": obj.nome
        }
    except Exception as e:
        await session.rollback()
        return {"status": "erro", "mensagem": f"Erro ao cadastrar marca: {str(e)}"}


@app.post("/volumes/sugerir/")
async def cadastrar_volume_sugerido(nome: str = Form(...), session: AsyncSession = Depends(get_session)):
    """Cadastra um volume sugerido pelo sistema"""
    nome_upper = nome.strip().upper()
    
    if not nome_upper:
        return {"status": "erro", "mensagem": "Nome não pode estar vazio"}
    
    # Verificar se já existe
    existing = await session.execute(select(Volume).where(Volume.nome == nome_upper))
    if existing.scalar_one_or_none():
        return {"status": "já_existia", "mensagem": "Volume já existe no banco"}
    
    # Cadastrar novo volume
    obj = Volume(nome=nome_upper)
    session.add(obj)
    try:
        await session.commit()
        await session.refresh(obj)
        return {
            "status": "adicionado", 
            "mensagem": "Volume cadastrado com sucesso",
            "volume": obj.nome
        }
    except Exception as e:
        await session.rollback()
        return {"status": "erro", "mensagem": f"Erro ao cadastrar volume: {str(e)}"} 