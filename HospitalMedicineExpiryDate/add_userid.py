import sqlite3

conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

cursor.execute("""
ALTER TABLE medicines
ADD COLUMN user_id INTEGER
""")

conn.commit()
conn.close()

print("Done")