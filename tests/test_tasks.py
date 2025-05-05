from fastapi.testclient import TestClient
import faker
from app.main import app


client = TestClient(app)
fake = faker.Faker()

client.fake_user_email = fake.email()
client.fake_user_password = fake.password()
client.fake_user_name = fake.first_name()
client.new_user_id = 0
client.auth_token = ""


def test_add_task():
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password()
    }
    client.post("/auth/signup", json=user_data)
    task_data = {
        "task_description": "Test task",
        "assignee": 1,
        "due_date": "2025-12-31",
    }
    response = client.post("/tasks/add-task", json=task_data)
    assert response.status_code == 201
    assert response.json()["task_description"] == task_data["task_description"]


def test_high_graded_task():
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password()
    }
    client.post("/auth/signup", json=user_data)
    task_data = {
        "task_description": "Test task",
        "assignee": 1,
        "due_date": "2025-12-31",
    }
    response = client.post("/tasks/add-task", json=task_data)
    assert response.status_code == 201
    assert response.json()["task_description"] == task_data["task_description"]


def test_update_task():
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password()
    }
    client.post("/auth/signup", json=user_data)

    task_data = {
        "task_description": "Test task",
        "assignee": 1,
        "due_date": "2025-12-31",
    }
    response = client.post("/tasks/add-task", json=task_data)
    task_id = response.json()["task_id"]
    update_data = {
        "task_description": "Updated description"
    }
    response = client.patch("/tasks/update-task", params={"task_id": task_id}, json=update_data)
    assert response.status_code == 202
    assert response.json()["task_description"] == "Updated description"


def test_my_tasks():
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password()
    }
    signup_response = client.post("/auth/signup", json=user_data)
    response = client.post("/auth/login",
                           data={"username": user_data["email"],
                                 "password": user_data["password"]}
                           )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    task_data = {
        "task_description": "Test task",
        "assignee": int(signup_response.text),
        "due_date": "2025-12-31",
    }
    client.post("/tasks/add-task", json=task_data)
    response = client.get("/tasks/my-tasks", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
