from django.core.mail import send_mail
import random

def send_otp_email(email):
    try:
        otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
        message = f'Your OTP code is: {otp}'
        subject = 'Your OTP Code'

        print(f"Sending OTP to {email}")

        # Send the email
        result = send_mail(
            subject,
            message,
            'hebagassem911@gmail.com',  # Sender's email address
            [email],  # Recipient's email address
            fail_silently=False,
        )

        if result == 1:
            print("Email successfully sent")
        else:
            print("Email sending failed")

        return otp if result == 1 else None  # Return OTP only if email is sent successfully
    
    except Exception as e:
        print(f"Failed to send OTP email to {email}: {e}")  # Debugging
        return None
