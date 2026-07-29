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
            print("3. View Pending Requests")
            print("4. Logout")

            choice = input("Enter your choice (1-3): ")

            if choice == '1':
                self._add_new_asset()
            elif choice == '2':
                self._view_all_assets()
            elif choice == '3':
                self._view_pending_requests()
            elif choice == '4':
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

    def _view_pending_requests(self):
        print("\n--- PENDING ASSET REQUESTS ---")
        requests = self.allocation_controller.get_pending_requests(token=self.token)

        if not requests:
            print("No pending requests.")
        print(tabulate(requests, headers="keys", tablefmt="grid"))

        action = input("\nEnter AllocationId to approve, or press Enter to cancel: ")
        if action.isdigit():
            self.allocation_controller.approve_request(int(action), token=self.token)