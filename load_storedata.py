from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from stores_db import Base, Manager, Store, Product

engine = create_engine('sqlite:///shoestores.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create dummy user1
Manager1 = Manager(name="Joe Manager", email="jmanager@lotsofkicks.com",
             picture="""https://upload.wikimedia.org/wikipedia/de/thumb/5/50/
             Adidas_klassisches_logo.svg/
             500px-Adidas_klassisches_logo.svg.png""")
session.add(Manager1)
session.commit()


# Inventory for store 1
Store1 = Store(manager_id=1, name="Awesome Store", zipcode = 10010)

session.add(Store1)
session.commit()

product1 = Product(manager_id=1, name="Adidas NMD", price=149.99,
                    description="A dope pair of kicks", units=5,
                    size=10, store=Store1)

session.add(product1)
session.commit()

print "Loaded stores and items data."