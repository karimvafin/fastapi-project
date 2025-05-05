from fastapi import FastAPI

from app.routes import task, auth


app = FastAPI(
    title="Система для управления задачами",
    description="Система для управления задачами с возможностью регистрации пользователей",
    version="0.0.1",
    contact={
        "name": "Karim Vafin",
        "email": "karim.vafin@mail.ru",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

app.include_router(auth.router)
app.include_router(task.router)
