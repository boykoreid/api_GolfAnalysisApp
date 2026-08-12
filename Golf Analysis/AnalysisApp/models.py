from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String, nullable=False)
    admin = Column(Boolean, nullable=False)

 
class Rounds(Base):
    __tablename__ = 'rounds'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    season = Column(Integer, nullable=False)
    course_name = Column(String)
    is_front_nine = Column(Boolean, nullable=False)

 
class Holes(Base):
    __tablename__ = 'holes'

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey('rounds.id'), nullable=False)
    hole_number = Column(Integer, nullable=False)
    par = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    putts = Column(Integer, nullable=False)
    gir = Column(Boolean, nullable=False)
    fairway_hit = Column(Boolean, nullable=True)
    penalty_strokes = Column(Integer, nullable=True)

