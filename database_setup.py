import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
	
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(80), nullable=False)


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

class Item(Base): 
    __tablename__ = 'item'

    id = Column(Integer, primary_key = True)
    name = Column(String(100), nullable = False)
    description = Column(String(300))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship('Category', backref=backref('items', cascade="all, delete"))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


engine = create_engine('sqlite:///itemcatalogue.db')

Base.metadata.create_all(engine)

print('Database created!')