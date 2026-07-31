# controllers/asset_controller.py
from models.db_manager import DatabaseManager
from utils.logger import get_logger
from utils.decorators import jwt_required

log = get_logger(__name__)

class AssetController:
    def __init__(self):
        self.db = DatabaseManager()

    def get_available_assets_generator(self):
        """Yields only AVAILABLE assets for employees."""
        query = """
            SELECT a.AssetNo, a.AssetName, c.CategoryName, a.AssetModel, a.Status
            FROM Assets a
            JOIN AssetCategories c ON a.CategoryId = c.CategoryId
            WHERE a.Status = 'AVAILABLE'
        """
        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query)
            
            # Fetch all rows into memory first to avoid unbuffered cursor crashes
            rows = cursor.fetchall()
            for row in rows:
                yield row
                
        except Exception as e:
            log.error(f"Generator failed to fetch available assets: {e}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            self.db.disconnect()

    @jwt_required(allowed_roles=['ADMIN'])
    def get_all_assets_generator(self, token=None):
        """Yields ALL assets for the Admin view."""
        query = """
            SELECT a.AssetNo, a.AssetName, c.CategoryName, a.AssetModel, a.Status
            FROM Assets a
            JOIN AssetCategories c ON a.CategoryId = c.CategoryId
        """
        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query)
            
            rows = cursor.fetchall()
            for row in rows:
                yield row
                
        except Exception as e:
            log.error(f"Generator failed to fetch all assets: {e}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            self.db.disconnect()

    def get_unique_categories(self):
        query = "SELECT CategoryName FROM AssetCategories"
        try:
            self.db.connect()
            cursor = self.db.connection.cursor()
            cursor.execute(query)
            unique_categories = {row[0] for row in cursor.fetchall()}
            return unique_categories
        except Exception as e:
            log.error(f"Failed to fetch categories: {e}")
            return set()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            self.db.disconnect()

    @jwt_required(allowed_roles=['ADMIN'])
    def add_asset(self, asset_no, name, category_id, model, value, token=None):
        query = """
            INSERT INTO Assets (AssetNo, AssetName, CategoryId, AssetModel, AssetValue) 
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            self.db.execute_query(query, (asset_no, name, category_id, model, value))
            print(f"\n✅ Successfully added Asset: {name} ({asset_no})")
            log.info(f"Asset added: {name} {asset_no}")
            return True
        except Exception as e:
            print("\n❌ Failed to add asset. Check if Asset Number already exists.")
            log.error(f"Failed to add asset: {e}")
            return False

    @jwt_required(allowed_roles=['ADMIN'])
    def get_inventory_summary(self, token=None):
        """Fetches the bulk count of specific hardware models."""
        query = """
            SELECT 
                c.CategoryName,
                a.AssetName,
                COUNT(*) as TotalOwned,
                SUM(CASE WHEN a.Status = 'AVAILABLE' THEN 1 ELSE 0 END) as TotalAvailable,
                SUM(CASE WHEN a.Status = 'ALLOCATED' THEN 1 ELSE 0 END) as TotalAllocated
            FROM Assets a
            JOIN AssetCategories c ON a.CategoryId = c.CategoryId
            GROUP BY c.CategoryName, a.AssetName
            ORDER BY c.CategoryName, a.AssetName
        """

        try:
            self.db.connect()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            log.error(f"Failed to fetch detailed inventory summary: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            self.db.disconnect()