from django.core.mail import send_mail
import logging
import requests
import threading
import os
from dotenv import load_dotenv
from wuzzuf.queue import send_to_queue

load_dotenv()
logger = logging.getLogger(__name__)

def _post_fire_and_forget(url, data):
    # def task():
    #     try:
    #         requests.post(url, json=data)
    #     except Exception as e:
    #         logger.error(f"Failed to send request to {url}: {e}")
    # threading.Thread(target=task).start()
    send_to_queue('email_queue', 'post', url, data)

def send_bulk_application_emails(applications, status_text=None, fail=False):
    application_list = []
    if hasattr(applications, "__iter__"):
        for application in applications:
            application_list.append({
                "user_email": application.user.email,
                "user_name": application.user.name,
                "job_title": application.job.title,
                "company_name": application.job.company.name,
                "company_email": application.job.company.email,
            })
    else:
        application_list.append({
            "user_email": applications.user.email,
            "user_name": applications.user.name,
            "job_title": applications.job.title,
            "company_name": applications.job.company.name,
            "company_email": applications.job.company.email,
        })

    # url = os.getenv("MAIL_SERVICE") + "/send-bulk-email"
    url = 'send-bulk-email'
    data = {
        "applications": application_list,
        "status_text": status_text,
        "fail": fail
    }
    _post_fire_and_forget(url, data)

def send_schedule_email(user, company, phase, link, time):
    # url = os.getenv("MAIL_SERVICE") + "/send-schedule-email"
    url = 'send-schedule-email'
    data = {
        "user_email": user.email,
        "user_name": user.name,
        "company_name": company.name,
        "company_email": company.email,
        "link": link,
        "time": time,
        "phase": phase
    }
    _post_fire_and_forget(url, data)

def send_status_email(user, company, phase, link, time):
    # url = os.getenv("MAIL_SERVICE") + "/send-dynamic-email"
    url = 'send-dynamic-email'
    data = {
        "user_email": user.email,
        "user_name": user.name,
        "company_name": company.name,
        "company_email": company.email,
        "link": link,
        "time": time,
        "phase": phase
    }
    _post_fire_and_forget(url, data)
def send_contract(application):
    # url = os.getenv("MAIL_SERVICE") + "/send-contract"
    url = 'send-contract'
    data = {
        "user_email": application.user.email,
        "user_name": application.user.name,
        "job_title": application.job.title,
        "job_attendance": application.job.attend,
        "job_type": application.job.type_of_job,
        "company_name": application.job.company.name,
        "company_email": application.job.company.email,
        'salary': application.salary,
        'insurance': application.insurance,
        'termination': application.termination
    }
    _post_fire_and_forget(url, data)

def send_assessment_email(user, company, link):
    # url = os.getenv("MAIL_SERVICE") + "/send-assessment-email"
    print("send_assessment_email", user, company, link)
    url = 'send-assessment-email'
    data = {
        "user_email": user.email,
        "user_name": user.name,
        "company_name": company.name,
        "company_email": company.email,
        "link": link,
    }
    _post_fire_and_forget(url, data)
