"""Migration script to add Phase 2 columns to articles table."""
import pymysql
from app.config import get_settings

settings = get_settings()

def migrate():
    """Add Phase 2 columns to articles table."""
    try:
        # Parse database URL
        # Format: mysql+pymysql://user:password@host:port/database
        db_url = settings.database_url.replace('mysql+pymysql://', '')
        auth, host_db = db_url.split('@')
        user, password = auth.split(':')
        host_port, database = host_db.split('/')
        
        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 3306
        
        # Connect to MySQL
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✅ Connected to database: {database}")
        
        with connection.cursor() as cursor:
            # Check if columns already exist
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'articles'
                AND COLUMN_NAME IN ('fact_check_status', 'bias_explanation', 'deep_dive_content')
            """, (database,))
            
            existing_columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
            print(f"Existing Phase 2 columns: {existing_columns}")
            
            # Add missing columns
            if 'fact_check_status' not in existing_columns:
                print("Adding column: fact_check_status...")
                cursor.execute("""
                    ALTER TABLE articles 
                    ADD COLUMN fact_check_status VARCHAR(20) DEFAULT NULL
                """)
                print("✅ Added fact_check_status")
            else:
                print("⏭️  fact_check_status already exists")
            
            if 'bias_explanation' not in existing_columns:
                print("Adding column: bias_explanation...")
                cursor.execute("""
                    ALTER TABLE articles 
                    ADD COLUMN bias_explanation TEXT DEFAULT NULL
                """)
                print("✅ Added bias_explanation")
            else:
                print("⏭️  bias_explanation already exists")
            
            if 'deep_dive_content' not in existing_columns:
                print("Adding column: deep_dive_content...")
                cursor.execute("""
                    ALTER TABLE articles 
                    ADD COLUMN deep_dive_content TEXT DEFAULT NULL
                """)
                print("✅ Added deep_dive_content")
            else:
                print("⏭️  deep_dive_content already exists")
            
            connection.commit()
            print("\n✅ Migration complete! Phase 2 columns added to articles table.")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    migrate()
