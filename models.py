import random
import string
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
from sqlalchemy.ext.associationproxy import association_proxy

secret_key = ''.join(random.choice(
                     string.ascii_uppercase + string.digits)
                     for x in xrange(32))

Base = declarative_base()


class User(Base):
    '''User Model'''
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    '''Category Model'''
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column('name', String(80), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="category")

    @property
    def serialize(self):
        return {'id': self.id,
                'name': self.name,
                'Items': [i.serialize for i in self.items]}


class Item(Base):
    '''Catalog Item model'''
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(250), nullable=False)
    date_updated = Column(DateTime, nullable=False)
    image_path = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category,
                            backref=backref('items',
                                            cascade='all,delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="items")

    # association proxy of 'item categories' collection to
    # 'category' attribute
    categories = association_proxy('item_categories', 'category')

    @property
    def serialize(self):
        return {'id': self.id,
                'title': self.title,
                'description': self.description,
                'image_path': self.image_path,
                'date_updated': self.date_updated,
                'category': self.category.name}


engine = create_engine('sqlite:///catalogapp.db')

Base.metadata.create_all(engine)
