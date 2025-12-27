from pymysql import connect as mysql_connect
from psycopg2 import connect as pg_connect


class DatabaseManager:
    def __init__(self, db_name, host, port, username, password, db_type="mysql"):
        self.db_type = db_type.lower()
        self.db_name = db_name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        try:
            if self.db_type == "postgresql":
                self.connection = pg_connect(
                    dbname=self.db_name,
                    user=self.username,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
            elif self.db_type == "mysql":
                self.connection = mysql_connect(
                    database=self.db_name,
                    user=self.username,
                    password=self.password,
                    host=self.host,
                    port=int(self.port)
                )
            else:
                raise ValueError("Unsupported database type")

            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            print("🔒 Database connection closed")

    def extract_all_tables(self):
        if not self.connection:
            raise RuntimeError("Database not connected")

        query_pg = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """

        query_mysql = "SHOW TABLES"

        with self.connection.cursor() as cursor:
            cursor.execute(query_pg if self.db_type == "postgresql" else query_mysql)
            return [row[0] for row in cursor.fetchall()]

    def describe_table(self, table_name):
        if not self.connection:
            raise RuntimeError("Database not connected")

        if self.db_type == "postgresql":
            query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
            """
        else:
            query = f"DESCRIBE `{table_name}`"

        with self.connection.cursor() as cursor:
            if self.db_type == "postgresql":
                cursor.execute(query, (table_name,))
            else:
                cursor.execute(query)

            return cursor.fetchall()

    def describe_all_tables(self):
        schema = {}
        tables = self.extract_all_tables()

        for table in tables:
            schema[table] = self.describe_table(table)

        return schema

    def query_database(self, query, params=None):
        if not self.connection:
            raise RuntimeError("Database not connected")
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                # Store column info for later use
                if hasattr(cursor, 'description') and cursor.description:
                    self._last_columns = [desc[0] for desc in cursor.description]
                else:
                    self._last_columns = []
                return results
        except Exception as e:
            return f"Error executing query: {e}"

    def get_last_columns(self):
        return getattr(self, '_last_columns', [])

    def test_connection(self):
        try:
            if not self.connect():
                return False, "Failed to connect to database"
            
            # Test with a simple query
            if self.db_type == "postgresql":
                test_query = "SELECT 1"
            else:  # MySQL
                test_query = "SELECT 1"
            
            with self.connection.cursor() as cursor:
                cursor.execute(test_query)
                result = cursor.fetchone()
                if result and result[0] == 1:
                    return True, "Connection successful"
                else:
                    return False, "Unexpected test query result"
                    
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
        finally:
            self.close()
            
    def get_database_info(self):
        if not self.connect():
            return "Not connected to any database"
            
        try:
            info = {
                "database_name": self.db_name,
                "database_type": self.db_type,
                "tables": [],
                "size": "N/A",
                "version": "N/A"
            }
            
            # Get database version
            if self.db_type == "postgresql":
                version_query = "SELECT version()"
            else:  # MySQL
                version_query = "SELECT VERSION()"
            
            with self.connection.cursor() as cursor:
                cursor.execute(version_query)
                info["version"] = cursor.fetchone()[0]
                
                # Get database size
                if self.db_type == "postgresql":
                    cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                else:  # MySQL
                    cursor.execute("""
                        SELECT 
                            table_schema AS 'Database', 
                            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
                        FROM information_schema.TABLES 
                        WHERE table_schema = DATABASE()
                        GROUP BY table_schema
                    """)
                size_result = cursor.fetchone()
                if size_result:
                    info["size"] = size_result[0]
                
                # Get table counts
                if self.db_type == "postgresql":
                    cursor.execute("""
                        SELECT 
                            table_name,
                            pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
                            (SELECT count(*) FROM information_schema.columns 
                             WHERE table_name = t.table_name) as column_count
                        FROM information_schema.tables t
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                else:  # MySQL
                    cursor.execute("""
                        SELECT 
                            table_name,
                            ROUND(((data_length + index_length) / 1024 / 1024), 2) as size_mb,
                            (SELECT COUNT(*) 
                             FROM information_schema.columns 
                             WHERE table_schema = DATABASE() 
                             AND table_name = t.table_name) as column_count
                        FROM information_schema.tables t
                        WHERE table_schema = DATABASE()
                        ORDER BY table_name
                    """)
                
                for table in cursor.fetchall():
                    info["tables"].append({
                        "name": table[0],
                        "size": table[1],
                        "columns": table[2]
                    })
            
            return info
            
        except Exception as e:
            return f"Error getting database info: {str(e)}"
        finally:
            self.close()