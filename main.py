from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, ForeignKey
from sqlalchemy import String as SQLString
from sqlalchemy import Float as SQLFloat
from sqlalchemy import Text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
import time 
import os
from rapidfuzz import fuzz # O Cérebro Inteligente

# ==========================================
# 1. BANCO DE DADOS (Versão Blindada para Deploy)
# ==========================================
# Pega a pasta onde este arquivo está
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Salva o banco na MESMA pasta, sem inventar moda de subir nível
DB_PATH = os.path.join(BASE_DIR, "saberius.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# === MODELOS ===
class UsuarioDB(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(SQLString)
    email = Column(SQLString, unique=True, index=True)
    senha = Column(SQLString) 
    tipo = Column(SQLString)  
    especialidade = Column(SQLString, nullable=True)
    valor_hora = Column(SQLFloat, nullable=True)
    bio = Column(SQLString, nullable=True)
    foto = Column(Text, nullable=True)

class TransacaoDB(Base):
    __tablename__ = "transacoes"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"))
    mentor_id = Column(Integer, ForeignKey("usuarios.id"))
    valor = Column(SQLFloat)
    data = Column(SQLString)

Base.metadata.create_all(bind=engine)

# === GARANTIA DE ADMIN ===
def garantir_admin():
    db = SessionLocal()
    try:
        email_ceo = "ceo@saberius.com"
        foto_padrao = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        ceo = db.query(UsuarioDB).filter(UsuarioDB.email == email_ceo).first()
        if not ceo:
            db.add(UsuarioDB(nome="CEO Roberto", email=email_ceo, senha="admin", tipo="admin", bio="Super Admin", valor_hora=0.0, foto=foto_padrao))
            db.commit()
        else:
            ceo.senha = "admin"
            if not ceo.foto: ceo.foto = foto_padrao
            db.commit()
    except: pass
    finally: db.close()

garantir_admin()

# === API ===
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UsuarioCriar(BaseModel):
    nome: str
    email: str
    senha: str
    tipo: str
    especialidade: Optional[str] = None
    valor_hora: Optional[float] = None
    foto: Optional[str] = None 

class TransacaoCriar(BaseModel):
    mentor_id: int
    valor: float
    data_agendada: str

class PedidoRecomendacao(BaseModel):
    texto_usuario: str

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UsuarioDB).filter(UsuarioDB.email == form_data.username).first()
    if not user or user.senha != form_data.password:
        raise HTTPException(status_code=400, detail="Credenciais inválidas")
    return {"access_token": user.email, "token_type": "bearer", "tipo_usuario": user.tipo, "foto_usuario": user.foto}

@app.post("/usuarios/")
def criar_usuario(user: UsuarioCriar, db: Session = Depends(get_db)):
    if db.query(UsuarioDB).filter(UsuarioDB.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email já existe")
    foto_final = user.foto if user.foto else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    bio_auto = f"Especialista em {user.especialidade}" if user.especialidade else "Novo usuário."
    db_user = UsuarioDB(nome=user.nome, email=user.email, senha=user.senha, tipo=user.tipo, especialidade=user.especialidade, valor_hora=user.valor_hora, bio=bio_auto, foto=foto_final)
    db.add(db_user)
    db.commit()
    return db_user

@app.get("/usuarios/")
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(UsuarioDB).all()

@app.post("/transacoes/")
def criar_transacao(transacao: TransacaoCriar, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    comprador = db.query(UsuarioDB).filter(UsuarioDB.email == token).first()
    if not comprador: raise HTTPException(status_code=401)
    db.add(TransacaoDB(cliente_id=comprador.id, mentor_id=transacao.mentor_id, valor=transacao.valor, data=transacao.data_agendada))
    db.commit()
    return {"status": "sucesso"}

@app.get("/minhas-transacoes/")
def pegar_minhas_transacoes(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    usuario = db.query(UsuarioDB).filter(UsuarioDB.email == token).first()
    if not usuario: raise HTTPException(status_code=401)
    lista_final = []
    if usuario.tipo == 'cliente':
        for c in db.query(TransacaoDB).filter(TransacaoDB.cliente_id == usuario.id).all():
            m = db.query(UsuarioDB).filter(UsuarioDB.id == c.mentor_id).first()
            if m: lista_final.append({"id": c.id, "data": c.data, "valor": c.valor, "nome_outro_lado": m.nome, "tipo_pessoa": "Mentor"})
    return lista_final

@app.get("/admin/resumo/")
def dados_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    admin = db.query(UsuarioDB).filter(UsuarioDB.email == token).first()
    if not admin or admin.tipo != 'admin': raise HTTPException(status_code=403)
    total_m = db.query(UsuarioDB).filter(UsuarioDB.tipo == 'mentor').count()
    vendas = db.query(TransacaoDB).all()
    return {"usuarios": db.query(UsuarioDB).count(), "mentores": total_m, "faturamento": sum([v.valor for v in vendas]), "transacoes": len(vendas)}

# BUSCA FUZZY
@app.post("/recomendacao/")
def recomendar_mentor(pedido: PedidoRecomendacao, db: Session = Depends(get_db)):
    time.sleep(0.5) 
    mentores = db.query(UsuarioDB).filter(UsuarioDB.tipo == 'mentor').all()
    texto_usuario = pedido.texto_usuario.lower()
    melhor_mentor = None
    maior_score = 0
    for m in mentores:
        if m.especialidade:
            score = fuzz.partial_ratio(texto_usuario, m.especialidade.lower())
            if score > 50 and score > maior_score:
                maior_score = score
                melhor_mentor = m
    if melhor_mentor:
        return {"encontrou": True, "nome": melhor_mentor.nome, "especialidade": melhor_mentor.especialidade, "motivo": f"Compatibilidade: {maior_score}%", "id": melhor_mentor.id, "valor": melhor_mentor.valor_hora, "foto": melhor_mentor.foto}
    return {"encontrou": False}