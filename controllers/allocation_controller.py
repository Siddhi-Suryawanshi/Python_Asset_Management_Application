# controllers/allocation_controller.py
from models.db_manager import DatabaseManager
from utils.logger import get_logger
from utils.decorators import jwt_required

log = get_logger(__name__)

class AllocationController:
    def __init__(self):
        self.db = DatabaseManager()

    def request_asset(self, asset_no, user_id):
        """Allows an employee to request an available asset."""
        try:
            # Fetch asset to ensure it exists
            asset = self.db.fetch_one(
                "SELECT AssetId, Status FROM Assets WHERE AssetNo = %s",
                (asset_no,)
            )

            if not asset:
                print(f"Error: Asset {asset_no} not found in the catalog.")
                return False

            if asset["Status"] != "AVAILABLE":
                print(
                    f"Error: Asset {asset_no} is currently {asset['Status']} "
                    "and cannot be requested."
                )
                return False

            query = """
                INSERT INTO AssetAllocations (AssetId, UserId, Status)
                VALUES (%s, %s, 'REQUESTED')
            """

            self.db.execute_query(query, (asset["AssetId"], user_id))

            print("\nAsset requested successfully! The request is now pending Admin approval.")
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
    def assign_auditor(self, allocation_id, auditor_id, token=None):
        try:
            alloc = self.db.fetch_one(
                "SELECT UserId FROM AssetAllocations WHERE AllocationId = %s AND Status = 'REQUESTED'", (allocation_id,)
            )

            if not alloc:
                print("Request not found or already assigned.")
                return False

            if alloc['UserId'] == auditor_id:
                print("\nSECURITY BLOCK: An employee cannot be assigned to audit their own asset request!")
                return False

            self.db.execute_query(
                "UPDATE AssetAllocations SET Status = 'PENDING_AUDIT', AuditorId = %s WHERE AllocationId = %s AND Status = 'REQUESTED'", (auditor_id, allocation_id) 
            )

            print(f"Auditor {auditor_id} assigned successfully! Status is now PENDING_AUDIT.")
            return True
        except Exception as e:
            print("Failed to assign auditor.")
            log.error(f"Assign auditor error: {e}")
            return False

    def get_audit_tasks(self, auditor_id):
        query = """
            SELECT al.AllocationId, u.Name AS Requester, a.AssetName, a.AssetNo 
            FROM AssetAllocations al
            JOIN Users u ON al.UserId = u.UserId
            JOIN Assets a ON al.AssetId = a.AssetId
            WHERE al.AuditorId = %s AND al.Status = 'PENDING_AUDIT'
        """

        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query, (auditor_id,))
            return cursor.fetchall()
        except Exception as e:
            log.error(f"Failed to fetch audit tasks: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            self.db.disconnect()

    

    def submit_audit_result(self, allocation_id, auditor_id, is_approved):
        """Step 3b: Employee submits their audit findings, checking for maintenance issues."""
        try:
            # Check if the asset attached to this allocation is under maintenance
            asset_check_query = """
                SELECT a.Status 
                FROM AssetAllocations al
                JOIN Assets a ON al.AssetId = a.AssetId
                WHERE al.AllocationId = %s
            """
            asset = self.db.fetch_one(asset_check_query, (allocation_id,))
            
            # The Warning Logic!
            if asset and asset['Status'] == 'IN_MAINTENANCE' and is_approved:
                print("\n⚠️ WARNING: This asset is currently marked as IN_MAINTENANCE!")
                print("You cannot approve an audit for an asset that requires repairs.")
                return False

            new_status = 'AUDIT_APPROVED' if is_approved else 'AUDIT_DENIED'

            self.db.execute_query(
                "UPDATE AssetAllocations SET Status = %s WHERE AllocationId = %s AND AuditorId = %s",
                (new_status, allocation_id, auditor_id)
            )
            print(f"✅ Audit submitted! Status updated to {new_status}.")
            return True
        except Exception as e:
            print("❌ Failed to submit audit.")
            log.error(f"Submit audit error: {e}")
            return False

    @jwt_required(allowed_roles=['ADMIN'])
    def get_audited_requests(self, token=None):
        query = """
            SELECT al.AllocationId, u.Name AS Requester, au.Name AS Auditor, a.AssetName, a.AssetNo 
            FROM AssetAllocations al
            JOIN Users u ON al.UserId = u.UserId
            JOIN Users au ON al.AuditorId = au.UserId
            JOIN Assets a ON al.AssetId = a.AssetId
            WHERE al.Status = 'AUDIT_APPROVED'
        """

        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            log.error(f"Failed to fetch audited requests: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor: cursor.close()
            self.db.disconnect()

    @jwt_required(allowed_roles=['ADMIN'])
    def approve_request(self, allocation_id, token=None):
        try:
            alloc = self.db.fetch_one("SELECT AssetId FROM AssetAllocations WHERE AllocationId = %s AND Status = 'AUDIT_APPROVED'", (allocation_id,))

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

    @jwt_required(allowed_roles=['ADMIN'])
    def get_employee_list(self, token=None):
        query = "SELECT UserId, Name, Email FROM Users WHERE Role = 'EMPLOYEE'"
        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            log.error(f"Failed to fetch employee list: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            self.db.disconnect()

    def raise_service_ticket(self, asset_no, user_id, issue_type, description):
        """Allows an employee to raise a service ticket and return the broken asset."""
        # 1. Verify the user actually owns this asset right now
        check_query = """
            SELECT al.AllocationId, a.AssetId 
            FROM AssetAllocations al
            JOIN Assets a ON al.AssetId = a.AssetId
            WHERE a.AssetNo = %s AND al.UserId = %s AND al.Status = 'ALLOCATED'
        """
        try:
            alloc = self.db.fetch_one(check_query, (asset_no, user_id))
            
            if not alloc:
                print(f"❌ Error: You do not currently have Asset '{asset_no}' allocated to you.")
                return False

            # 2. Insert the service request (Stripped down to basic columns)
            insert_ticket_query = """
                INSERT INTO ServiceRequests 
                (AssetNo, UserId, IssueType, Description, Status)
                VALUES (%s, %s, %s, %s, 'OPEN')
            """
            self.db.execute_query(insert_ticket_query, (asset_no, user_id, issue_type, description))

            # 3. End the employee's allocation
            self.db.execute_query(
                "UPDATE AssetAllocations SET Status = 'RETURNED', ActualReturnDate = NOW() WHERE AllocationId = %s", 
                (alloc['AllocationId'],)
            )

            # 4. Update the physical Asset to IN_MAINTENANCE
            self.db.execute_query(
                "UPDATE Assets SET Status = 'IN_MAINTENANCE' WHERE AssetId = %s", 
                (alloc['AssetId'],)
            )
            
            print(f"\n✅ Ticket raised for {asset_no}. You have returned the asset to IT for maintenance.")
            return True
            
        except Exception as e:
            print("\n❌ Failed to raise service ticket.")
            log.error(f"Service ticket error: {e}")
            return False

    @jwt_required(allowed_roles=['ADMIN'])
    def get_open_service_tickets(self, token=None):
        """Fetches all open service tickets for the Admin to review."""
        query = """
            SELECT sr.ServiceId, sr.AssetNo, u.Name AS ReportedBy, sr.IssueType, sr.Description, sr.RequestDate
            FROM ServiceRequests sr
            JOIN Users u ON sr.UserId = u.UserId
            WHERE sr.Status = 'OPEN'
        """
        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            log.error(f"Failed to fetch open tickets: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor: cursor.close()
            self.db.disconnect()

    @jwt_required(allowed_roles=['ADMIN'])
    def resolve_service_ticket(self, service_id, token=None):
        """Marks a ticket as RESOLVED and makes the asset AVAILABLE again."""
        try:
            # 1. Get the AssetNo associated with this ticket
            ticket_check = self.db.fetch_one(
                "SELECT AssetNo FROM ServiceRequests WHERE ServiceId = %s AND Status = 'OPEN'",
                (service_id,)
            )

            if not ticket_check:
                print("❌ Ticket not found or is already resolved.")
                return False

            asset_no = ticket_check['AssetNo']

            # 2. Update the ticket status to RESOLVED
            self.db.execute_query(
                "UPDATE ServiceRequests SET Status = 'RESOLVED' WHERE ServiceId = %s",
                (service_id,)
            )

            # 3. Update the actual Asset back to AVAILABLE
            self.db.execute_query(
                "UPDATE Assets SET Status = 'AVAILABLE' WHERE AssetNo = %s",
                (asset_no,)
            )

            print(f"\n✅ Ticket #{service_id} resolved! Asset {asset_no} is now AVAILABLE for allocation.")
            return True
            
        except Exception as e:
            print("\n❌ Failed to resolve ticket.")
            log.error(f"Resolve ticket error: {e}")
            return False

    @jwt_required(allowed_roles=['ADMIN'])
    def retire_asset(self, asset_no, token=None):
        """Soft deletes an asset by marking it as RETIRED."""
        try:
            # 1. Verify the asset exists
            asset = self.db.fetch_one("SELECT AssetId, Status FROM Assets WHERE AssetNo = %s", (asset_no,))
            
            if not asset:
                print(f"❌ Error: Asset '{asset_no}' not found in the database.")
                return False

            if asset['Status'] == 'RETIRED':
                print(f"⚠️ Asset '{asset_no}' is already retired.")
                return False
                
            # Optional: You could add a check here to ensure the status isn't 'ALLOCATED' 
            # to prevent retiring a laptop that someone is currently using!

            # 2. Perform the Soft Delete
            self.db.execute_query(
                "UPDATE Assets SET Status = 'RETIRED' WHERE AssetNo = %s",
                (asset_no,)
            )

            print(f"\n✅ Asset '{asset_no}' has been successfully RETIRED. It is removed from circulation.")
            log.info(f"Asset {asset_no} was retired by Admin.")
            return True
            
        except Exception as e:
            print("\n❌ Failed to retire asset.")
            log.error(f"Retire asset error: {e}")
            return False