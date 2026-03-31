from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Athlete(Base):
    __tablename__ = "athletes"

    id            = Column(Integer, primary_key=True)
    strava_id     = Column(BigInteger, unique=True, nullable=False)
    firstname     = Column(String)
    lastname      = Column(String)
    city          = Column(String)
    country       = Column(String)
    access_token  = Column(String)
    refresh_token = Column(String)
    expires_at    = Column(Integer)


class Activity(Base):
    __tablename__ = "activities"

    id               = Column(Integer, primary_key=True)
    strava_id        = Column(BigInteger, unique=True, nullable=False)
    athlete_id       = Column(BigInteger, nullable=False)
    name             = Column(String)
    date             = Column(DateTime)
    distance_m       = Column(Float)
    duration_s       = Column(Integer)
    elevation_m      = Column(Float)
    avg_heartrate    = Column(Float, nullable=True)
    avg_pace_s_per_km = Column(Float, nullable=True)


def init_db():
    """Creates all tables in PostgreSQL. Run once on startup."""
    Base.metadata.create_all(bind=engine)