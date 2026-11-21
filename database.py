import os
import sqlite3
import pymysql
import pymysql.cursors
from config import Config

# Global variable to track active engine: 'mysql' or 'sqlite'
DB_ENGINE = None

def get_db_connection(use_database=True):
    """
    Establish and return a database connection.
    Attempts MySQL first using credentials from .env.
    If MySQL connection fails, seamlessly falls back to local SQLite database.
    """
    global DB_ENGINE

    # Try MySQL first if not explicitly fallback
    if DB_ENGINE != 'sqlite':
        try:
            kwargs = {
                'host': Config.MYSQL_HOST,
                'port': Config.MYSQL_PORT,
                'user': Config.MYSQL_USER,
                'password': Config.MYSQL_PASSWORD,
                'cursorclass': pymysql.cursors.DictCursor,
                'autocommit': False,
                'charset': 'utf8mb4'
            }
            if use_database:
                kwargs['database'] = Config.MYSQL_DB
            
            conn = pymysql.connect(**kwargs)
            DB_ENGINE = 'mysql'
            return conn
        except (pymysql.MySQLError, Exception) as err:
            if DB_ENGINE is None:
                print(f"[MySQL Notice] Could not connect to MySQL ({err}).")
                print("[MySQL Notice] Falling back to local SQLite database (instance/smart_expense_tracker.db).")
                print("[MySQL Notice] Update MYSQL_PASSWORD in .env anytime to switch to MySQL.")
            DB_ENGINE = 'sqlite'

    # SQLite Fallback Connection
    instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'smart_expense_tracker.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Register MySQL compatible SQL functions in SQLite
    def _year(d):
        if not d: return None
        return int(str(d).split('-')[0])

    def _month(d):
        if not d: return None
        return int(str(d).split('-')[1])

    def _coalesce_sum(val):
        return val if val is not None else 0

    conn.create_function('YEAR', 1, _year)
    conn.create_function('MONTH', 1, _month)
    return conn

def init_db():
    """
    Initializes database tables and default category seeds for MySQL or SQLite fallback.
    """
    global DB_ENGINE
    try:
        # Step 1: Attempt MySQL initialization
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` "
                           f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()

        # Step 2: Run schema.sql against MySQL
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4'
        )
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            with conn.cursor() as cursor:
                for stmt in statements:
                    if stmt.upper().startswith(('CREATE DATABASE', 'USE ')):
                        continue
                    try:
                        cursor.execute(stmt)
                    except Exception:
                        pass
            conn.commit()
        conn.close()
        DB_ENGINE = 'mysql'
        print("[Database] Connected and initialized MySQL database successfully.")
        return
    except Exception as e:
        print(f"[Database] MySQL connection note: {e}")
        print("[Database] Initializing local SQLite database schema for fallback.")
        DB_ENGINE = 'sqlite'

    # SQLite Schema Initialization
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            currency TEXT DEFAULT '$',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'expense',
            icon TEXT DEFAULT 'tag',
            color TEXT DEFAULT '#8B5CF6',
            user_id INTEGER NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            description TEXT,
            payment_method TEXT DEFAULT 'Cash',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            income_date TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NULL,
            amount REAL NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            UNIQUE(user_id, category_id, month, year)
        );
    """)

    # Seed Default Categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories WHERE user_id IS NULL")
    if cursor.fetchone()[0] == 0:
        default_cats = [
            ('Food', 'expense', 'utensils', '#F59E0B'),
            ('Shopping', 'expense', 'shopping-bag', '#EC4899'),
            ('Travel', 'expense', 'plane', '#3B82F6'),
            ('Education', 'expense', 'graduation-cap', '#8B5CF6'),
            ('Entertainment', 'expense', 'film', '#6366F1'),
            ('Bills', 'expense', 'receipt', '#EF4444'),
            ('Healthcare', 'expense', 'heart-pulse', '#10B981'),
            ('Others', 'expense', 'folder', '#64748B')
        ]
        cursor.executemany(
            "INSERT INTO categories (name, type, icon, color, user_id) VALUES (?, ?, ?, ?, NULL)",
            default_cats
        )

    conn.commit()
    conn.close()
    print("[Database] SQLite database initialized and ready.")

def query_db(query, args=(), one=False):
    """
    Execute a SELECT query and return all or one result as dictionary.
    """
    conn = get_db_connection()
    try:
        if DB_ENGINE == 'sqlite':
            # Translate placeholder %s to ? and DATE_SUB for SQLite
            formatted_query = query.replace('%s', '?')
            formatted_query = formatted_query.replace('DATE_SUB(CURDATE(), INTERVAL 6 MONTH)', "date('now', '-6 month')")
            cursor = conn.cursor()
            cursor.execute(formatted_query, args)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            return (results[0] if results else None) if one else results
        else:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                results = cursor.fetchall()
                return (results[0] if results else None) if one else results
    finally:
        conn.close()

def execute_db(query, args=(), return_id=False):
    """
    Execute an INSERT, UPDATE, or DELETE statement.
    """
    conn = get_db_connection()
    try:
        if DB_ENGINE == 'sqlite':
            formatted_query = query.replace('%s', '?')
            cursor = conn.cursor()
            cursor.execute(formatted_query, args)
            conn.commit()
            if return_id:
                return cursor.lastrowid
            return cursor.rowcount
        else:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                conn.commit()
                if return_id:
                    return cursor.lastrowid
                return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
