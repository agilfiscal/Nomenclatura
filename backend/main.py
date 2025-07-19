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
    return {"message": "API online"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    from sqlalchemy.future import select
    async with SessionLocal() as session:
        # Buscar listas do banco
        marcas = [m.nome for m in (await session.execute(select(Marca))).scalars().all()]
        tipos = [t.nome for t in (await session.execute(select(Tipo))).scalars().all()]
        particularidades = [p.nome for p in (await session.execute(select(Particularidade))).scalars().all()]
        volumes = [v.nome for v in (await session.execute(select(Volume))).scalars().all()]
        abreviacoes = [{"abreviacao": a.abreviacao, "palavra_completa": a.palavra_completa} for a in (await session.execute(select(Abreviacao))).scalars().all()]

    # Ler o arquivo enviado (CSV ou XLSX)
    content = await file.read()
    filename = file.filename or ''
    if filename.lower().endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
    else:
        df = pd.read_excel(io.BytesIO(content))

    # Verificar se as colunas necessárias existem
    if not set(['nome', 'ean']).issubset(df.columns.str.lower()):
        return JSONResponse(status_code=400, content={"error": "A planilha deve conter as colunas 'nome' e 'ean'"})

    # Normalizar nomes das colunas
    df.columns = [c.lower() for c in df.columns]

    # Processar cada produto e sugerir nome TMPV
    sugestoes = []
    for _, row in df.iterrows():
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

    return {"produtos": sugestoes}


def expandir_abreviacoes(texto: str, abreviacoes: list) -> str:
    """Expande abreviações no texto"""
    texto_expandido = texto.upper()
    for abrev in abreviacoes:
        # Usar regex para substituir apenas palavras completas
        pattern = r'\b' + re.escape(abrev['abreviacao']) + r'\b'
        texto_expandido = re.sub(pattern, abrev['palavra_completa'], texto_expandido)
    return texto_expandido


def sugerir_tmpv(nome: str, tipos, marcas, particularidades, volumes):
    nome_up = nome.upper()
    
    # Buscar tipo, marca e volume (mantém lógica original)
    tipo = next((t for t in tipos if re.search(rf'\b{re.escape(t)}\b', nome_up)), "")
    marca = next((m for m in marcas if re.search(rf'\b{re.escape(m)}\b', nome_up)), "")
    volume = next((v for v in volumes if re.search(rf'\b{re.escape(v)}\b', nome_up)), "")
    
    # Buscar TODAS as particularidades encontradas no nome
    partes_usadas = [tipo, marca, volume]
    particularidade = buscar_todas_particularidades(nome_up, particularidades, partes_usadas)
    
    # Se não encontrou particularidade cadastrada, tentar identificar possíveis particularidades no texto
    sugestoes_particularidades = []
    if not particularidade:
        sugestoes_particularidades = identificar_possiveis_particularidades(nome_up, tipo, marca, volume)
    
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
    
    # Se particularidade não for identificada, deixar em branco e montar apenas TMV
    if not particularidade:
        campos_tmv = [tipo, marca, volume]
        campos_unicos = [c for c in campos_tmv if c]  # Remove campos vazios
        sugestao = " ".join(campos_unicos).replace("  ", " ").strip()
        return sugestao, {
            "tipo": tipo, 
            "marca": marca, 
            "particularidade": "", 
            "volume": volume,
            "confiabilidade": confiabilidade,
            "padrao": "TMV",
            "sugestoes_particularidades": sugestoes_particularidades,
            "detalhes_confiabilidade": detalhes_confiabilidade
        }
    
    # Caso contrário, montar TMPV
    campos = [tipo, marca, particularidade, volume]
    campos_unicos = []
    for c in campos:
        if c and c not in campos_unicos:
            campos_unicos.append(c)
    sugestao = " ".join(campos_unicos).replace("  ", " ").strip()
    return sugestao, {
        "tipo": tipo, 
        "marca": marca, 
        "particularidade": particularidade, 
        "volume": volume,
        "confiabilidade": confiabilidade,
        "padrao": "TMPV",
        "sugestoes_particularidades": [],
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

DATABASE_URL = "sqlite+aiosqlite:///./nomenclatura.db"
engine = create_async_engine(DATABASE_URL, echo=True)
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

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        pass

@app.get("/marcas/")
async def listar_marcas(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Marca))
    return [m.nome for m in result.scalars().all()]

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
    result = await session.execute(select(Tipo))
    return [m.nome for m in result.scalars().all()]

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
    result = await session.execute(select(Particularidade))
    return [m.nome for m in result.scalars().all()]

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
    result = await session.execute(select(Volume))
    return [m.nome for m in result.scalars().all()]

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