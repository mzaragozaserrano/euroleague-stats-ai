"""
Modelo SQLAlchemy para tabla 'player_stats_games'.
Almacena estadísticas de jugadores por partido (Box Score).
"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class PlayerGameStats(Base):
    """
    Modelo de Estadísticas por Partido (Box Score).
    
    Datos detallados de un jugador en un partido específico.
    
    Atributos:
        id: UUID único
        game_id: FK a games.id
        player_id: FK a players.id
        team_id: FK a teams.id (equipo con el que jugó)
        minutes: Minutos jugados (formato "MM:SS" o minutos decimales?) -> Usaremos string "MM:SS" de la API
        points: Puntos
        rebounds: Rebotes totales
        assists: Asistencias
        steals: Robos
        blocks: Tapones
        turnovers: Pérdidas
        pir: Valoración
        is_starter: Si fue titular (True/False)
    """

    __tablename__ = "player_stats_games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    minutes = Column(String(10), nullable=True) # "25:30"
    points = Column(Integer, default=0)
    rebounds = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    steals = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    turnovers = Column(Integer, default=0)
    
    # Tiros
    two_points_made = Column(Integer, default=0)
    two_points_attempted = Column(Integer, default=0)
    three_points_made = Column(Integer, default=0)
    three_points_attempted = Column(Integer, default=0)
    free_throws_made = Column(Integer, default=0)
    free_throws_attempted = Column(Integer, default=0)
    
    offensive_rebounds = Column(Integer, default=0)
    defensive_rebounds = Column(Integer, default=0)
    
    fouls_committed = Column(Integer, default=0)
    fouls_drawn = Column(Integer, default=0)
    
    pir = Column(Float, default=0.0)
    is_starter = Column(Boolean, default=False)
    
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)
    updated_at = Column(String(50), default=lambda: datetime.utcnow().isoformat(), nullable=False)

    # Relaciones
    game = relationship("Game", back_populates="player_stats")
    player = relationship("Player", backref="game_stats")
    team = relationship("Team", backref="player_game_stats")

    # Índices
    __table_args__ = (
        Index("ix_player_stats_games_player_game", "player_id", "game_id"),
        Index("ix_player_stats_games_game_team", "game_id", "team_id"),
    )

    def __repr__(self):
        return f"<PlayerGameStats(player_id={self.player_id}, game_id={self.game_id}, points={self.points})>"



