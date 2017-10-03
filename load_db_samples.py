from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Business


engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Joe Schmo", email="jschmo1@clowncollege.edu",
             picture='https://upload.wikimedia.org/wikipedia/fi/1/17/Krusty_the_Clown.png')
session.add(User1)
session.commit()

# sample business
business1 = Business(user_id=1, address='61 Lexington Ave, Unit B, New York, NY 10010',
                     id_name='bao-bao-cafe-new-york-2',
                     image_url='https://s3-media2.fl.yelpcdn.com/bphoto/iEEU_Xu1duVjO7Le9jVhPA/o.jpg',
                     image_url_med='https://s3-media2.fl.yelpcdn.com/bphoto/iEEU_Xu1duVjO7Le9jVhPA/300s.jpg',
                     image_url_sm='https://s3-media2.fl.yelpcdn.com/bphoto/iEEU_Xu1duVjO7Le9jVhPA/120s.jpg',
                     name='Bao Bao Cafe', phone='(917) 388-2479', price='$', rating=4.0, review_count=287,
                     url='https://www.yelp.com/biz/bao-bao-cafe-new-york-2')

session.add(business1)
session.commit()


print("Added sample database items.")
