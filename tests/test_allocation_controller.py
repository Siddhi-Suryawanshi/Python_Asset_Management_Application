import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from controllers.allocation_controller import AllocationController
from config import JWT_SECRET_KEY, JWT_ALGORITHM


# =====================================================
# Fixtures
# =====================================================

@pytest.fixture
def mock_db():
    """Mock DatabaseManager."""
    with patch("controllers.allocation_controller.DatabaseManager") as MockDb:
        db = MockDb.return_value
        yield db


@pytest.fixture
def controller(mock_db):
    controller = AllocationController()
    controller.db = mock_db
    return controller


@pytest.fixture
def admin_token():
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


# =====================================================
# request_asset()
# =====================================================

def test_request_asset_success(controller, mock_db):
    mock_db.fetch_one.return_value = {
        "AssetId": 101,
        "Status": "AVAILABLE"
    }

    result = controller.request_asset(
        "TAG-101",
        5
    )

    assert result is True

    mock_db.fetch_one.assert_called_once()
    mock_db.execute_query.assert_called_once()


def test_request_asset_not_found(controller, mock_db):
    mock_db.fetch_one.return_value = None

    result = controller.request_asset(
        "TAG-999",
        5
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_request_asset_not_available(controller, mock_db):
    mock_db.fetch_one.return_value = {
        "AssetId": 101,
        "Status": "ALLOCATED"
    }

    result = controller.request_asset(
        "TAG-101",
        5
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_request_asset_database_exception(controller, mock_db):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    result = controller.request_asset(
        "TAG-101",
        5
    )

    assert result is False


# =====================================================
# get_pending_requests()
# =====================================================

def test_get_pending_requests_success(
        controller,
        mock_db,
        admin_token
):
    cursor = MagicMock()

    cursor.fetchall.return_value = [
        {
            "AllocationId": 1,
            "EmployeeName": "John",
            "AssetName": "MacBook",
            "AssetNo": "TAG-101"
        }
    ]

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_pending_requests(
        token=admin_token
    )

    assert len(result) == 1
    assert result[0]["EmployeeName"] == "John"

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_pending_requests_empty(
        controller,
        mock_db,
        admin_token
):
    cursor = MagicMock()

    cursor.fetchall.return_value = []

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_pending_requests(
        token=admin_token
    )

    assert result == []

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_pending_requests_database_exception(
        controller,
        mock_db,
        admin_token
):
    mock_db.connect.side_effect = Exception("Database Error")

    result = controller.get_pending_requests(
        token=admin_token
    )

    assert result == []


# =====================================================
# assign_auditor()
# =====================================================

def test_assign_auditor_success(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = {
        "UserId": 5
    }

    result = controller.assign_auditor(
        allocation_id=10,
        auditor_id=7,
        token=admin_token
    )

    assert result is True

    mock_db.execute_query.assert_called_once()


def test_assign_auditor_request_not_found(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = None

    result = controller.assign_auditor(
        allocation_id=10,
        auditor_id=7,
        token=admin_token
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_assign_auditor_same_employee(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = {
        "UserId": 7
    }

    result = controller.assign_auditor(
        allocation_id=10,
        auditor_id=7,
        token=admin_token
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_assign_auditor_database_exception(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    result = controller.assign_auditor(
        allocation_id=10,
        auditor_id=7,
        token=admin_token
    )

    assert result is False

# =====================================================
# get_audit_tasks()
# =====================================================

def test_get_audit_tasks_success(controller, mock_db):
    cursor = MagicMock()

    cursor.fetchall.return_value = [
        {
            "AllocationId": 1,
            "Requester": "John",
            "AssetName": "MacBook",
            "AssetNo": "TAG-101"
        }
    ]

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_audit_tasks(7)

    assert len(result) == 1
    assert result[0]["Requester"] == "John"

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_audit_tasks_empty(controller, mock_db):
    cursor = MagicMock()

    cursor.fetchall.return_value = []

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_audit_tasks(7)

    assert result == []

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_audit_tasks_database_exception(controller, mock_db):
    mock_db.connect.side_effect = Exception("Database Error")

    result = controller.get_audit_tasks(7)

    assert result == []


# =====================================================
# submit_audit_result()
# =====================================================

def test_submit_audit_result_approved_success(controller, mock_db):
    mock_db.fetch_one.return_value = {
        "Status": "AVAILABLE"
    }

    result = controller.submit_audit_result(
        allocation_id=10,
        auditor_id=7,
        is_approved=True
    )

    assert result is True
    mock_db.execute_query.assert_called_once()


def test_submit_audit_result_denied_success(controller, mock_db):
    mock_db.fetch_one.return_value = {
        "Status": "AVAILABLE"
    }

    result = controller.submit_audit_result(
        allocation_id=10,
        auditor_id=7,
        is_approved=False
    )

    assert result is True
    mock_db.execute_query.assert_called_once()


def test_submit_audit_result_asset_under_maintenance(controller, mock_db):
    mock_db.fetch_one.return_value = {
        "Status": "IN_MAINTENANCE"
    }

    result = controller.submit_audit_result(
        allocation_id=10,
        auditor_id=7,
        is_approved=True
    )

    assert result is False
    mock_db.execute_query.assert_not_called()


def test_submit_audit_result_database_exception(controller, mock_db):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    result = controller.submit_audit_result(
        allocation_id=10,
        auditor_id=7,
        is_approved=True
    )

    assert result is False


# =====================================================
# get_audited_requests()
# =====================================================

def test_get_audited_requests_success(
        controller,
        mock_db,
        admin_token
):
    cursor = MagicMock()

    cursor.fetchall.return_value = [
        {
            "AllocationId": 1,
            "Requester": "John",
            "Auditor": "Alice",
            "AssetName": "MacBook",
            "AssetNo": "TAG-101"
        }
    ]

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_audited_requests(
        token=admin_token
    )

    assert len(result) == 1
    assert result[0]["Auditor"] == "Alice"

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_audited_requests_empty(
        controller,
        mock_db,
        admin_token
):
    cursor = MagicMock()

    cursor.fetchall.return_value = []

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_audited_requests(
        token=admin_token
    )

    assert result == []

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_audited_requests_database_exception(
        controller,
        mock_db,
        admin_token
):
    mock_db.connect.side_effect = Exception("Database Error")

    result = controller.get_audited_requests(
        token=admin_token
    )

    assert result == []


# =====================================================
# approve_request()
# =====================================================

def test_approve_request_success(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = {
        "AssetId": 100
    }

    result = controller.approve_request(
        allocation_id=5,
        token=admin_token
    )

    assert result is True

    assert mock_db.execute_query.call_count == 2


def test_approve_request_not_found(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = None

    result = controller.approve_request(
        allocation_id=5,
        token=admin_token
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_approve_request_database_exception(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    result = controller.approve_request(
        allocation_id=5,
        token=admin_token
    )

    assert result is False

# =====================================================
# get_employee_assets()
# =====================================================

def test_get_employee_assets_success(controller, mock_db):
    cursor = MagicMock()

    cursor.fetchall.return_value = [
        {
            "AllocationId": 1,
            "AssetName": "MacBook Pro",
            "AssetNo": "TAG-101",
            "Status": "ALLOCATED"
        }
    ]

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_employee_assets(5)

    assert len(result) == 1
    assert result[0]["AssetName"] == "MacBook Pro"
    assert result[0]["Status"] == "ALLOCATED"

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_employee_assets_empty(controller, mock_db):
    cursor = MagicMock()

    cursor.fetchall.return_value = []

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_employee_assets(5)

    assert result == []

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_employee_assets_database_exception(controller, mock_db):
    mock_db.connect.side_effect = Exception("Database Error")

    result = controller.get_employee_assets(5)

    assert result == []


# =====================================================
# return_asset()
# =====================================================

def test_return_asset_success(controller, mock_db):
    mock_db.fetch_one.return_value = {
        "AllocationId": 11,
        "AssetId": 101
    }

    result = controller.return_asset(
        asset_no="TAG-101",
        user_id=5
    )

    assert result is True

    assert mock_db.execute_query.call_count == 2


def test_return_asset_not_allocated(controller, mock_db):
    mock_db.fetch_one.return_value = None

    result = controller.return_asset(
        asset_no="TAG-101",
        user_id=5
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_return_asset_database_exception(controller, mock_db):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    result = controller.return_asset(
        asset_no="TAG-101",
        user_id=5
    )

    assert result is False


# =====================================================
# get_employee_list()
# =====================================================

def test_get_employee_list_success(
        controller,
        mock_db,
        admin_token
):
    cursor = MagicMock()

    cursor.fetchall.return_value = [
        {
            "UserId": 1,
            "Name": "John",
            "Email": "john@example.com"
        },
        {
            "UserId": 2,
            "Name": "Alice",
            "Email": "alice@example.com"
        }
    ]

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_employee_list(
        token=admin_token
    )

    assert len(result) == 2
    assert result[0]["Name"] == "John"
    assert result[1]["Name"] == "Alice"

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_employee_list_empty(
        controller,
        mock_db,
        admin_token
):
    cursor = MagicMock()

    cursor.fetchall.return_value = []

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_employee_list(
        token=admin_token
    )

    assert result == []

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_employee_list_database_exception(
        controller,
        mock_db,
        admin_token
):
    mock_db.connect.side_effect = Exception("Database Error")

    result = controller.get_employee_list(
        token=admin_token
    )

    assert result == []

# =====================================================
# raise_service_ticket()
# =====================================================

def test_raise_service_ticket_success(controller, mock_db):
    mock_db.fetch_one.return_value = {
        "AllocationId": 20,
        "AssetId": 101
    }

    result = controller.raise_service_ticket(
        asset_no="TAG-101",
        user_id=5,
        issue_type="Hardware",
        description="Screen is flickering"
    )

    assert result is True

    # Insert ticket + update allocation + update asset
    assert mock_db.execute_query.call_count == 3


def test_raise_service_ticket_asset_not_allocated(controller, mock_db):
    mock_db.fetch_one.return_value = None

    result = controller.raise_service_ticket(
        asset_no="TAG-101",
        user_id=5,
        issue_type="Hardware",
        description="Screen issue"
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_raise_service_ticket_database_exception(controller, mock_db):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    result = controller.raise_service_ticket(
        asset_no="TAG-101",
        user_id=5,
        issue_type="Hardware",
        description="Screen issue"
    )

    assert result is False


# =====================================================
# get_open_service_tickets()
# =====================================================

def test_get_open_service_tickets_success(
        controller,
        mock_db,
        admin_token
):
    cursor = MagicMock()

    cursor.fetchall.return_value = [
        {
            "ServiceId": 1,
            "AssetNo": "TAG-101",
            "ReportedBy": "John",
            "IssueType": "Hardware",
            "Description": "Keyboard not working"
        }
    ]

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_open_service_tickets(
        token=admin_token
    )

    assert len(result) == 1
    assert result[0]["AssetNo"] == "TAG-101"

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_open_service_tickets_empty(
        controller,
        mock_db,
        admin_token
):
    cursor = MagicMock()

    cursor.fetchall.return_value = []

    mock_db.connection.cursor.return_value = cursor

    result = controller.get_open_service_tickets(
        token=admin_token
    )

    assert result == []

    mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_get_open_service_tickets_database_exception(
        controller,
        mock_db,
        admin_token
):
    mock_db.connect.side_effect = Exception("Database Error")

    result = controller.get_open_service_tickets(
        token=admin_token
    )

    assert result == []


# =====================================================
# resolve_service_ticket()
# =====================================================

def test_resolve_service_ticket_success(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = {
        "AssetNo": "TAG-101"
    }

    result = controller.resolve_service_ticket(
        service_id=1,
        token=admin_token
    )

    assert result is True

    # update service request + update asset
    assert mock_db.execute_query.call_count == 2


def test_resolve_service_ticket_not_found(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = None

    result = controller.resolve_service_ticket(
        service_id=1,
        token=admin_token
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_resolve_service_ticket_database_exception(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    result = controller.resolve_service_ticket(
        service_id=1,
        token=admin_token
    )

    assert result is False


# =====================================================
# retire_asset()
# =====================================================

def test_retire_asset_success(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = {
        "AssetId": 101,
        "Status": "AVAILABLE"
    }

    result = controller.retire_asset(
        asset_no="TAG-101",
        token=admin_token
    )

    assert result is True

    mock_db.execute_query.assert_called_once()


def test_retire_asset_not_found(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = None

    result = controller.retire_asset(
        asset_no="TAG-999",
        token=admin_token
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_retire_asset_already_retired(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.return_value = {
        "AssetId": 101,
        "Status": "RETIRED"
    }

    result = controller.retire_asset(
        asset_no="TAG-101",
        token=admin_token
    )

    assert result is False

    mock_db.execute_query.assert_not_called()


def test_retire_asset_database_exception(
        controller,
        mock_db,
        admin_token
):
    mock_db.fetch_one.side_effect = Exception("Database Error")

    result = controller.retire_asset(
        asset_no="TAG-101",
        token=admin_token
    )

    assert result is False