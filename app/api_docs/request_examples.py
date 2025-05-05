from fastapi import Body


example_create_task = Body(
    openapi_examples={
        "normal":   {
            "summary": "Пример запроса",
            "description": "Пример запроса для создания задачи",
            "value": {
                "task_description": "Подготовить презентацию",
                "assignee": 1,
                "due_date": "2025-05-20",
                "grade": 3
            }
        },
    }
)
