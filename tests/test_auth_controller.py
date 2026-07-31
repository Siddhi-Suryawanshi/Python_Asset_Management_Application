import pytest
import jwt
import bcrypt
from unittest.mock import MagicMock, patch

from controllers.auth_controller import AuthController
from models.user_model import Employee, Admin
from config import JWT_SECRET_KEY, JWT_ALGORITHM


@pytest.fixture
def mock_db():
    with patch("controllers.auth_controller.DatabaseManager") as MockDb:
        db = MockDb.return_value
        yield db


@pytest.fixture
def controller(mock_db):
    controller = AuthController()
    controller.db = mock_db
    return controller


# -------------------------
# Register User Tests
# -------------------------

def test_register_user_success(controller, mock_db):
    mock_db.fetch_one.return_value = None

    result = controller.register_user(
        name="John Doe",
        email="john@example.com",
        password="Password123",
        gender="Male",
        contact="9876543210",
        address="Pune",
        role="EMPLOYEE"
    )

    assert result is True
    mock_db.execute_query.assert_called_once()


def test_register_duplicate_email(controller, mock_db):
    mock_db.fetch_one.return_value = {
        "Email": "john@example.com"
    }

    result = controller.register_user(
        name="John Doe",
        email="john@example.com",
        password="Password123",
        gender="Male",
        contact="9876543210",
        address="Pune"
    )

    assert result is False


def test_register_invalid_email(controller):
    result = controller.register_user(
        name="John Doe",
        email="invalid-email",
        password="Password123",
        gender="Male",
        contact="9876543210",
        address="Pune"
    )

    assert result is False


def test_register_invalid_phone(controller):
    result = controller.register_user(
        name="John Doe",
        email="john@example.com",
        password="Password123",
        gender="Male",
        contact="12345",
        address="Pune"
    )

    assert result is False


# -------------------------
# Login Tests
# -------------------------

def test_login_employee_success(controller, mock_db):
    password = "Password123"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    mock_db.fetch_one.return_value = {
        "UserId": 1,
        "Name": "John",
        "Email": "john@example.com",
        "PasswordHash": hashed,
        "Role": "EMPLOYEE"
    }

    user, token = controller.login(
        "john@example.com",
        password
    )

    assert isinstance(user, Employee)
    assert token is not None

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM]
    )

    assert payload["user_id"] == 1
    assert payload["role"] == "EMPLOYEE"


def test_login_admin_success(controller, mock_db):
    password = "Admin123"

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    mock_db.fetch_one.return_value = {
        "UserId": 10,
        "Name": "Admin",
        "Email": "admin@example.com",
        "PasswordHash": hashed,
        "Role": "ADMIN"
    }

    user, token = controller.login(
        "admin@example.com",
        password
    )

    assert isinstance(user, Admin)
    assert token is not None

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM]
    )

    assert payload["role"] == "ADMIN"


def test_login_wrong_password(controller, mock_db):
    hashed = bcrypt.hashpw(
        b"CorrectPassword",
        bcrypt.gensalt()
    ).decode()

    mock_db.fetch_one.return_value = {
        "UserId": 1,
        "Name": "John",
        "Email": "john@example.com",
        "PasswordHash": hashed,
        "Role": "EMPLOYEE"
    }

    user, token = controller.login(
        "john@example.com",
        "WrongPassword"
    )

    assert user is None
    assert token is None


def test_login_user_not_found(controller, mock_db):
    mock_db.fetch_one.return_value = None

    user, token = controller.login(
        "nouser@example.com",
        "Password123"
    )

    assert user is None
    assert token is None


def test_register_database_exception(controller, mock_db):
    mock_db.fetch_one.return_value = None
    mock_db.execute_query.side_effect = Exception("Database Error")

    result = controller.register_user(
        "John",
        "john@example.com",
        "Password123",
        "Male",
        "9876543210",
        "Pune"
    )

    assert result is False


def test_login_database_exception(controller, mock_db):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    user, token = controller.login(
        "john@example.com",
        "Password123"
    )

    assert user is None
    assert token is None