from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    id = Column(Integer, primary_key=True)

    @property
    def serialize(self):
        return {
           'name': self.name,
           'id': self.id,
           'email': self.email,
           'picture': self.picture,
        }


class Business(Base):
    __tablename__ = 'business'

    name = Column(String(200), nullable=False)
    #id = Column(Integer, primary_key=True) #old code, working, a lot depends on this to render the list object correctly
    #id_name = Column(String(100)) #old code, working, a lot depends on this to render the list object correctly
    id_name = Column(String(100), primary_key=True) #new code, to work w unique requirement per postgresql
    url = Column(String(250))
    address = Column(String(250))
    phone = Column(String(30))
    rating = Column(String(4))
    review_count = Column(Integer)
    price = Column(String(5))
    image_url = Column(String(250))
    image_url_sm = Column(String(250))
    image_url_med = Column(String(250))
    comment = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
           'name': self.name,
           'id_name': self.id_name,
           'url': self.url,
           'phone': self.phone,
           'address': self.address,
           'rating': self.rating,
           'reviews': self.review_count,
           'price': self.price,
           'image_url': self.image_url
        }


class BizList(Base):
    __tablename__ = 'biz_list'

    name = Column(String(200), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'listname': self.name,
            'description': self.description,
            'list_id': self.id,
            'user_Id': self.user_id,
            'username': self.user.name,
            'user_email': self.user.email
        }


class ListObject(Base):
    __tablename__ = 'list_object'

    id = Column(Integer, primary_key=True)

    name = Column(String(100), ForeignKey('business.id_name')) #old code, working, a lot depends on this to render the list object correctly
    #name = Column(String(100))#, business.id_name) 
    #biz_id = Column(Integer, ForeignKey('business.id')) #new code, to work w unique requirement per postgresql
    business = relationship(Business)

    list_id = Column(Integer, ForeignKey('biz_list.id'))
    biz_list = relationship(BizList)

    @property
    def serialize(self):
        return {
            'list_obj_id': self.id,
            'ref_biz_name': self.name,
            #'ref_biz_id': self.biz_id,
            'ref_bizname': self.business.name,
            'ref_list': self.biz_list.name,
            'ref_username': self.biz_list.user.name,
            'ref_user_email': self.biz_list.user.email
        }


engine = create_engine('postgresql://catalog:catalog@localhost/catalog')


Base.metadata.create_all(engine)
