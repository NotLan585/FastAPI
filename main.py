from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, func, \
    DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

app = FastAPI(title='Ian\'s Project',
              description='Learning more about FastAPI and SQLAlchemy')

# Database setup
SQLALCHEMY_DATABASE_URL = 'sqlite:///./user.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer, index=True)
    sex = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Create the database tables


Base.metadata.create_all(bind=engine)

# Pydantic model


class UserCreate(BaseModel):
    name: str
    email: str
    age: int
    sex: str

    class Config:
        orm_mode = True


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    age: int
    sex: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None


@app.post('/users/', response_model=UserRead, tags=['Create User'])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail='Email already in use')
    if user.sex != 'Female' and user.sex != 'Male':
        raise HTTPException(status_code=422, detail='Please choose Female or '
                                                    'Male for sex')
    if '@' not in user.email:
        raise HTTPException(status_code=422, detail='Please enter a valid '
                                                    'email address')
    db_user = User(name=user.name, email=user.email, age=user.age,
                   sex=user.sex)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserRead.from_orm(db_user)


@app.get('/users/{user_id}', response_model=UserRead, tags=['Get User Info'])
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return UserRead.from_orm(db_user)


@app.get('/user/', response_model=UserRead, tags=['Get User Info'])
def read_user_by_email(email: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return UserRead.from_orm(db_user)


@app.patch('/users/{user_id}', response_model=UserRead, tags=['Update User'
                                                              ' Info'])
def update_user(user_id: int, user_update: UserUpdate,
                db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')

    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.email is not None:
        # Check if the email is already registered
        existing_user = db.query(User).filter(
            User.email == user_update.email).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400,
                                detail='Email already registered')
        db_user.email = user_update.email
    if user_update.age is not None:
        if user_update.age is not int:
            raise HTTPException(status_code=422,
                                detail='Please enter a valid age')
        else:
            db_user.age = user_update.age
    if user_update.sex is not None:
        if user_update.sex != 'Female' or 'Male':
            raise HTTPException(status_code=422,
                                detail='Please enter Female or Male')
        else:
            db_user.sex = user_update.sex
    db_user.updated_at = func.now()

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserRead.from_orm(db_user)


@app.delete('/delete/{user_id}', tags=['Delete User'])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    db.delete(db_user)
    db.commit()
    return {'message': 'User has been deleted'}
