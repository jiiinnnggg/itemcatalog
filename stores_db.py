from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)


Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))

class Manager(Base):
    __tablename__ = 'manager'

    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))
    id = Column(Integer, primary_key = True)

    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in = expiration)
        return s.dumps({'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            #Valid Token, but expired
            return None
        except BadSignature:
            #Invalid Token
            return None
        user_id = data['id']
        return user_id

    @property
    def serialize(self):
       return {
           'name'       : self.name,
           'id'         : self.id,
           'email'      : self.email,
           'picture'    : self.picture,
       }


class Store(Base):
    __tablename__ = 'store'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    zipcode = Column(Integer, nullable=False)
    manager_id = Column(Integer, ForeignKey('manager.id'))
    manager = relationship(Manager)

    @property
    def serialize(self):
       return {
           'name'       : self.name,
           'id'         : self.id,
           'zipcode'    : self.zipcode,
           'manager_id' : self.manager_id
       }


class Product(Base):
    __tablename__ = 'product'

    name =Column(String, nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String)
    units = Column(Integer)
    price = Column(Float)
    size = Column(Integer, nullable = False)
    store_id = Column(Integer,ForeignKey('store.id'))
    store = relationship(Store)
    manager_id = Column(Integer, ForeignKey('manager.id'))
    manager = relationship(Manager)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'           : self.name,
           'id'             : self.id,
           'description'    : self.description,
           'price'          : self.price,
           'units'          : self.units,
        }


engine = create_engine('sqlite:///shoestores.db')


Base.metadata.create_all(engine)
