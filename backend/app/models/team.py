"""
Modelo SQLAlchemy para tabla 'teams'.
Almacena información de equipos de Euroleague.
"""

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Team(Base):
    """
    Modelo de Equipo.
    
    Atributos:
        id: UUID único del equipo
        code: Código corto (RM, BAR, OLM, etc.)
        name: Nombre completo del equipo
        logo_url: URL del logo del equipo
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
    """

    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    logo_url = Column(Text, nullable=True)
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)
    updated_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)

    # Relaciones
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team(code={self.code}, name={self.name})>"

