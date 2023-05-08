import mysql.connector
import hashlib
import random
name = input('Enter your Name : ')
department = input('Enter your Department : ')
email = input('Enter yout Email-ID : ')
password = input('Enter you password : ')

salt = ''.join([chr(random.randint(65, 98)) for i in range(6)])

password += salt

check_sum = hashlib.sha256(password.encode()).hexdigest()
try :
    con = mysql.connector.connect(username = 'root', password = 'Parth123', host = 'localhost', database = 'emp')
except Exception as e:
    print('Error connecting to database : ')
    print(e)
    exit()
cursor = con.cursor()

cursor.execute("SELECT NAME, EMAIL_ID FROM ACCOUNTS")
if (name, email) in cursor.fetchall() :
    print('Details already added into database !')
    exit()

cursor.execute(f"INSERT INTO ACCOUNTS (NAME, EMAIL_ID, HASH, SALT, DEPARTMENT) VALUES ('{name}', '{email}', '{check_sum}', '{salt}', '{department}')")
cursor.execute('commit')
cursor.close()
print("Data successfully added !")