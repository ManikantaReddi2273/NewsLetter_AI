"""Quick database setup and test script."""
import pymysql
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings

settings = get_settings()

print("🔍 Checking database connection...")
print(f"Host: {settings.MYSQL_HOST}")
print(f"Database: {settings.MYSQL_DATABASE}")
print(f"User: {settings.MYSQL_USER}")

try:
    # Connect without selecting a database
    connection = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD
    )
    
    print("✅ MySQL connection successful!")
    
    with connection.cursor() as cursor:
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS newsletter_db")
        print("✅ Database 'newsletter_db' created/verified!")
        
        # Use the database
        cursor.execute("USE newsletter_db")
        
        # Show tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📋 Existing tables: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\n⚠️  No tables found. Database needs initialization.")
    
    connection.close()
    
    print("\n✅ Database is ready!")
    print("\n📝 Next steps:")
    print("1. Run: python init_database.py  (to create tables)")
    print("2. Run: python scripts/setup_faiss_index.py  (to add sample data)")
    print("3. Run: python main.py  (to start the API)")
    
except Exception as e:
    print(f"\n❌ Database error: {e}")
    print("\n💡 Please check:")
    print("1. MySQL is running")
    print("2. Password in .env is correct")
    print("3. MySQL user has permissions")
