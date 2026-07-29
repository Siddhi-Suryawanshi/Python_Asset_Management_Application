from views.console_view import ConsoleView
from utils.logger import get_logger
from views.employee_dashboard import EmployeeDashboard
from views.admin_dashboard import AdminDashboard

log = get_logger(__name__)

def main():
    log.info("Application started.")

    while True:
        view = ConsoleView()

        logged_in_user, token = view.display_startup_menu()

        if logged_in_user and token:
            print("\n"+"*"*50)
            print(f"Welcome, {logged_in_user.name}!")

            print(f"System: {logged_in_user.get_role_description()}")
            print(f"\n JWT Generated: {token[:30]}... (truncated)")
            print("*"*50)

            

            # route to correct dashboard 
            if logged_in_user.role == 'ADMIN':
                print("\n[Admin Dashboard Module loading...]")

                admin_dashboard = AdminDashboard(logged_in_user, token)
                admin_dashboard.display_menu()
            else:
                print("\n[Employee Dashboard Module loading...]")

                emp_dashboard = EmployeeDashboard(logged_in_user, token)
                emp_dashboard.display_menu()

        log.info("Application closed.")

if __name__ == '__main__':
    main()