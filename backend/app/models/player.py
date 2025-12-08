from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Player(Base):
    """
    Modelo SQLAlchemy para la tabla 'players'.
    Almacena información de jugadores vinculados a equipos.
    """

    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_code = Column(String(50), nullable=False, unique=True, index=True)  # Código de Euroleague API
    team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False, index=True)
    position = Column(String(50), nullable=True, index=True)
    height = Column(Numeric(3, 2), nullable=True)
    birth_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    team = relationship("Team", back_populates="players")
    player_stats = relationship(
        "PlayerStats", back_populates="player", cascade="all, delete-orphan"
    )
    season_stats = relationship(
        "PlayerSeasonStats", back_populates="player", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.name}', position='{self.position}')>"
