# test_email_connection.py
import smtplib

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('hebagassem911@gmail.com', 'jucz gujg xwxx ewln ')
    print("Connection Successful!")
except Exception as e:
    print(f"Failed to connect: {e}")
