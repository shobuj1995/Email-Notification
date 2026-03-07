import psycopg2

conn = psycopg2.connect(
    dbname="todo_app_db",
    user="todo_user",
    password="StrongPassword123",
    host="localhost",
    port="5432"
)
print("Connected successfully!")
conn.close()
