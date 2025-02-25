import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("tiktok_got_talent.db")
cursor = conn.cursor()

# Check if the 'users' table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
table_exists = cursor.fetchone()

if table_exists:
    print("The 'users' table exists.")
else:
    print("The 'users' table does not exist.")

# Optionally, check the data in the 'users' table (if it exists)
if table_exists:
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

# Close the database connection
conn.close()
