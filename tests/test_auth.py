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


def test_signup():
    response = client.post("/auth/signup",
                           json={"email": client.fake_user_email,
                                 "password": client.fake_user_password,
                                 "name": client.fake_user_name}
                           )
    assert response.status_code == 201
    client.new_user_id = response.json()


def test_login():
    response = client.post("/auth/login",
                           data={"username": client.fake_user_email,
                                 "password": client.fake_user_password}
                           )
    assert response.status_code == 200
    client.auth_token = response.json()["access_token"]


def test_me():
    response = client.get("/auth/me",
                          headers={"Authorization": f"Bearer {client.auth_token}"}
                          )
    assert response.status_code == 200
    assert response.json()["user_id"] == client.new_user_id


def test_signup_duplicate_email():
    user_data = {
        "name": fake.name(),
        "email": "existing@example.com",
        "password": fake.password()
    }
    client.post("/auth/signup", json=user_data)
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 422


def test_login_invalid_password():
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password()
    }
    client.post("/auth/signup", json=user_data)
    login_data = {
        "username": user_data["email"],
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401


def get_token(email, password):
    login_data = {
        "username": email,
        "password": password
    }
    response = client.post("/auth/login", data=login_data)
    return response.json()["access_token"]

def test_show_current_user():
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password()
    }
    client.post("/auth/signup", json=user_data)
    token = get_token(user_data["email"], user_data["password"])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]


def test_update_user():
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password()
    }
    client.post("/auth/signup", json=user_data)
    token = get_token(user_data["email"], user_data["password"])
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "name": "Ivan"
    }
    response = client.patch("/auth/update-user", params={"user_id": 1}, json=update_data, headers=headers)
    assert response.status_code == 202
    assert response.json()["name"] == "Ivan"


def test_list_users():
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password()
    }
    client.post("/auth/signup", json=user_data)
    response = client.get("/auth/users")
    assert response.status_code == 200
    assert len(response.json()) > 0
