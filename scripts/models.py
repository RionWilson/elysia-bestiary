
import json, os
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///database.db")
Base = declarative_base()

stats_keys = ["str", "dex", "agi", "end", "vit", "tou", "wis", "wil", "cha", "int", "per", "lck"]
stats_default = json.dumps({key: 10 for key in stats_keys})
text_default = '{"DEFAULT": ""}'

# creatures table

class Creature(Base):

    __tablename__ = "creatures"

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    path = Column(SmallInteger, nullable=True)
    created = Column(DateTime, default=datetime.utcnow())
    modified = Column(DateTime, default=datetime.utcnow())
    image = Column(String(64), nullable=True, default=None)
    stats = Column(Text, default=stats_default)
    text = Column(Text, default=text_default)

# creatures table

class Group(Base):

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    path = Column(SmallInteger, nullable=True)

# database management
Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)
