# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Item, User, Base

engine = create_engine('sqlite:///itemcatalogue.db')

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy with the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
user1 = User(name="Conor Bailey", email="conbailey90@gmail.com")
session.add(user1)
session.commit()

# Items for Synths
category1 = Category(name="Synths", user_id=1)

session.add(category1)
session.commit()

item1 = Item(name="Korg M1", description="A classic synth", category=category1, user_id=1)

session.add(item1)
session.commit()

item2 = Item(name="Moog Minimoog", description="A monophonic synth", category=category1, user_id=1)

session.add(item2)
session.commit()

item3 = Item(name="Sequential Circuits Prophet-5", description="A polyphonic synth", category=category1, user_id=1)

session.add(item3)
session.commit()

# Items for Drum Machines
category2 = Category(name="Drum Machines", user_id=1)

session.add(category2)
session.commit()

item1 = Item(name="Roland TR-808", description="The Roland TR-808 is a famous drum machine", category=category2, user_id=1)

session.add(item1)
session.commit()

item2 = Item(name="Roland TR-909", description="The Roland TR-909 is used in techno muic production", category=category2, user_id=1)

session.add(item2)
session.commit()

item3 = Item(name="Akai MPC60", description="The Akai MPC is a decent drum machine.", category=category2, user_id=1)

session.add(item3)
session.commit()

# Items for DAW Software
category3 = Category(name="DAW Software", user_id=1)

session.add(category3)
session.commit()

item1 = Item(name="Ableton Live", description="Ableton Live is a digital audio workstaion", category=category3, user_id=1)

session.add(item1)
session.commit()

item2 = Item(name="Logic Pro", description="Logic Pro is a digital audio workstation", category=category3, user_id=1)

session.add(item2)
session.commit()

item3 = Item(name="Pro Tools", description="Pro Tools is a digital audio workstation", category=category3, user_id=1)

session.add(item3)
session.commit()

print('items added!!!')


categories = session.query(Category).all()
for category in categories:
    print "Category: " + category.name