from database import create_tables, create_user

create_tables()

username = input("Enter username: ")
password = input("Enter password: ")

if len(password) < 8:
    print("Password must be at least 8 characters long.")
else:
    create_user(username, password)