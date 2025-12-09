"""
Modelo SQLAlchemy para tabla 'games'.
Almacena metadatos de los partidos.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class Game(Base):
    """
    Modelo de Partido.
    
    Almacena información general de cada partido.
    
    Atributos:
        id: UUID único
        game_code: Código del partido en Euroleague (ej: 1, 2, 3...)
        season: Temporada (ej: 2024, 2025)
        round: Número de jornada
        date: Fecha y hora del partido
        home_team_id: FK a teams.id (local)
        away_team_id: FK a teams.id (visitante)
        home_score: Puntos del equipo local
        away_score: Puntos del equipo visitante
    """

    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_code = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False, index=True)
    round = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=True)
    
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    home_score = Column(Integer, default=0)
    away_score = Column(Integer, default=0)
    
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)
    updated_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)

    # Relaciones
    home_team = relationship("Team", foreign_keys=[home_team_id], backref="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], backref="away_games")
    player_stats = relationship("PlayerGameStats", back_populates="game")

    # Unicidad: season + game_code
    __table_args__ = (
        UniqueConstraint('season', 'game_code', name='uq_game_season_code'),
        Index("ix_games_season_round", "season", "round"),
    )

    def __repr__(self):
        return f"<Game(season={self.season}, code={self.game_code}, round={self.round})>"

