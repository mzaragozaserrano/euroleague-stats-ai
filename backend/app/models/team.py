from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Team(Base):
    """
    Modelo SQLAlchemy para la tabla 'teams'.
    Almacena información de equipos de la Euroliga.
    """

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")
    home_games = relationship(
        "Game",
        foreign_keys="Game.home_team_id",
        back_populates="home_team",
        cascade="all, delete-orphan",
    )
    away_games = relationship(
        "Game",
        foreign_keys="Game.away_team_id",
        back_populates="away_team",
        cascade="all, delete-orphan",
    )
    player_stats = relationship("PlayerStats", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team(id={self.id}, code='{self.code}', name='{self.name}')>"
