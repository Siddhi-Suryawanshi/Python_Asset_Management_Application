import jwt
import datetime
from config import JWT_SECRET_KEY, JWT_ALGORITHM
import bcrypt
from models.db_manager import DatabaseManager
from models.user_model import Employee, Admin
from utils.validators import is_valid_email, is_valid_phone
from utils.logger import get_logger

log = get_logger(__name__)

class AuthController:
    def __init__(self):
        
        self.db = DatabaseManager()

    def _hash_password(self, password):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def register_user(self, name, email, password, gender, contact, address, role='EMPLOYEE'):
        try:
            if not is_valid_email(email):
                print("Invalid email format.")
                return False
            if contact and not is_valid_phone(contact):
                print("Invalid phone number. Must be 10 digits.")
                return False

            existing = self.db.fetch_one("SELECT Email FROM Users WHERE Email = %s", (email,))
            if existing:
                print("Email already registered.")
                return False

            hashed_pw = self._hash_password(password)
            query = """
                INSERT INTO Users (Name, Email, PasswordHash, Gender, ContactNumber, Address, Role) VALUES (%s, %s, %s, %s, %s, %s, %s)"""

            self.db.execute_query(query, (name, email, hashed_pw, gender, contact, address, role))
            print(f"Registration successful for {name}!")
            log.info(f"New user registered: {email}")
            return True

        except Exception as e:
            print("Registration failed due to a system error.")
            log.error(f"Registration error: {e}")
            return False

    def login(self, email, password):
        try:
            user_data = self.db.fetch_one("SELECT * FROM Users WHERE Email = %s", (email,))

            if user_data:
                hashed_pw = user_data['PasswordHash'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
                    payload = {
                        "user_id": user_data['UserId'],
                        "role": user_data['Role'],
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)                    
                    }
                    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

                    if user_data['Role'] == 'ADMIN':
                        log.info(f"Admin logged in: {email}")
                        user_obj = Admin(user_data['UserId'], user_data['Name'], user_data['Email'])
                    else:
                        log.info(f"Employee logged in: {email}")
                        user_obj = Employee(user_data['UserId'], user_data['Name'], user_data['Email'])
                    
                    # 4. Return BOTH object and token
                    return user_obj, token
                else:
                    print("Invalid password.")
            else:
                print("User not found or account is inactive.")

            return None, None

        except Exception as e:
            print("Login failed due to a system error.")
            log.error(f"Login error: {e}")
            return None, None