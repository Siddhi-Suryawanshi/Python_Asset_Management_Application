class User:
    """Base class: User"""
    def __init__(self, user_id, name, email, role):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role

    def get_role_description(self):
        return "I am a generic user."

class Employee(User):
    def __init__(self, user_id, name, email):
        super().__init__(user_id, name, email, role="EMPLOYEE")

    def get_role_description(self):
        return "I am an Employee. I can request and return assets."

class Admin(User):
    def __init__(self, user_id, name, email):
        super().__init__(user_id, name, email, role="ADMIN")

    def get_role_description(self):
        return "I am an Admin. I manage the asset catalog and system audits."