import functools
import jwt
from config import JWT_SECRET_KEY, JWT_ALGORITHM
from utils.logger import get_logger

log = get_logger(__name__)

def jwt_required(allowed_roles=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token = kwargs.get('token')

            if not token:
                print("\nAccess Denied: Missing JWT token. Please log in.")
                return None

            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

                if allowed_roles and payload['role'] not in allowed_roles:
                    print(f"\n❌ Access Denied: Requires roles {allowed_roles}. You are an {payload['role']}.")
                    log.warning(f"Unauthorized role access attempt by User ID {payload['user_id']}")
                    return None

                return func(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                print("\nAccess Denied: JWT token has expired. Please log in again.")
                return None

            except jwt.InvalidTokenError:
                print("\nAccess Denied: Invalid JWT token. Please log in again.")
                return None

        return wrapper

    return decorator