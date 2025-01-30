import os
import sqlite3

db = None

def init_db(app):
    global db
    try:
        # Use an environment variable to get the SQLite DB path, or default to 'database.db'
        database_path = os.getenv("SQLITE_DB_PATH", "database.db")
        # The 'check_same_thread=False' option can help if multiple threads use this connection
        db = sqlite3.connect(database_path, check_same_thread=False)
        db.row_factory = sqlite3.Row  # Enable accessing columns by name
        print("SQLite connection successful")

        # Create 'users' table if it doesn't exist
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                ptero_id INTEGER,
                profile_picture TEXT
            )
        """)

        # Create 'servers' table if it doesn't exist
        db.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ptero_server_id INTEGER,
                server_name TEXT,
                memory INTEGER DEFAULT 0,
                cpu INTEGER DEFAULT 0,
                disk INTEGER DEFAULT 0,
                backups INTEGER DEFAULT 0,
                databases INTEGER DEFAULT 0
            )
        """)

        # Check if columns exist in 'servers' table and add if missing
        cursor = db.execute("PRAGMA table_info(servers)")
        columns = [column_info['name'] for column_info in cursor.fetchall()]
        
        if 'memory' not in columns:
            db.execute("ALTER TABLE servers ADD COLUMN memory INTEGER DEFAULT 0")
            print("Added 'memory' column to 'servers' table")
        if 'cpu' not in columns:
            db.execute("ALTER TABLE servers ADD COLUMN cpu INTEGER DEFAULT 0")
            print("Added 'cpu' column to 'servers' table")
        if 'disk' not in columns:
            db.execute("ALTER TABLE servers ADD COLUMN disk INTEGER DEFAULT 0")
            print("Added 'disk' column to 'servers' table")
        if 'backups' not in columns:
            db.execute("ALTER TABLE servers ADD COLUMN backups INTEGER DEFAULT 0")
            print("Added 'backups' column to 'servers' table")
        if 'databases' not in columns:
            db.execute("ALTER TABLE servers ADD COLUMN databases INTEGER DEFAULT 0")
            print("Added 'databases' column to 'servers' table")

        db.commit()
        return db
    except Exception as e:
        print(f"Failed to connect to SQLite: {str(e)}")
        raise

# Database helper functions

def get_user_by_username(username):
    cursor = db.execute("SELECT * FROM users WHERE username=?", (username,))
    return cursor.fetchone()

def get_user_by_email(email):
    cursor = db.execute("SELECT * FROM users WHERE email=?", (email,))
    return cursor.fetchone()

def insert_user(username, email, password, ptero_id):
    db.execute(
        "INSERT INTO users (username, email, password, ptero_id) VALUES (?, ?, ?, ?)",
        (username, email, password, ptero_id)
    )
    db.commit()

def update_user(username, updates):
    set_clause = ", ".join(f"{key}=?" for key in updates.keys())
    values = list(updates.values())
    values.append(username)
    sql = f"UPDATE users SET {set_clause} WHERE username=?"
    db.execute(sql, values)
    db.commit()

def delete_user_by_username(username):
    db.execute("DELETE FROM users WHERE username=?", (username,))
    db.commit()

def get_user_by_id(user_id):
    cursor = db.execute("SELECT * FROM users WHERE id=?", (user_id,))
    return cursor.fetchone()

def insert_server(user_id, ptero_server_id, server_name, memory, cpu, disk=0, backups=0, databases=0):
    db.execute(
        """INSERT INTO servers 
           (user_id, ptero_server_id, server_name, memory, cpu, disk, backups, databases) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, ptero_server_id, server_name, memory, cpu, disk, backups, databases)
    )
    db.commit()

def get_servers_by_user_id(user_id):
    cursor = db.execute("SELECT * FROM servers WHERE user_id=?", (user_id,))
    return cursor.fetchall()

def get_server_count_by_user_id(user_id):
    cursor = db.execute("SELECT COUNT(*) as c FROM servers WHERE user_id=?", (user_id,))
    count_row = cursor.fetchone()
    return count_row['c']

def get_total_resource_usage_by_user_id(user_id):
    cursor = db.execute("""
        SELECT 
            SUM(memory) as total_memory_used,
            SUM(cpu) as total_cpu_used,
            SUM(disk) as total_disk_used,
            SUM(backups) as total_backups_used,
            SUM(databases) as total_databases_used
        FROM servers 
        WHERE user_id=?
    """, (user_id,))
    row = cursor.fetchone()
    return (
        row['total_memory_used'] or 0,
        row['total_cpu_used'] or 0,
        row['total_disk_used'] or 0,
        row['total_backups_used'] or 0,
        row['total_databases_used'] or 0
    )

def get_server_by_id(server_id):
    cursor = db.execute("SELECT * FROM servers WHERE id=?", (server_id,))
    server = cursor.fetchone()
    if server:
        print("DEBUG: Server record from database =>", dict(server))
    else:
        print("DEBUG: No server found with ID:", server_id)
    return server

def delete_server_by_id(server_id):
    db.execute("DELETE FROM servers WHERE id=?", (server_id,))
    db.commit()
