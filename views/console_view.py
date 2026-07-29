import getpass
from controllers.auth_controller import AuthController
from utils.logger import get_logger

log = get_logger(__name__)

class ConsoleView:
    def __init__(self):
        self.auth_controller = AuthController()

    def display_startup_menu(self):
        while True:
            print("\n" + "="*50)
            print(" EMPLOYEE ENTERPRISE ASSET MANAGEMENT SYSTEM")
            print("="*50)
            print("1. Login")
            print("2. Register (Employee/Admin)")
            print("3. Exit")

            choice = input("Enter your choice (1-3): ")

            if choice == '1':
                user, token = self._handle_login()
                if user and token:
                    return user, token
            elif choice == '2':
                self._handle_register()
            elif choice == '3':
                print("Exiting application. Have a Nice Day!")
                # return None, None
                exit()
            else:
                print("Invalid choice. Please try again.")

    def _handle_login(self):
        print("\n--- LOGIN ---")
        email = input("Enter your email: ")
        password = getpass.getpass("Enter your password: ")
        return self.auth_controller.login(email, password)

    def _handle_register(self):
        print("\n--- REGISTRATION ---")
        name = input("Full Name: ")
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        gender = input("Gender (Male/Female): ")
        contact = input("Contact Number (10 digits): ")
        address = input("Address: ")

        role_input = input("Role (EMPLOYEE/ADMIN) [Press Enter for default EMPLOYEE]: ").upper()
        role = role_input if role_input in ['EMPLOYEE', 'ADMIN'] else 'EMPLOYEE'

        self.auth_controller.register_user(name, email, password, gender, contact, address, role)