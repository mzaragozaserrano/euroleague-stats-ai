"""
Modelo SQLAlchemy para tabla 'player_season_stats'.
Almacena estadísticas agregadas de jugadores por temporada.
"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class PlayerSeasonStats(Base):
    """
    Modelo de Estadísticas por Temporada.
    
    Datos agregados de un jugador en una temporada específica.
    Poblado por ETL diario a las 7 AM desde euroleague_api.
    
    Atributos:
        id: UUID único
        player_id: FK a players.id
        season: Código de temporada (E2025, E2024, etc.)
        games_played: Número de partidos jugados
        points: Total de puntos anotados
        rebounds: Total de rebotes
        assists: Total de asistencias
        steals: Total de robos
        blocks: Total de bloqueos
        turnovers: Total de pérdidas
        threePointsMade: Total de triples anotados
        pir: Player Efficiency Rating
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
    """

    __tablename__ = "player_season_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    season = Column(String(10), nullable=False, index=True)  # E2025, E2024, etc.
    games_played = Column(Integer, default=0)
    points = Column(Float, default=0.0)
    rebounds = Column(Float, default=0.0)
    assists = Column(Float, default=0.0)
    steals = Column(Float, default=0.0)
    blocks = Column(Float, default=0.0)
    turnovers = Column(Float, default=0.0)
    threePointsMade = Column(Float, default=0.0)
    pir = Column(Float, default=0.0)
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)
    updated_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)

    # Relaciones
    player = relationship("Player", back_populates="season_stats")

    # Índice compuesto para queries rápidas por temporada + jugador
    __table_args__ = (
        Index("ix_player_season_stats_player_season", "player_id", "season"),
    )

    def __repr__(self):
        return f"<PlayerSeasonStats(player_id={self.player_id}, season={self.season}, points={self.points})>"



