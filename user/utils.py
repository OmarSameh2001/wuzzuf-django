from django.core.mail import send_mail
import random
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_otp_email(email):
    try:
        # otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
        # message = f'Your OTP code is: {otp}'
        # subject = 'Your OTP Code'

        # print(f"Sending OTP to {email}")

        # # Send the email
        # result = send_mail(
        #     subject,
        #     message,
        #     'hebagassem911@gmail.com',  # Sender's email address
        #     [email],  # Recipient's email address
        #     fail_silently=False,
        # )
        
        result = requests.post(os.getenv('MAIL_SERVICE') + 'send-otp', json={"email": email})
        result.raise_for_status()
        
        return result.json()['otp']  # Return OTP only if email is sent successfully
    
    except Exception as e:
        print(f"Failed to send OTP email to {email}: {e}")  # Debugging
        return None
def send_company_verified(email, name):
    try:
        result = requests.post(os.getenv('MAIL_SERVICE') + 'send-verification-email', json={"email": email, "name": name})
        result.raise_for_status()
        return result.json()['otp']  # Return OTP only if email is sent successfully
    except Exception as e:
        print(f"Failed to send company verified email to {email}: {e}")  # Debugging
        return None