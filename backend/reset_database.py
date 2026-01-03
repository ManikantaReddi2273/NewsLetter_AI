"""Reset database script."""
import pymysql
from app.config import get_settings

settings = get_settings()

try:
    # Connect without selecting a database
    connection = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD
    )
    
    with connection.cursor() as cursor:
        # Drop and recreate database
        cursor.execute("DROP DATABASE IF EXISTS newsletter_db")
        cursor.execute("CREATE DATABASE newsletter_db")
        print("✅ Database 'newsletter_db' recreated successfully!")
        
        # Show databases
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print("\n📋 Available databases:")
        for db in databases:
            print(f"  - {db[0]}")
    
    connection.close()
    print("\n✅ Database reset complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
