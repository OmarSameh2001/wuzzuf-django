from django.core.mail import send_mail
import random

def send_otp_email(email, name):
    otp = random.randint(100000, 999999)  # Generate a 6-digit OTP

    # message = f'Your OTP code is: {otp}'
    subject = 'Your OTP Verification Code'
    message_template = (
            f"Dear {name} \n\n"
            f"Your One-Time Password (OTP) is: {otp}\n\n"
            f"This code is valid for a short time. Please do not share it with anyone.\n\n"
            f"Best regards,\n"
            f"Verification Team"
        )

    # print(f"Sending OTP to {email}")

    # Prepare sender (can be customized as needed)
    sender = '"RecruitHub" <hebagassem911@gmail.com>'
    
    try:

        # Format message
        message = message_template.format(username=name, otp=otp)

        print(f"Sending OTP to {email}")

        # Send email
        result = send_mail(
            subject,
            message,
            sender,
            [email],
            fail_silently=False,
        )

        if result == 1:
            print("Email successfully sent")
            return otp
        else:
            print("Email sending failed")
            return None

    except Exception as e:
        print(f"Failed to send OTP email to {email}: {e}")
        return None
    #     # Send the email
    #     result = send_mail(
    #         subject,
    #         # message,
    #         'hebagassem911@gmail.com',  # Sender's email address
    #         [email],  # Recipient's email address
    #         fail_silently=False,
    #     )

    #     if result == 1:
    #         print("Email successfully sent")
    #     else:
    #         print("Email sending failed")

    #     return otp if result == 1 else None  # Return OTP only if email is sent successfully
    
    # except Exception as e:
    #     print(f"Failed to send OTP email to {email}: {e}")  # Debugging
    #     return None
