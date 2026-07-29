# controllers/allocation_controller.py
from models.db_manager import DatabaseManager
from utils.logger import get_logger
from utils.decorators import jwt_required

log = get_logger(__name__)

class AllocationController:
    def __init__(self):
        self.db = DatabaseManager()

    def request_asset(self, asset_no, user_id):
        # fetch asset to ensure it exists and is AVAILABLE
        asset = self.db.fetch_one("SELECT AssetId, Status FROM Assets WHERE AssetNo = %s", (asset_no,))

        if not asset:
            print(f"Error: Asset {asset_no} not found in the catalog.")
            return False

        if asset['Status'] != 'AVAILABLE':
            print(f"Error: Asset {asset_no} is currently {asset['Status']} and cannot be requested.")
            return False

        query = """
            INSERT INTO AssetAllocations (AssetId, UserId, Status) VALUES (%s, %s, 'REQUESTED')
        """

        try:
            self.db.execute_query(query, (asset['AssetId'], user_id))
            print(f"\nAsset requested successfully! The request is now pending Admin approval.")
            log.info(f"User {user_id} requested Asset {asset['AssetId']}.")
            return True
        except Exception as e:
            print("\nFailed to request asset.")
            log.error(f"Allocation request error: {e}")
            return False

    @jwt_required(allowed_roles=['ADMIN'])
    def get_pending_requests(self, token=None):
        query = """
            SELECT al.AllocationId, u.Name AS EmployeeName, a.AssetName, a.AssetNo, al.RequestDate
            FROM AssetAllocations al
            JOIN Users u ON al.UserId = u.UserId
            JOIN Assets a ON al.AssetId = a.AssetId
            WHERE al.Status = 'REQUESTED'
        """

        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            log.error(f"Failed to fetch pending requests: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            self.db.disconnect()

    @jwt_required(allowed_roles=['ADMIN'])
    def approve_request(self, allocation_id, token=None):
        try:
            alloc = self.db.fetch_one("SELECT AssetId FROM AssetAllocations WHERE AllocationId = %s AND Status = 'REQUESTED'", (allocation_id,))

            if not alloc: 
                print("Requests not found")
                return False

            self.db.execute_query("UPDATE AssetAllocations SET Status = 'ALLOCATED', AllocationDate = NOW() WHERE AllocationId = %s", (allocation_id,))

            self.db.execute_query("UPDATE Assets SET Status = 'ALLOCATED' WHERE AssetId = %s", (alloc['AssetId'],))

            print("Request Approved! The asset has been officially allocated.")
            return True
        except Exception as e:
            log.error(f"Failed to approve request: {e}")
            return False

    def get_employee_assets(self, user_id):
        query = """
            SELECT al.AllocationId, a.AssetName, a.AssetNo, al.AllocationDate, al.Status
            FROM AssetAllocations al
            JOIN Assets a ON al.AssetId = a.AssetId
            WHERE al.UserId = %s
        """

        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        except Exception as e:
            log.error(f"Failed to fetch employee assets: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            self.db.disconnect()

    def return_asset(self, asset_no, user_id):
        # check query
        check_query = """
            SELECT al.AllocationId, a.AssetId
            FROM AssetAllocations al
            JOIN Assets a ON al.AssetId = a.AssetId
            WHERE a.AssetNo = %s AND al.UserId = %s AND al.Status = 'ALLOCATED'
        """

        try:
            alloc = self.db.fetch_one(check_query, (asset_no, user_id))

            if not alloc:
                print(f"Error: You do not currently have Asset {asset_no} allocated to you.")
                return False

            # update the allocation record
            self.db.execute_query(
                "UPDATE AssetAllocations SET Status = 'RETURNED', ActualReturnDate = NOW() WHERE AllocationId = %s", (alloc['AllocationId'],)
            )

            # update the asset catalog status back to AVAILABLE
            self.db.execute_query(
                "UPDATE Assets SET Status = 'AVAILABLE' WHERE AssetId = %s", (alloc['AssetId'],)
            )

            print(f"\nSuccessfully returned {asset_no}. Thank You!")
            log.info(f"User {user_id} returned Asset {alloc['AssetId']}.")
            return True
        except Exception as e:
            print("\nFailed to return asset.")
            log.error(f"Asset return error: {e}")
            return False