from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PlayerStats(Base):
    """
    Modelo SQLAlchemy para la tabla 'player_stats_games'.
    Almacena estadísticas granulares de jugadores por partido (box score).
    """

    __tablename__ = "player_stats_games"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Estadísticas básicas
    minutes = Column(Integer, nullable=True)
    points = Column(Integer, nullable=True)
    rebounds_total = Column(Integer, nullable=True)
    assists = Column(Integer, nullable=True)
    steals = Column(Integer, nullable=True)
    blocks = Column(Integer, nullable=True)
    turnovers = Column(Integer, nullable=True)

    # Estadísticas de tiros
    fg2_made = Column(Integer, nullable=True)  # 2-pointers made
    fg2_attempted = Column(Integer, nullable=True)  # 2-pointers attempted
    fg3_made = Column(Integer, nullable=True)  # 3-pointers made
    fg3_attempted = Column(Integer, nullable=True)  # 3-pointers attempted
    ft_made = Column(Integer, nullable=True)  # Free throws made
    ft_attempted = Column(Integer, nullable=True)  # Free throws attempted

    # Faltas
    fouls_drawn = Column(Integer, nullable=True)
    fouls_committed = Column(Integer, nullable=True)

    # Índice calculado
    pir = Column(Numeric(5, 2), nullable=True)  # Performance Index Rating

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    game = relationship("Game", back_populates="player_stats")
    player = relationship("Player", back_populates="player_stats")
    team = relationship("Team", back_populates="player_stats")

    def __repr__(self):
        return f"<PlayerStats(id={self.id}, game_id={self.game_id}, player_id={self.player_id}, points={self.points})>"
