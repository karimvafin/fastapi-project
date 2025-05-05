import httpx
import asyncio
from fastapi import APIRouter, status, Depends, HTTPException, Response
from sqlmodel import Session, select
from typing import Annotated, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.db import get_session, get_async_session
from ..schemas import task as schema_task
from app.api_docs import request_examples
from ..auth import auth_handler


router = APIRouter(prefix="/tasks", tags=["Задания"])


@router.post("/add-task", status_code=status.HTTP_201_CREATED,
             response_model=schema_task.TaskRead,
             summary="Добавить задание")
def create_task(task: Annotated[
                        schema_task.TaskCreate,
                        request_examples.example_create_task],
                session: Session = Depends(get_session)
                ):
    """
    Создание задачи
    """
    statement = (
        select(schema_task.User)
        .where(schema_task.User.user_id == task.assignee)
    )
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Assignee not found"
        )

    if task.grade and user.grade and user.grade < task.grade:
        raise HTTPException(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            detail=f"User {user.name} must have higher or equal grade, than the task grade"
        )

    new_task = schema_task.Task(
        task_description=task.task_description,
        assignee=task.assignee,
        due_date=task.due_date,
        grade=task.grade,
        project=task.project
    )
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task


@router.patch("/update-task", status_code=status.HTTP_202_ACCEPTED,
            response_model=schema_task.TaskRead,
            summary="Обновить задание")
def update_task(
        task_id: int,
        user_data: schema_task.TaskUpdate,
        session: Session = Depends(get_session)
):
    """
    Обновление задачи
    """
    task = session.exec(select(schema_task.Task).where(schema_task.Task.task_id == task_id)).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    if user_data.assignee:
        statement = select(schema_task.Task).where(schema_task.Task.assignee == user_data.assignee)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_data.assignee} not found"
            )
    if user_data.project:
        statement = select(schema_task.Task).where(schema_task.Task.project == user_data.project)
        project = session.exec(statement).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {user_data.project} not found"
            )

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    session.add(task)
    session.commit()
    session.refresh(task)

    return task


@router.get("/tasks-list", status_code=status.HTTP_200_OK,
            response_model=List[schema_task.TaskRead],
            summary="Показать список заданий")
async def read_tasks_async(session: AsyncSession = Depends(get_async_session)):
    """
    Список всех заданий
    """
    result = await session.execute(select(schema_task.Task))
    tasks = result.scalars().all()
    if tasks is None or len(tasks) == 0:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"The task list is empty"
        )
    return tasks


@router.get("/my-tasks",
            status_code=status.HTTP_200_OK,
            response_model=List[schema_task.TaskRead],
            summary = 'Список моих заданий')
def show_my_tasks(
    current_user: Annotated[schema_task.User, Depends(auth_handler.get_current_user)],
    session: Session = Depends(get_session)
):
    """
    Список всех заданий для вошедшего пользователя
    """
    statement = select(schema_task.Task).where(schema_task.Task.assignee == current_user.user_id)
    result = session.exec(statement)
    tasks = result.all()
    if tasks is None or len(tasks) == 0:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"The task list for user {current_user.name} is empty"
        )
    return tasks


@router.get("/tasks-for-day",
            status_code=status.HTTP_200_OK,
            summary="Показать ближайшие задания")
async def read_tasks_for_day(response: Response,
                             session: AsyncSession = Depends(get_async_session),
                             due_date: date = date.today()):
    """
    Показать задания с заданным дедлайном
    """
    async def query_db(due_date_param):
        statement = (
            select(schema_task.Task)
            .where(schema_task.Task.due_date == due_date_param)
        )
        result = await session.execute(statement)
        return result.scalars().all()


    http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=None))
    res = await asyncio.gather(
        query_db(due_date),
        http_client.get(f"https://isdayoff.ru/{due_date}"),
    )

    output = [{
        "due_date": due_date,
        "is_day_off": res[1].text == "1",
        "tasks": res[0]
    }]

    return output


@router.get("/get-candidate/{task_grade}",
               response_model=schema_task.UserRead,
               summary="Подобрать исполнителя")
def get_candidate(task_grade: int, session: Session = Depends(get_session)):
    """
    Подобрать подходящего кандидата для задания с учетом его грейда и занятости
    """
    statement = select(schema_task.User).where(schema_task.User.grade >= task_grade)
    users = session.exec(statement).all()
    tasks = session.exec(select(schema_task.Task)).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users"
        )

    task_counts = {user.user_id: 0 for user in users}
    for task in tasks:
        if task.assignee in task_counts:
            task_counts[task.assignee] += 1

    user_with_min_tasks = min(
        users,
        key=lambda user: task_counts.get(user.user_id, 0)
    )

    return user_with_min_tasks


@router.delete("/delete-task/{task_id}",
               summary="Удалить задание")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    """
    Удалить задание с заданным id
    """
    task = session.get(schema_task.Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    session.delete(task)
    session.commit()

    return {"Message": f"Task with id {task_id} deleted"}
