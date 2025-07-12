import sqlite3

conn = sqlite3.connect('call_stack_graph.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM nodes WHERE type = "Class"')
classes = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM nodes WHERE type = "Method"')
methods = cursor.fetchone()[0]

print(f'Database contains: {classes} classes and {methods} methods')

# Show first few entries
cursor.execute('SELECT * FROM nodes LIMIT 10')
rows = cursor.fetchall()
print("\nFirst 10 database entries:")
for row in rows:
    print(row)

conn.close()
