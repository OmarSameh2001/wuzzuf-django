from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

def send_bulk_application_emails(applications, status_text=None, fail=False):
    email_errors = []
    for app in applications:
        user = app.user
        job = app.job
        company = job.company

        if fail:
            subject = f"Application Update for {job.title} at {company.username}"
            message = (
                f"Dear {user.username},\n\n"
                f"We regret to inform you that your application for {job.title} at {company.username} "
                f"has not passed the current stage.\n\n"
                f"Best regards,\n{company.username} Team"
            )
        else:
            subject = f"Application Update for {job.title} at {company.username}"
            message = (
                f"Dear {user.username},\n\n"
                f"Your application for {job.title} at {company.username} "
                f"has moved to the next stage: {status_text}.\n\n"
                f"Best regards,\n{company.username} Team"
            )

        sender = f'"{company.username} HR Team" <{company.email}>'

        try:
            send_mail(
                subject,
                message,
                sender,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            email_errors.append(user.email)

    return email_errors
