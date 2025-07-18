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
    tipo = next((t for t in tipos if re.search(rf'\b{re.escape(t)}\b', nome_up)), "")
    marca = next((m for m in marcas if re.search(rf'\b{re.escape(m)}\b', nome_up)), "")
    volume = next((v for v in volumes if re.search(rf'\b{re.escape(v)}\b', nome_up)), "")
    
    # Particularidade: só se estiver na lista, como palavra isolada e diferente do volume
    partes_usadas = [tipo, marca, volume]
    particularidade = " ".join([
        p for p in particularidades
        if re.search(rf'\b{re.escape(p)}\b', nome_up) and p not in partes_usadas and p != volume
    ])
    
    # Se particularidade não for identificada, deixar em branco e montar apenas TMV
    if not particularidade:
        campos_tmv = [tipo, marca, volume]
        campos_unicos = [c for c in campos_tmv if c]  # Remove campos vazios
        sugestao = " ".join(campos_unicos).replace("  ", " ").strip()
        return sugestao, {"tipo": tipo, "marca": marca, "particularidade": "", "volume": volume}
    
    # Caso contrário, montar TMPV
    campos = [tipo, marca, particularidade, volume]
    campos_unicos = []
    for c in campos:
        if c and c not in campos_unicos:
            campos_unicos.append(c)
    sugestao = " ".join(campos_unicos).replace("  ", " ").strip()
    return sugestao, {"tipo": tipo, "marca": marca, "particularidade": particularidade, "volume": volume}

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