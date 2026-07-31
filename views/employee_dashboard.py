# views/employee_dashboard.py
from tabulate import tabulate
from controllers.asset_controller import AssetController
from controllers.allocation_controller import AllocationController
from utils.logger import get_logger


log = get_logger(__name__)

class EmployeeDashboard:
    def __init__(self, user, token):
        self.user = user
        self.token = token
        self.asset_controller = AssetController()
        self.allocation_controller = AllocationController()

    def display_menu(self):
        """Main loop for the employee dashboard"""
        while True:
            print("\n"+"="*50)
            print(f"EMPLOYEE DASHBOARD - {self.user.name}")
            print("="*50)
            print("1. View Asset Catalog")
            print("2. Request New Asset")
            print("3. Return Asset")
            print("4. View My Allocated Assets")
            print("5. View Audit Tasks")
            print("6. Raise Service Ticket")
            print("7. Logout")

            choice = input("Enter your choice (1-7): ")

            if choice == '1':
                self._view_catalog()
            elif choice == '2':
                self._request_asset()
            elif choice == '3':
                self._return_asset()
            elif choice == '4':
                self._view_my_assets()
            elif choice == '5':
                self._view_audit_tasks()
            elif choice == '6':
                self._raise_ticket()
            elif choice == '7':
                print("Logging out...")
                break
            else:
                print("Invalid choice.")

    def _view_catalog(self):
        print("\n--- ASSET CATALOG ---")

        #use set to show available categories
        categories = self.asset_controller.get_unique_categories()
        if categories:
            print(f"Available Categories: {', '.join(categories)}\n")

        # consume the generator to build the list of dictionaries
        generator = self.asset_controller.get_available_assets_generator()

        # process the generator one by one and add to a standard list for the table
        asset_list = []
        for asset in generator:
            asset_list.append(asset)

        # print the table
        if not asset_list:
            print("No assets available.")
        else:
            print(tabulate(asset_list, headers="keys", tablefmt="grid"))

    def _request_asset(self):
        print("\n--- REQUEST NEW ASSET ---")
        self._view_catalog()

        asset_no = input("Enter the AssetNumber of the asset you want to request (e.g., TAG-001) or 'cancel': ")

        if asset_no.lower() == 'cancel':
            return

        self.allocation_controller.request_asset(asset_no, self.user.user_id)

    def _view_my_assets(self):
        print("\n--- MY ALLOCATED ASSETS ---")
        my_assets = self.allocation_controller.get_employee_assets(self.user.user_id)

        if not my_assets:
            print("No assets allocated to you.")
        else:
            print(tabulate(my_assets, headers="keys", tablefmt="grid"))

    def _return_asset(self):
        print("\n--- RETURN ASSET ---")
        self._view_my_assets()

        asset_no = input("Enter the Asset Number you want to return (e.g., TAG-001) or 'cancel': ")

        if asset_no.lower() == 'cancel':
            return

        self.allocation_controller.return_asset(asset_no, self.user.user_id)

    def _view_audit_tasks(self):
        print("\n---MY PENDING AUDITS ---")
        tasks = self.allocation_controller.get_audit_tasks(self.user.user_id)

        if not tasks:
            print("No pending audit tasks.")
            return 

        print(tabulate(tasks, headers="keys", tablefmt="grid"))

        action = input("\nEnter AllocationId to process, or press Enter to cancel: ")
        if action.isdigit():
            decision = input("Is the asset in good condition? (y/n): ")
            is_approves = decision.lower() == 'y'
            self.allocation_controller.submit_audit_result(int(action), self.user.user_id, is_approves)

    def _raise_ticket(self):
        print("\n--- RAISE SERVICE TICKET ---")
        self._view_my_assets()

        asset_no = input("Enter the Asset Number you want to raise a ticket for (e.g., TAG-001) or 'cancel': ")

        if asset_no.lower() == 'cancel':
            return

        print("\nIssue Type: 1=Malfunction, 2=REPAIR")
        issue_choice = input("Select Issue Type (1-2): ")
        issue_type = 'MALFUNCTION' if issue_choice == '1' else 'REPAIR'

        description = input("Describe the issue: ")

        self.allocation_controller.raise_service_ticket(asset_no, self.user.user_id, issue_type, description)