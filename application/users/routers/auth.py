import os
from datetime import timedelta, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field, conint, validator
from sqlalchemy.orm import Session
from starlette import status

from ..database import SessionLocal
from ..models import Users

router = APIRouter(
    prefix='/api',
    tags=['Auth']
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/api/login')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class UserRequest(BaseModel):
    username: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=6, max_length=100)
    first_name: str = Field(min_length=3, max_length=100)
    last_name: str = Field(min_length=3, max_length=100)
    dob: int = conint()
    phone_number: str = Field(min_length=10, max_length=10)

    @validator('dob')
    def validate_dob(cls, value):
        # Convert the epoch timestamp to a datetime object
        try:
            datetime.utcfromtimestamp(int(value / 1000))
        except Exception as e:
            raise ValueError('Invalid DOB') from e
        return value

    class Config:
        json_schema_extra = {
            'example': {
                'username': 'rohan.last',
                'password': 'paffworld',
                'first_name': 'Rohan',
                'last_name': 'Last',
                'dob': 1706251709000,
                'phone_number': '9876543210',
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str


def validate_username(username: str, db):
    user = db.query(Users).filter_by(username=username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_a_new_user(db: db_dependency, user_details: UserRequest):
    validate_username(user_details.username, db)
    user_model = Users(
        username=user_details.username,
        hashed_password=bcrypt_context.hash(user_details.password),
        first_name=user_details.first_name,
        last_name=user_details.last_name,
        dob=datetime.utcfromtimestamp(int(user_details.dob / 1000)),
        phone_number=user_details.phone_number,
    )
    db.add(user_model)
    db.commit()


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username, Users.is_deleted == False).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'user': username, 'id': user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, os.environ.get('SECRET_KEY'), algorithm=os.environ.get('ALGORITHM'))


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, os.environ.get('SECRET_KEY'), algorithms=[os.environ.get('ALGORITHM')])
        username: str = payload.get('user')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user, Token expired.')


@router.post("/login", response_model=Token)
async def obtain_a_jwt_token_for_authentication(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                                db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
    token = create_access_token(user.username, user.id, timedelta(hours=1))
    return {'access_token': token, 'token_type': 'bearer'}
