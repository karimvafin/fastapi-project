from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from psycopg2.errors import UniqueViolation
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated, List

from ..auth import auth_handler
from app.config import settings
from app.db import get_session, get_async_session
from ..schemas import task as schema_task

router = APIRouter(prefix="/auth", tags=["Аутентификация пользователей"])

@router.post("/signup", status_code=status.HTTP_201_CREATED,
             response_model=int,
             summary="Зарегистрироваться")
def create_user(user: schema_task.User,
                session: Session = Depends(get_session)):
    """
    Регистрация пользователя
    """
    new_user = schema_task.User(
        name=user.name,
        email=user.email,
        password=auth_handler.get_password_hash(user.password),
        grade=user.grade
    )
    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user.user_id
    except IntegrityError as e:
        assert isinstance(e.orig, UniqueViolation)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User with email {user.email} already exists"
        )


@router.post("/login",
             status_code=status.HTTP_200_OK,
             summary="Войти в систему")
def user_login(login_attempt_data: OAuth2PasswordRequestForm = Depends(),
               db_session: Session = Depends(get_session)):
    """
    Авторизация пользователя
    """
    statement = (select(schema_task.User)
                 .where(schema_task.User.email == login_attempt_data.username))
    existing_user = db_session.exec(statement).first()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User {login_attempt_data.username} not found"
        )

    if auth_handler.verify_password(login_attempt_data.password,
                                    existing_user.password):
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = auth_handler.create_access_token(
            data={"sub": login_attempt_data.username},
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Wrong password for user {login_attempt_data.username}"
        )


@router.get("/me",
            response_model=schema_task.UserRead,
            summary = 'Информация о пользователе')
def show_current_user(
    current_user: Annotated[schema_task.User, Depends(auth_handler.get_current_user)]
):
    """
    Информация о вошедшем пользователе
    """
    return current_user



@router.patch("/update-user", status_code=status.HTTP_202_ACCEPTED,
            response_model=schema_task.UserRead,
            summary="Обновить данные пользователя")
def update_user(
        user_id: int,
        user_data: schema_task.UserUpdate,
        session: Session = Depends(get_session)
):
    user = session.exec(select(schema_task.User).where(schema_task.User.user_id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@router.get("/users", status_code=status.HTTP_200_OK,
            response_model=List[schema_task.UserRead],
            summary="Показать список пользователей")
async def read_users_async(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(schema_task.User))
    users = result.scalars().all()
    if users is None or len(users) == 0:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"The user list is empty"
        )
    users_result = [schema_task.UserRead(
        name=user.name,
        email=user.email,
        user_id=user.user_id,
        grade=user.grade
    ) for user in users]
    return users_result
