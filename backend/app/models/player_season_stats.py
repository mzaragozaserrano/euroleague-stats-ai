from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey, Decimal
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PlayerSeasonStats(Base):
    """
    Modelo SQLAlchemy para la tabla 'player_season_stats'.
    Almacena estadísticas agregadas de jugadores por temporada.
    
    Estos datos se populan diariamente a las 7 AM desde euroleague_api.
    """

    __tablename__ = "player_season_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    season = Column(String(10), nullable=False, index=True)  # "E2025", "E2024"
    
    # Estadísticas básicas
    games_played = Column(Integer, nullable=True)
    points = Column(Decimal(5, 2), nullable=True, index=True)
    rebounds = Column(Decimal(5, 2), nullable=True, index=True)
    assists = Column(Decimal(5, 2), nullable=True, index=True)
    steals = Column(Decimal(5, 2), nullable=True)
    blocks = Column(Decimal(5, 2), nullable=True)
    turnovers = Column(Decimal(5, 2), nullable=True)
    
    # Tiros
    fg2_made = Column(Decimal(5, 2), nullable=True)
    fg2_attempted = Column(Decimal(5, 2), nullable=True)
    fg3_made = Column(Decimal(5, 2), nullable=True)
    fg3_attempted = Column(Decimal(5, 2), nullable=True)
    ft_made = Column(Decimal(5, 2), nullable=True)
    ft_attempted = Column(Decimal(5, 2), nullable=True)
    
    # Faltas
    fouls_drawn = Column(Integer, nullable=True)
    fouls_committed = Column(Integer, nullable=True)
    
    # Eficiencia
    pir = Column(Decimal(5, 2), nullable=True)  # Performance Index Rating
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    player = relationship("Player", back_populates="season_stats")

    def __repr__(self):
        return f"<PlayerSeasonStats(player_id={self.player_id}, season='{self.season}', points={self.points})>"

