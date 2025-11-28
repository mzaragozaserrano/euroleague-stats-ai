from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Game(Base):
    """
    Modelo SQLAlchemy para la tabla 'games'.
    Almacena información de partidos/encuentros de la Euroliga.
    """

    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, nullable=False, index=True)
    round = Column(Integer, nullable=False, index=True)
    home_team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    away_team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date = Column(Date, nullable=False, index=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    home_team = relationship(
        "Team",
        foreign_keys=[home_team_id],
        back_populates="home_games",
    )
    away_team = relationship(
        "Team",
        foreign_keys=[away_team_id],
        back_populates="away_games",
    )
    player_stats = relationship("PlayerStats", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id={self.id}, season={self.season}, round={self.round}, date={self.date})>"
