import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from controllers.asset_controller import AssetController
from config import JWT_SECRET_KEY, JWT_ALGORITHM


@pytest.fixture
def mock_db():
    """Fixture to mock DatabaseManager connection and cursors."""
    with patch("controllers.asset_controller.DatabaseManager") as MockDbManager:
        db_instance = MockDbManager.return_value
        yield db_instance


@pytest.fixture
def admin_token():
    """Generate a valid ADMIN JWT for testing."""
    payload = {
        "user_id": 1,
        "role": "ADMIN",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def test_get_available_assets_generator_success(mock_db):
    """Test generator yielding available assets for employees."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "AssetNo": "TAG-101",
            "AssetName": "MacBook Pro",
            "CategoryName": "Laptops",
            "AssetModel": "M2",
            "Status": "AVAILABLE",
        }
    ]

    mock_db.connection.cursor.return_value = mock_cursor

    controller = AssetController()
    controller.db = mock_db

    results = list(controller.get_available_assets_generator())

    assert len(results) == 1
    assert results[0]["AssetNo"] == "TAG-101"
    assert results[0]["Status"] == "AVAILABLE"

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_all_assets_generator_success(mock_db, admin_token):
    """Test generator yielding all assets for the admin view."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "AssetNo": "TAG-101",
            "AssetName": "MacBook Pro",
            "CategoryName": "Laptops",
            "AssetModel": "M2",
            "Status": "ALLOCATED",
        }
    ]

    mock_db.connection.cursor.return_value = mock_cursor

    controller = AssetController()
    controller.db = mock_db

    results = list(controller.get_all_assets_generator(token=admin_token))

    assert len(results) == 1
    assert results[0]["Status"] == "ALLOCATED"

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_unique_categories_success(mock_db):
    """Test fetching unique category names."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("Laptops",),
        ("Monitors",),
        ("Laptops",),
    ]

    mock_db.connection.cursor.return_value = mock_cursor

    controller = AssetController()
    controller.db = mock_db

    categories = controller.get_unique_categories()

    assert categories == {"Laptops", "Monitors"}

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_add_asset_success(mock_db, admin_token):
    """Test admin successfully adding an asset."""
    controller = AssetController()
    controller.db = mock_db

    mock_db.execute_query.return_value = None

    result = controller.add_asset(
        asset_no="TAG-999",
        name="Dell Monitor",
        category_id=2,
        model="U2720Q",
        value=350.00,
        token=admin_token,
    )

    assert result is True
    mock_db.execute_query.assert_called_once()


def test_get_inventory_summary_success(mock_db, admin_token):
    """Test fetching aggregate inventory stock counts."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "CategoryName": "Laptops",
            "AssetName": "MacBook Pro",
            "TotalOwned": 5,
            "TotalAvailable": 2,
            "TotalAllocated": 3,
        }
    ]

    mock_db.connection.cursor.return_value = mock_cursor

    controller = AssetController()
    controller.db = mock_db

    summary = controller.get_inventory_summary(token=admin_token)

    assert isinstance(summary, list)
    assert len(summary) == 1
    assert summary[0]["CategoryName"] == "Laptops"
    assert summary[0]["AssetName"] == "MacBook Pro"
    assert summary[0]["TotalOwned"] == 5
    assert summary[0]["TotalAvailable"] == 2
    assert summary[0]["TotalAllocated"] == 3

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()