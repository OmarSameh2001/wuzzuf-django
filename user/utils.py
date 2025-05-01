# from django.core.mail import send_mail
# import random

# def send_otp_email(email, name):
#     otp = random.randint(100000, 999999)  # Generate a 6-digit OTP

#     subject = 'Your OTP Verification Code'
#     message_template = (
#             f"Dear {name} \n\n"
#             f"Your One-Time Password (OTP) is: {otp}\n\n"
#             f"This code is valid for a short time. Please do not share it with anyone.\n\n"
#             f"Best regards,\n"
#             f"RecruitHub Team"
#         )

#     sender = '"RecruitHub" <hebagassem911@gmail.com>'
    
#     try:

#         # Format message
#         message = message_template.format(username=name, otp=otp)

#         print(f"Sending OTP to {email}")

#         # Send email
#         result = send_mail(
#             subject,
#             message,
#             sender,
#             [email],
#             fail_silently=False,
#         )

#         if result == 1:
#             print("Email successfully sent")
#             return otp
#         else:
#             print("Email sending failed")
#             return None

#     except Exception as e:
#         print(f"Failed to send OTP email to {email}: {e}")
#         return None
    


# def send_company_verification_email(email, name):
#             subject = 'Your Company Has Been Verified'
#             message_template = (
#                 f"Dear {name},\n\n"
#                 f"Congratulations! Your company account has been successfully verified.\n\n"
#                 f"You can now log in and access all the platform features without restrictions.\n\n"
#                 f"If you have any questions, feel free to reach out to our support team.\n\n"
#                 f"Best regards,\n"
#                 f"RecruitHub Team"
#             )

#             sender = '"RecruitHub" <hebagassem911@gmail.com>'

#             try:
#                 print(f"Sending company verification email to {email}")

#                 result = send_mail(
#                     subject,
#                     message_template,
#                     sender,
#                     [email],
#                     fail_silently=False,
#                 )

#                 if result == 1:
#                     print("Verification email successfully sent")
#                     return True
#                 else:
#                     print("Verification email sending failed")
#                     return False

#             except Exception as e:
#                 print(f"Failed to send verification email to {email}: {e}")
#                 return False