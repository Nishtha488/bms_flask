import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='bank_system',
            user='root',  # Replace with your MySQL username
            password=''   # Replace with your MySQL password
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None