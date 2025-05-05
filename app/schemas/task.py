from datetime import date, timedelta
from pydantic import (BaseModel, Field, BeforeValidator, EmailStr)
from typing import Optional, Annotated, TypeAlias
from sqlmodel import SQLModel, Field as SQLField, UniqueConstraint

def _empty_str_or_none(value: str | None) -> None:
    if value is None or value == "":
        return None
    raise ValueError("Expected empty value")


EmptyStrOrNone: TypeAlias = Annotated[None, BeforeValidator(_empty_str_or_none)]


class TaskCreate(BaseModel):
    task_description: str = Field(
        description="Task description",
        max_length=300
    )
    assignee: int
    due_date: Optional[date] = Field(
        gt=date.today() - timedelta(days=1),
        default_factory=lambda: date.today() + timedelta(days=1)
    )
    grade: Optional[int] = None
    project: Optional[int] = None


class TaskRead(TaskCreate):
    task_id: int
    due_date: EmptyStrOrNone | date


class Task(SQLModel, TaskRead, table=True):
    task_id: int = SQLField(default=None, nullable=False,
                            primary_key=True)
    due_date: date
    assignee: int = SQLField(foreign_key="user.user_id")
    project: int = SQLField(default=None, nullable=True, foreign_key="project.project_id")
    grade: int = SQLField(default=None, nullable=True, ge=1, le=10)


class TaskUpdate(TaskCreate):
    task_description: Optional[str] = None
    assignee: Optional[int] = None


class User(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("email"),)
    user_id: int = SQLField(default=None, nullable=False, primary_key=True)
    email: str = SQLField(nullable=True, unique_items=True)
    password: str | None
    name: str
    grade: int | None = SQLField(ge=1,
                                 le=10,
                                 description="""
                                 Чем выше грейд, тем ценнее сотрудник.
                                 Сотрудник может выдать задание только сотруднику с меньшим грейдом.
                                 Сотруднику с грейдом k можно выдать задание только сложности <= k.
                                 """)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Иван Иванов",
                "email": "user@example.com",
                "password": "qwerty",
                "grade": 1
            }
        }


class UserRead(BaseModel):
    name: str
    email: str
    user_id: int
    grade: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[int] = None


class Project(SQLModel, table=True):
    project_id: int = SQLField(default=None, nullable=False, primary_key=True)
    project_name: str
    project_description: str | None
