from sqlalchemy import (Column, ForeignKey, Integer, String, create_engine)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

## Databse URL
db_url = "sqlite:///database.db"

## Creates a database engine that will connect to the SQLite database
engine = create_engine(db_url)


## Creates a base class for our models to inherit from
# This will allow us to create tables in the database
Base = declarative_base()

## Creates a longURL table with an id and url column
class LongURL(Base):
    __tablename__ = 'longURLs'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    shortUrl = relationship("ShortUrl", back_populates="longURLs", uselist=False)

## Creates a shortURL table with an id and url column
class ShortUrl(Base):
    __tablename__ = 'shortURLs'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    longURL_id = Column(Integer, ForeignKey('longURLs.id'))
    longURLs = relationship("LongURL", back_populates="shortUrl")

    ## Creates the database tables if they don't exist
Base.metadata.create_all(engine)
