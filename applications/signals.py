from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Application

def send_application_email(user, job_title, status, fail):
    """Helper function to send emails based on application updates."""
    if fail:
        subject = "Application Update: You Did Not Pass"
        message = f"Dear {user.username},\n\nWe regret to inform you that your application for {job_title} has not passed the assessment stage.\n\nBest Regards,\nRecruitment Team"
    else:
        subject = "Application Update: Stage Progression"
        message = f"Dear {user.username},\n\nYour application for {job_title} has moved to the next stage: {status}.\n\nBest Regards,\nRecruitment Team"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )

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
    if created:
        send_application_email(instance.user, instance.job.title, instance.status, instance.fail)
