from .models import Application
from .serializers import ApplicationSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from jobs.models import Job 
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ApplicationFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import send_mail
from rest_framework import  viewsets, status
from django.utils.timezone import make_aware
from rest_framework.viewsets import ModelViewSet
import datetime
import logging
import requests
import json

logger = logging.getLogger(__name__)



FASTAPI_URL = "http://127.0.0.1:8001" 

class CustomPagination(PageNumberPagination):
     page_size = 5  # Adjust as needed
     page_size_query_param = 'page_size'
     max_page_size = 100

@method_decorator(csrf_exempt, name='dispatch')
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.order_by('id')
#     queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ApplicationFilter
    pagination_class = CustomPagination
    
    STATUS_MAP = {
        2: "Application Accepted",
        3: "Technical Assessment",
        4: "Technical Interview",
        5: "HR Interview",
        6: "Offer Interview"
    }
    FAILURE_MESSAGES = {
        3: "We regret to inform you that you did not pass the Technical Assessment phase.",
        4: "Unfortunately, you were not successful in the Technical Interview stage.",
        5: "We’re sorry to inform you that you were not selected after the HR Interview.",
        6: "Unfortunately, we will not be proceeding with your offer interview."
    }

    def perform_create(self, serializer):
        application = serializer.save()
        perform_create_for_admin(application)
        

          


    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """Updates application status and sends an email based on success/failure."""
        print(f"Incoming request data: {request.data}")  # Debugging
        
        try:
            application = Application.objects.get(pk=pk)
            new_status = request.data.get("status")
            fail = request.data.get("fail", False)

            # Ensure status is valid
            if new_status is None:
                return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

            new_status = int(new_status)  # Convert status to integer
            if isinstance(fail, str):
                fail = fail.lower() == "true"  # Convert fail flag to boolean

            # Update application
            application.status = new_status
            application.fail = fail
            application.save()

            # Email content
            if fail:
                subject = "Application Update: Rejection"
                message = (
                    f"Dear {application.user.username},\n\n"
                    "We regret to inform you that your application has been rejected.\n\n"
                    "Best regards,\nCompany Team"
                )
            else:
                subject = f"Application Update: {self.STATUS_MAP.get(new_status, 'Status Updated')}"
                message = (
                    f"Dear {application.user.username},\n\n"
                    f"Your application status has been updated to: {self.STATUS_MAP.get(new_status, 'Updated')}.\n\n"
                    "Best regards,\nCompany Team"
                )

            # Attempt to send email
            try:
                send_mail(
                    subject,
                    message,
                    "aishaamr63@gmail.com",  # Replace with actual sender email
                    [application.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send email to {application.user.email}: {e}")
                return Response(
                    {
                        "message": "Application status updated, but email failed to send",
                        "status": application.status,
                        "failed": fail,
                    },
                    status=status.HTTP_200_OK
                )

            # If everything is successful, return success response
            return Response(
                {
                    "message": "Application status updated successfully",
                    "status": application.status,
                    "failed": fail,
                },
                status=status.HTTP_200_OK
            )

        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
        
        except (ValueError, TypeError):
            return Response({"error": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["patch"])
    def schedule_interview(self, request, pk=None):
        application = self.get_object()
        interview_time_str = request.data.get("interview_time")
        interview_link = request.data.get("interview_link")
        interview_phase = request.data.get("phase")

        if not interview_time_str or not interview_link or not isinstance(interview_phase, int):
            return Response({"error": "Missing or invalid interview details"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interview_time = make_aware(datetime.datetime.strptime(interview_time_str, "%Y-%m-%d %H:%M"))
        except ValueError:
            return Response({"error": "Invalid date format, expected YYYY-MM-DD HH:MM"}, status=status.HTTP_400_BAD_REQUEST)

        interview_types = {
            3: "Technical Assessment",
            4: "Technical Interview",
            5: "HR Interview",
            6: "Offer Interview"
        }

        if interview_phase not in interview_types:
            return Response({"error": "Invalid interview phase"}, status=status.HTTP_400_BAD_REQUEST)

        if interview_phase == 3:
            application.interview_time = interview_time
            application.interview_link = interview_link
        else:
            application.hr_time = interview_time
            application.hr_link = interview_link

        application.save()

        subject = f"Your {interview_types[interview_phase]} is Scheduled"
        message = (f"Dear {application.user.username},\n\n"
                   f"Your {interview_types[interview_phase]} is scheduled for {interview_time.strftime('%Y-%m-%d %H:%M')}.\n"
                   f"Meeting Link: {interview_link}\n\n"
                   f"Best regards,\nCompany Team")

        try:
            send_mail(
                subject,
                message,
                "aishaamr63@gmail.com",
                [application.user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send interview email to {application.user.email}: {e}")
            return Response({"error": "Failed to send email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": f"{interview_types[interview_phase]} scheduled successfully"}, status=status.HTTP_200_OK)
 
 
def perform_create_for_admin(application):
    print(application)
    user_id = application.user.id
    job_id = application.job.id
    cv_url = application.user.cv.url.split('/raw/upload/')[-1].replace('.pdf', '')
    
    if not cv_url:
        raise ValueError("User CV not found")

    ats_url = f"{FASTAPI_URL}/ats/{user_id}/{job_id}/"
    ats_data = {"cv_url": cv_url, "job_id": job_id}

    ats_response = requests.post(ats_url, json=ats_data)
    ats_result = ats_response.json()

    if ats_response.status_code != 200:
        raise Exception(f"ATS Service Error: {ats_result.get('detail', 'Unknown Error')}")

    recommendation_url = f"{FASTAPI_URL}/recom/?user_id={user_id}&cv_url={cv_url}"
    recommendation_response = requests.get(recommendation_url)
    recommendations = recommendation_response.json()

    if recommendation_response.status_code != 200:
        raise Exception(f"Recommendation Service Error: {recommendations.get('detail', 'Unknown Error')}")

    application.ats_res = ats_result.get("match_percentage", 0)
    recommendations_list = recommendations.get("recommendations", [])
    application.screening_res = json.dumps([job.get("id") or job.get("_id") for job in recommendations_list if job.get("id") is not None or job.get("_id") is not None])
    application.save()

    return ats_result, recommendations
 