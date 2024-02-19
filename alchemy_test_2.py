import sqlalchemy
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker



engine = create_engine("sqlite:///test1.db")

Session = sessionmaker(bind=engine)

session = Session()

Base = declarative_base()


# Declare User Table Base

class User(Base):
    __tablename__='users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    password = Column(String)

    def __repr__ (self):
        return f'User{self.name}'
    
# Create tables
    
Base.metadata.create_all(engine)

# Create a class instance

user = User(name='Jhon Snow', password='johnpassword')
session.add(user)
session.flush()
session.commit()

print(user.id)
