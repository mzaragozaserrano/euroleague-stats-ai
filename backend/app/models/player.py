"""
Modelo SQLAlchemy para tabla 'players'.
Almacena información de jugadores de Euroleague.
"""

from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Player(Base):
    """
    Modelo de Jugador.
    
    Atributos:
        id: UUID único del jugador
        team_id: FK a teams.id
        player_code: Código de jugador de euroleague_api (para matching)
        name: Nombre completo del jugador
        position: Posición (Base, Escolta, Alero, Ala-Pivot, Pivot)
        season: Código de temporada (E2025, E2024, etc.)
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
    """

    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True)
    player_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    position = Column(String(50), nullable=True)  # Base, Escolta, Alero, Ala-Pivot, Pivot
    season = Column(String(10), nullable=False, index=True)  # E2025, E2024, etc.
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)
    updated_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)

    # Relaciones
    team = relationship("Team", back_populates="players")
    season_stats = relationship("PlayerSeasonStats", back_populates="player", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Player(name={self.name}, position={self.position}, team_id={self.team_id})>"

