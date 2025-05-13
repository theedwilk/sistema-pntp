from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class TipoOrgao(Base):
    __tablename__ = 'tipos_orgao'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)  # Ex: Município, Poder Executivo, Secretaria, Autarquia
    
    def __repr__(self):
        return f"<TipoOrgao(nome='{self.nome}')>"

class Orgao(Base):
    __tablename__ = 'orgaos'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    tipo_id = Column(Integer, ForeignKey('tipos_orgao.id'))
    uf = Column(String(2))  # Estado (AM, SP, RJ, etc.)
    
    tipo = relationship("TipoOrgao", back_populates="orgaos")
    links = relationship("Link", back_populates="orgao")
    
    def __repr__(self):
        return f"<Orgao(nome='{self.nome}', uf='{self.uf}')>"

class TipoLink(Base):
    __tablename__ = 'tipos_link'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)  # Ex: Site Oficial, Portal Transparência, Site Câmara
    
    def __repr__(self):
        return f"<TipoLink(nome='{self.nome}')>"

class Link(Base):
    __tablename__ = 'links'
    
    id = Column(Integer, primary_key=True)
    orgao_id = Column(Integer, ForeignKey('orgaos.id'))
    tipo_id = Column(Integer, ForeignKey('tipos_link.id'))
    url = Column(String(500), nullable=False)
    ativo = Column(Boolean, default=True)
    ultima_verificacao = Column(String(20))  # Data da última verificação
    
    orgao = relationship("Orgao", back_populates="links")
    tipo = relationship("TipoLink")
    
    def __repr__(self):
        return f"<Link(url='{self.url}')>"

# Adicionar relacionamentos reversos
TipoOrgao.orgaos = relationship("Orgao", back_populates="tipo")