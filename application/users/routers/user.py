from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, conint, validator
from sqlalchemy.orm import Session, defer
from starlette import status

from .auth import get_current_user, bcrypt_context
from ..database import SessionLocal
from ..models import Users

router = APIRouter(
    prefix='/api/user',
    tags=['Users']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class UserDetailsRequest(BaseModel):
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
                'first_name': 'Rohan',
                'last_name': 'Last',
                'dob': 1706251709000,
                'phone_number': '9876543210',
            }
        }


class PasswordUpdateRequest(BaseModel):
    password: str
    new_password: str = Field(min_length=6)


@router.get("", status_code=status.HTTP_200_OK)
async def get_user_details(user: user_dependency, db: db_dependency):
    columns_to_exclude = [Users.hashed_password, Users.is_deleted, Users.is_active]
    return db.query(Users).options(*[defer(column) for column in columns_to_exclude]).filter(
        Users.id == user.get('id')).first()


@router.put("", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_details(user: user_dependency, db: db_dependency, user_details: UserDetailsRequest):
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    user_model.first_name = user_details.first_name
    user_model.last_name = user_details.last_name
    user_model.dob = datetime.utcfromtimestamp(int(user_details.dob / 1000))
    user_model.phone_number = user_details.phone_number
    db.add(user_model)
    db.commit()


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password(user: user_dependency, db: db_dependency, password_details: PasswordUpdateRequest):
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if not bcrypt_context.verify(password_details.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail='Invalid Current Password')
    user_model.hashed_password = bcrypt_context.hash(password_details.new_password)
    db.add(user_model)
    db.commit()
