# views/admin_dashboard.py
from tabulate import tabulate
from controllers.asset_controller import AssetController
from controllers.allocation_controller import AllocationController
from utils.logger import get_logger



log = get_logger(__name__)

class AdminDashboard:
    def __init__(self, user, token):
        self.user = user
        self.token = token
        self.asset_controller = AssetController()
        self.allocation_controller = AllocationController()

    def display_menu(self):
        while True:
            print("\n" + "="*50)
            print(f"ADMIN DASHBOARD - {self.user.name}")
            print("="*50)
            print("1. Add New Asset")
            print("2. View All Assets")
            print("3. Assign Auditor to New Requests")
            print("4. Finalize Audited Requests")
            print("5. View Inventory Summary")
            print("6. Manage Service Desk")
            print("7. Retire an Asset")
            print("8. Logout")

            choice = input("Enter your choice (1-8): ")

            if choice == '1':
                self._add_new_asset()
            elif choice == '2':
                self._view_all_assets()
            elif choice == '3':
                self._assign_auditor()
            elif choice == '4':
                self._finalize_requests()
            elif choice == '5':
                self._view_summary()
            elif choice == '6':
                self._manage_service_desk()
            elif choice == '7':
                self._retire_asset()
            elif choice == '8':
                print("Logging out...")
                break
            else:
                print("Invalid choice.")

    def _add_new_asset(self):
        
        print("\n--- ADD NEW ASSET ---")
        asset_no = input("Asset Number (e.g., TAG-001): ")
        name = input("Asset Name (e.g., Dell XPS 15): ")
        
        print("\nCategories: 1=Laptops, 2=Vehicles, 3=Furniture, 4=Software")
        try:
            category_id = int(input("Enter Category ID (1-4): "))
            model = input("Asset Model: ")
            value = float(input("Asset Value ($): "))
            
            # Notice how we pass token=self.token so the Decorator can verify it!
            self.asset_controller.add_asset(
                asset_no, name, category_id, model, value, token=self.token
            )
        except ValueError:
            print("❌ Invalid input. Category ID and Value must be numbers.")


    def _view_all_assets(self, token=None):
        print("\n--- ALL SYSTEM ASSETS ---")

        generator = self.asset_controller.get_all_assets_generator(token=self.token)

        asset_list = [asset for asset in generator]

        if not asset_list:
            print("No assets available.")
        else:
            print(tabulate(asset_list, headers="keys", tablefmt="grid"))

    def _assign_auditor(self):
        print("\n--- NEW ASSET REQUESTS ---")
        requests = self.allocation_controller.get_pending_requests(token=self.token)

        if not requests:
            print("No new requests at this time.")
            return

        print(tabulate(requests, headers="keys", tablefmt="grid"))

        alloc_id = input("\nEnter AllocationId to assign an auditor (or Enter to cancel): ")


        if alloc_id.isdigit():
            # NEW: Fetch and print the user directory before asking for the ID
            print("\n--- AVAILABLE EMPLOYEES ---")
            employees = self.allocation_controller.get_employee_list(token=self.token)
            if employees:
                 print(tabulate(employees, headers="keys", tablefmt="simple"))
            else:
                 print("Warning: No employees found in the system to assign!")
                 return
            
            auditor_id = input("Enter the UserId of the Employee to audit this asset:")
            if auditor_id.isdigit():
                self.allocation_controller.assign_auditor(int(alloc_id), int(auditor_id), token=self.token)

        

    def _finalize_requests(self):
        print("\n--- AUDITED REQUESTS READY FOR FINAL APPROVAL ---")
        requests = self.allocation_controller.get_audited_requests(token=self.token)

        if not requests:
            print("No audited requests waiting for approval")
            return

        print(tabulate(requests, headers="keys", tablefmt="grid"))

        action = input("\nEnter AllocationId to finalize approval (or Enter to cancel): ")

        if action.isdigit():
            self.allocation_controller.approve_request(int(action), token=self.token)

    def _view_summary(self, token=None):
        print("\n--- GLOBAL INVENTORY SUMMARY ---")
        summary_data = self.asset_controller.get_inventory_summary(token=self.token)

        if not summary_data:
            print("No inventory data available.")
        else:
            print(tabulate(summary_data, headers="keys", tablefmt="fancy_grid"))

    def _manage_service_desk(self):
        print("\n--- IT SERVICE DESK (OPEN TICKETS) ---")
        tickets = self.allocation_controller.get_open_service_tickets(token=self.token)

        if not tickets:
            print("No open service tickets at this time. Great job!")
            return

        print(tabulate(tickets, headers="keys", tablefmt="grid"))

        ticket_id = input("\nEnter ServiceId to mark as RESOLVED (or Enter to cancel): ")

        if ticket_id.isdigit():
            self.allocation_controller.resolve_service_ticket(int(ticket_id), token=self.token)

    def _retire_asset(self):
        print("\n--- RETIRE ASSET (SOFT DELETE) ---")
        
        # Show the assets so the Admin knows the AssetNo
        self._view_all_assets()
        
        asset_no = input("\nEnter the Asset Number to RETIRE (or 'cancel'): ")
        
        if asset_no.lower() == 'cancel':
            return
            
        confirm = input(f"⚠️ Are you sure you want to permanently retire {asset_no}? (y/n): ")
        
        if confirm.lower() == 'y':
            self.allocation_controller.retire_asset(asset_no, token=self.token)
        else:
            print("Operation cancelled.")