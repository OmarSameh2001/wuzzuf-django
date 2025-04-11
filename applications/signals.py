from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Application
from jobs.models import Job
import logging
logger = logging.getLogger(__name__)

# def send_application_email(user, job_title, status, fail):
    
#     """Helper function to send emails based on application updates."""
#     if fail:
#         subject = "Application Update: You Did Not Pass"
#         message = f"Dear {user.username},\n\nWe regret to inform you that your application for {job_title} has not passed the assessment stage.\n\nBest Regards,\nRecruitment Team"
#     else:
#         subject = "Application Update: Stage Progression"
#         message = f"Dear {user.username},\n\nYour application for {job_title} has moved to the next stage: {status}.\n\nBest Regards,\nRecruitment Team"

#     send_mail(
#         subject,
#         message,
#         # 'aishaamr63@gmail.com',
#         settings.DEFAULT_FROM_EMAIL,
#         [user.email],
#         fail_silently=False
#     )



def send_application_email(application, status, fail):
    """Helper function to send emails based on application updates using company info."""
    company = application.job.company
    job_title = application.job.title
    
    if fail:
        subject = f"Application Update for {job_title} at {company.username}"
        message = (
            f"Dear {application.user.username},\n\n"
            f"We regret to inform you that your application for {job_title} at {company.username} "
            "has not passed the current stage.\n\n"
            f"Best Regards,\n{company.username} Recruitment Team"
        )
    else:
        subject = f"Application Update for {job_title} at {company.username}"
        message = (
            f"Dear {application.user.username},\n\n"
            f"Your application for {job_title} at {company.username} "
            f"has moved to the next stage: {status}.\n\n"
            f"Best Regards,\n{company.username} Recruitment Team"
        )
    try:
        send_mail(
            subject,
            message,
            f'"{company.username}" <{settings.EMAIL_HOST_USER}>'
            # company.email,  # Use the company's email as sender
            [application.user.email],
            fail_silently=False
        )
    except Exception as e:
         logger.error(f"Failed to send interview email: {e}")  
         
         
           
@receiver(pre_save, sender=Application)
def check_status_change(sender, instance, **kwargs):
    """Detects changes in application status or fail flag before saving."""
    if instance.pk:  # Ensure application exists before checking changes
        old_instance = Application.objects.get(pk=instance.pk)

        if old_instance.status != instance.status or old_instance.fail != instance.fail:
            send_application_email(instance.user, instance.job.title, instance.status, instance.fail)

@receiver(post_save, sender=Application)
def send_email_on_create(sender, instance, created, **kwargs):
    """Sends an email when a new application is created."""
    # if created:
    #     send_application_email(instance.user, instance.job.title, instance.status, instance.fail)
    if created and int(instance.status) > 1:
        send_application_email(instance, instance.status, instance.fail)




# from django.db.models.signals import post_save, pre_save
# from django.dispatch import receiver
# from django.core.mail import EmailMessage
# from django.conf import settings
# from .models import Application
# import logging

# logger = logging.getLogger(__name__)

# import uuid
# from email.header import Header

# def get_email_headers(company_name):
#     """
#     Generate professional email headers to control sender display
    
#     Args:
#         company_name (str): The name of the company to display in the From field
    
#     Returns:
#         dict: Email headers including From, Reply-To, and anti-threading ID
#     """
#     return {
#         'From': Header(f"{company_name} Recruitment <noreply@yourdomain.com>"),
#         'Reply-To': "hr@yourdomain.com",
#         'X-Entity-Ref-ID': str(uuid.uuid4()),  # Unique ID to prevent email threading
#     }
    


# def send_application_email(application, status, fail):
#     company = application.job.company
#     subject = f"Application Update for {application.job.title}"
    
#     if fail:
#         body = f"Dear {application.user.username},\n\nWe regret to inform you..."
#     else:
#         body = f"Dear {application.user.username},\n\nYour application..."

#     email = EmailMessage(
#         subject,
#         body,
#         f'"{company.username} Recruitment" <iti@yourdomain.com>',  # Force header
#         [application.user.email],
#         reply_to=['hr@yourdomain.com'],  # Professional touch
#         headers=get_email_headers(company.username)
#     )
    
#     try:
#         email.send(fail_silently=False)
#         logger.info(f"Email sent to {application.user.email}")
#     except Exception as e:
#         logger.error(f"Email failed: {str(e)}")
# # Trigger email on status change
# @receiver(pre_save, sender=Application)
# def check_status_change(sender, instance, **kwargs):
#     if instance.pk:  # Only for existing instances
#         old = Application.objects.get(pk=instance.pk)
#         if old.status != instance.status or old.fail != instance.fail:
#             send_application_email(instance, instance.status, instance.fail)

# # Trigger email on new application
# @receiver(post_save, sender=Application)
# def send_email_on_create(sender, instance, created, **kwargs):
#     if created and instance.status > 1:
#         send_application_email(instance, instance.status, instance.fail)