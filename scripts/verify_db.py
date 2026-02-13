import os
import sqlite3

db_path = 'backend/costguard.db'
if os.path.exists(db_path):
    print(f"Database found at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        cursor.execute("SELECT * FROM cost_anomaly")
        rows = cursor.fetchall()
        print(f"Anomalies count: {len(rows)}")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading DB: {e}")
    finally:
        conn.close()
else:
    print(f"Database NOT found at: {db_path}")
    # Check parent dir just in case
    if os.path.exists('costguard.db'):
        print("Database found at: ./costguard.db")
    else:
        print("Database not found in ./ or ./backend/")
