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
import httpx
import csv
from io import StringIO
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd
logger = logging.getLogger(__name__)



FASTAPI_URL = "http://127.0.0.1:8001" 

class CustomPagination(PageNumberPagination):
     page_size = 5  # Adjust as needed
     page_size_query_param = 'page_size'
     max_page_size = 100

@method_decorator(csrf_exempt, name='dispatch')
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ApplicationFilter
    pagination_class = CustomPagination
    ordering = ['-ats_res']
    
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

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get the ordering query parameter (if any)
        ordering = self.request.query_params.get('ordering', None)

        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by(*self.ordering)

        return queryset

    def perform_create(self, serializer):
        print("serializer")
        application = serializer.save()
        if int(application.status) > 1:
            perform_create_for_admin(application)
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error in creating application: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, *args, **kwargs):
        # """Override update method to handle custom logic."""
        # instance = self.get_object()
        # res = perform_create_for_admin(instance)
        # def update(self, request, *args, **kwargs):
        #     """Override update method to handle custom logic."""
        instance = self.get_object()

        if int(instance.status) > 1 and instance.ats_res is None:    
            res = perform_create_for_admin(instance)
        print(request.data)
        return super().update(request, *args, **kwargs)
        for field, value in request.data.items():
            setattr(instance, field, value)
        instance.save()    
        print("Updated object:", instance)
        return super().update(request, *args, **kwargs)
        

          


    # @action(detail=True, methods=["patch"])
    # def update_status(self, request, pk=None):
    #     """Updates application status and sends an email based on success/failure."""
    #     print(f"Incoming request data: {request.data}")  # Debugging
        
    #     try:
    #         application = Application.objects.get(pk=pk)
    #         new_status = request.data.get("status")
    #         fail = request.data.get("fail", False)

    #         # Ensure status is valid
    #         if new_status is None:
    #             return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

    #         new_status = int(new_status)  # Convert status to integer
    #         if isinstance(fail, str):
    #             fail = fail.lower() == "true"  # Convert fail flag to boolean

    #         # Update application
    #         application.status = new_status
    #         application.fail = fail
    #         application.save()

    #         # Email content
    #         if fail:
    #             subject = "Application Update: Rejection"
    #             message = (
    #                 f"Dear {application.user.username},\n\n"
    #                 "We regret to inform you that your application has been rejected.\n\n"
    #                 "Best regards,\nCompany Team"
    #             )
    #         else:
    #             subject = f"Application Update: {self.STATUS_MAP.get(new_status, 'Status Updated')}"
    #             message = (
    #                 f"Dear {application.user.username},\n\n"
    #                 f"Your application status has been updated to: {self.STATUS_MAP.get(new_status, 'Updated')}.\n\n"
    #                 "Best regards,\nCompany Team"
    #             )

    #         # Attempt to send email
    #         try:
    #             send_mail(
    #                 subject,
    #                 message,
    #                 "aishaamr63@gmail.com",  # Replace with actual sender email
    #                 [application.user.email],
    #                 fail_silently=False,
    #             )
    #         except Exception as e:
    #             logger.error(f"Failed to send email to {application.user.email}: {e}")
    #             return Response(
    #                 {
    #                     "message": "Application status updated, but email failed to send",
    #                     "status": application.status,
    #                     "failed": fail,
    #                 },
    #                 status=status.HTTP_200_OK
    #             )

    #         # If everything is successful, return success response
    #         return Response(
    #             {
    #                 "message": "Application status updated successfully",
    #                 "status": application.status,
    #                 "failed": fail,
    #             },
    #             status=status.HTTP_200_OK
    #         )

    #     except Application.DoesNotExist:
    #         return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
        
    #     except (ValueError, TypeError):
    #         return Response({"error": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)

    #     except Exception as e:
    #         logger.error(f"Unexpected error: {e}")
    #         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # @action(detail=True, methods=["patch"])
    # def schedule_interview(self, request, pk=None):
    #     application = self.get_object()
    #     interview_time_str = request.data.get("interview_time")
    #     interview_link = request.data.get("interview_link")
    #     interview_phase = request.data.get("phase")

    #     if not interview_time_str or not interview_link or not isinstance(interview_phase, int):
    #         return Response({"error": "Missing or invalid interview details"}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         interview_time = make_aware(datetime.datetime.strptime(interview_time_str, "%Y-%m-%d %H:%M"))
    #     except ValueError:
    #         return Response({"error": "Invalid date format, expected YYYY-MM-DD HH:MM"}, status=status.HTTP_400_BAD_REQUEST)

    #     interview_types = {
    #         3: "Technical Assessment",
    #         4: "Technical Interview",
    #         5: "HR Interview",
    #         6: "Offer Interview"
    #     }

    #     if interview_phase not in interview_types:
    #         return Response({"error": "Invalid interview phase"}, status=status.HTTP_400_BAD_REQUEST)

    #     if interview_phase == 3:
    #         application.interview_time = interview_time
    #         application.interview_link = interview_link
    #     elif interview_phase == 4:
    #         application.hr_time = interview_time
    #         application.hr_link = interview_link
    #     elif interview_phase == 5:
    #         application.offer_time = interview_time
    #         application.offer_link = interview_link

    #     application.save()

    #     subject = f"Your {interview_types[interview_phase]} is Scheduled"
    #     message = (f"Dear {application.user.username},\n\n"
    #                f"Your {interview_types[interview_phase]} is scheduled for {interview_time.strftime('%Y-%m-%d %H:%M')}.\n"
    #                f"Meeting Link: {interview_link}\n\n"
    #                f"Best regards,\nCompany Team")

    #     try:
    #         send_mail(
    #             subject,
    #             message,
    #             "aishaamr63@gmail.com",
    #             [application.user.email],
    #             fail_silently=False,
    #         )
    #     except Exception as e:
    #         logger.error(f"Failed to send interview email to {application.user.email}: {e}")
    #         print(f"Failed to send interview email to {application.user.email}: {e}")
    #         # return Response({"error": "Failed to send email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #     return Response({"message": f"{interview_types[interview_phase]} scheduled successfully"}, status=status.HTTP_200_OK)
    # @action(methods=["patch"], detail=True)
    # def set_assessment_link(self, request, pk=None):
    #     """Updates application with new assessment link"""
    #     application = self.get_object()
    #     assessment_link = request.data.get("assessment_link")
    #     if assessment_link is None:
    #         return Response({"error": "Assessment link is required"}, status=status.HTTP_400_BAD_REQUEST)
    #     application.assessment_link = assessment_link
    #     application.save()
    #     return Response({"message": "Assessment link updated successfully"}, status=status.HTTP_200_OK)
 
 
 
    # Add this to your ApplicationViewSet in views.py
    @action(detail=False, methods=['patch'])
    def bulk_update_status(self, request):
        """Bulk update status for multiple applications"""
        try:
            application_ids = request.data.get('application_ids', [])
            new_status = request.data.get('status')
            fail = request.data.get('fail', False)
            
            if not application_ids:
                return Response({"error": "No applications selected"}, status=status.HTTP_400_BAD_REQUEST)
            
            if new_status is None:
                return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            new_status = int(new_status)
            if isinstance(fail, str):
                fail = fail.lower() == "true"

            # Get all applications at once
            applications = Application.objects.filter(id__in=application_ids)
            if not applications.exists():
                return Response({"error": "No valid applications found"}, status=status.HTTP_404_NOT_FOUND)
                
            # Get company info from first application (assuming all are for same company)
            company = applications.first().job.company
            job_title = applications.first().job.title
            
            # Bulk update
            updated_count = applications.update(status=new_status, fail=fail)
            
            # Send emails
            if not fail:
                status_text = self.STATUS_MAP.get(new_status, 'Status Updated')
                subject = f"Application Update for {job_title} at {company.username}"
                message_template = (
                    f"Dear {{username}},\n\n"
                    f"Your application for {job_title} at {company.username} "
                    f"has moved to the next stage: {status_text}.\n\n"
                    f"Best regards,\n{company.username} Team"
                )
            else:
                subject = f"Application Update for {job_title} at {company.username}"
                message_template = (
                    f"Dear {{username}},\n\n"
                    f"We regret to inform you that your application for {job_title} at {company.username} "
                    "has not passed the current stage.\n\n"
                    f"Best regards,\n{company.username} Team"
                )
                
            sender = f'"{company.username} HR Team" <{company.email}>'
            email_errors = []
            
            for app in applications:
                try:
                    message = message_template.format(username=app.user.username)
                    send_mail(
                        subject,
                        message,
                        sender,
                        [app.user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    email_errors.append(f"Failed to send email to {app.user.email}: {str(e)}")
                    logger.error(f"Email error for {app.user.email}: {str(e)}")
            
            response_data = {
                "message": f"Updated {updated_count} applications",
                "status": new_status,
                "failed": fail,
                "email_errors": email_errors if email_errors else None
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Bulk update error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
 
 
#    In your views.py
    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """Updates application status and sends an email based on success/failure."""
        try:
            application = self.get_object()
            company = application.job.company
            new_status = request.data.get("status")
            fail = request.data.get("fail", False)
            print ("application", application)
            print ("company", company)
            print ("new_status", new_status)
            if new_status is None:
                return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

            new_status = int(new_status)
            if isinstance(fail, str):
                fail = fail.lower() == "true"

            application.status = new_status
            application.fail = fail
            application.save()

            if fail:
                subject = f"Application Update from {company.username}"
                message = (
                    f"Dear {application.user.username},\n\n"
                    f"We regret to inform you that your application for {application.job.title} "
                    f"at {company.username} has been rejected.\n\n"
                    f"Best regards,\n{company.username} Team"
                )
            else:
                status_text = self.STATUS_MAP.get(new_status, 'Status Updated')
                subject = f"Application Update from {company.username}"
                message = (
                    f"Dear {application.user.username},\n\n"
                    f"Your application for {application.job.title} at {company.username} "
                    f"has been updated to: {status_text}.\n\n"
                    f"Best regards,\n{company.username} Team"
                )
            sender = f'"{company.username} HR Team" <{company.email}>'
            try:
                send_mail(
                    subject,
                    message,
                    sender,
                    # company.email,  # Use company's email as sender
                    [application.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                return Response(
                    {
                        "message": "Status updated but email failed",
                        "status": application.status,
                        "failed": fail,
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {
                    "message": "Status updated successfully",
                    "status": application.status,
                    "failed": fail,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["patch"])
    def schedule_interview(self, request, pk=None):
        application = self.get_object()
        company = application.job.company
        interview_time_str = request.data.get("interview_time")
        interview_link = request.data.get("interview_link")
        interview_phase = request.data.get("phase")

        if not interview_time_str or not interview_link or not isinstance(interview_phase, int):
            return Response({"error": "Missing or invalid interview details"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interview_time = make_aware(datetime.datetime.strptime(interview_time_str, "%Y-%m-%d %H:%M"))
        except ValueError:
            return Response({"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

        interview_types = {
            3: "Technical Assessment",
            4: "Technical Interview",
            5: "HR Interview",
            6: "Offer Interview"
        }

        if interview_phase not in interview_types:
            return Response({"error": "Invalid interview phase"}, status=status.HTTP_400_BAD_REQUEST)

    # Update the appropriate fields based on phase
        if interview_phase == 3:
            application.interview_time = interview_time
            application.interview_link = interview_link
        elif interview_phase == 4:
            application.hr_time = interview_time
            application.hr_link = interview_link
        elif interview_phase == 5:
            application.offer_time = interview_time
            application.offer_link = interview_link

        application.save()

        subject = f"{interview_types[interview_phase]} Invitation from {company.username}"
        message = (
            f"Dear {application.user.username},\n\n"
            f"{company.username} has scheduled your {interview_types[interview_phase]} "
            f"for {interview_time.strftime('%Y-%m-%d %H:%M')}.\n"
            f"Meeting Link: {interview_link}\n\n"
            f"Best regards,\n{company.username} Team"
        )
        sender = f'"{company.username} Recruitment" <{company.email}>'
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=sender,
                recipient_list=[application.user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send interview email to {application.user.email}: {e}")
            print(f"Failed to send interview email to {application.user.email}: {e}")
            # return Response({"error": "Failed to send email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": f"{interview_types[interview_phase]} scheduled successfully"}, status=status.HTTP_200_OK)
    @action(methods=["patch"], detail=True)
    def set_assessment_link(self, request, pk=None):
        """Updates application with new assessment link"""
        application = self.get_object()
        assessment_link = request.data.get("assessment_link")
        if assessment_link is None:
            return Response({"error": "Assessment link is required"}, status=status.HTTP_400_BAD_REQUEST)
        application.assessment_link = assessment_link
        application.save()
        return Response({"message": "Assessment link updated successfully"}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['post'])
    def update_status_by_ats(self, request):
        ats = int(request.data.get('ats', 0))
        new_status = request.data.get('new_status')
        fail = request.data.get('fail', False)
        old_status = request.data.get('old_status')
        company = request.data.get('company')

        print(ats)
        if new_status is None:
            return Response({'error': 'new_status is required'}, status=status.HTTP_400_BAD_REQUEST)
        if old_status is None:
            return Response({'error': 'old_status is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter applicants
        applicants = Application.objects.filter(ats_res__gte=ats, status=old_status, job__company=company)
        
        # Update and count affected applicants
        updated_count = applicants.update(status=new_status)
  
        if fail:
            fail_applicants = Application.objects.filter(ats_res__lt=ats, status=old_status, job__company=company)
            fail_count = fail_applicants.update(fail=True)

        return Response({
            'message': f'{updated_count} applicants updated.',
            'ATS': ats,
            'new_status': new_status
        })
    @action(detail=False, methods=['post'])
    def update_status_by_csv(self, request):
        success = int(request.data.get('success', 50))
        new_status = request.data.get('new_status')
        fail = request.data.get('fail', False)
        old_status = request.data.get('old_status')
        company = request.data.get('company')

        if new_status is None:
            return Response({'error': 'new_status is required'}, status=status.HTTP_400_BAD_REQUEST)
        if old_status is None:
            return Response({'error': 'old_status is required'}, status=status.HTTP_400_BAD_REQUEST)
        if 'file' not in request.FILES:
            return Response({'error': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name.lower()

        try:
            if file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            
            elif file_name.endswith('.csv'):
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8', on_bad_lines='skip')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(uploaded_file, encoding='ISO-8859-1', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        df = pd.read_csv(uploaded_file, encoding='Windows-1252', on_bad_lines='skip')
            
            else:
                return Response({'error': 'Unsupported file format. Please upload a CSV or Excel file.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

            if 'email' not in df.columns or 'score' not in df.columns:
                return Response({'error': 'File must contain "email" and "score" columns'}, 
                            status=status.HTTP_400_BAD_REQUEST)

            updated_count = 0
            fail_count = 0
            success_emails = []
            fail_emails = []

            for _, row in df.iterrows():
                email = row['email'].strip()
                try:
                    score = float(row['score'])
                except ValueError:
                    continue

                if score >= success:
                    try:
                        applicant = Application.objects.get(
                            user__email=email, 
                            status=old_status, 
                            job__company=company
                        )
                        applicant.status = new_status
                        applicant.save()
                        updated_count += 1
                        success_emails.append(email)
                    except ObjectDoesNotExist:
                        continue

                elif fail:
                    try:
                        applicant = Application.objects.get(
                            user__email=email, 
                            status=old_status, 
                            job__company=company
                        )
                        applicant.fail = True
                        applicant.save()
                        fail_count += 1
                        fail_emails.append(email)
                    except ObjectDoesNotExist:
                        continue

            return Response({
                'message': f'{updated_count} applicants updated and {fail_count} applicants marked as failed.',
                'success_score': success,
                'new_status': new_status,
                # 'success_emails': success_emails,
                # 'fail_emails': fail_emails
            })

        except Exception as e:
            return Response({'error': f'Error processing file: {str(e)}'}, 
                        status=status.HTTP_400_BAD_REQUEST)

 
 
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

    # recommendation_url = f"{FASTAPI_URL}/recom/?user_id={user_id}&cv_url={cv_url}"
    # recommendation_response = requests.get(recommendation_url)
    # recommendations = recommendation_response.json()

    # if recommendation_response.status_code != 200:
    #     raise Exception(f"Recommendation Service Error: {recommendations.get('detail', 'Unknown Error')}")

        application.ats_res = ats_result.get("match_percentage", 0)
    # recommendations_list = recommendations.get("recommendations", [])
    # application.screening_res = json.dumps([job.get("id") or job.get("_id") for job in recommendations_list if job.get("id") is not None or job.get("_id") is not None])
        application.save()

        return ats_result#, recommendations
 
    
async def perform_create_async(application):
    user_id = application.user.id
    job_id = application.job.id
    cv_url = application.user.cv.url.split('/raw/upload/')[-1].replace('.pdf', '')

    if not cv_url:
        raise ValueError("User CV not found")

    ats_url = f"{FASTAPI_URL}/ats/{user_id}/{job_id}/"
    ats_data = {"cv_url": cv_url, "job_id": job_id}

    async with httpx.AsyncClient() as client:
        ats_response = await client.post(ats_url, json=ats_data)
        ats_result = ats_response.json()

        if ats_response.status_code != 200:
            raise Exception(f"ATS Service Error: {ats_result.get('detail', 'Unknown Error')}")
        if ats_response.status_code != 200:
            raise Exception(f"ATS Service Error: {ats_result.get('detail', 'Unknown Error')}")

        recommendation_url = f"{FASTAPI_URL}/recom/?user_id={user_id}&cv_url={cv_url}"
        recommendation_response = await client.get(recommendation_url)
        recommendations = recommendation_response.json()

        if recommendation_response.status_code != 200:
            raise Exception(f"Recommendation Service Error: {recommendations.get('detail', 'Unknown Error')}")
        if recommendation_response.status_code != 200:
            raise Exception(f"Recommendation Service Error: {recommendations.get('detail', 'Unknown Error')}")

    # Store results before saving
    application.ats_res = ats_result.get("match_percentage", 0)
    recommendations_list = recommendations.get("recommendations", [])
    application.screening_res = json.dumps([
        job.get("id") or job.get("_id") for job in recommendations_list if job.get("id") is not None or job.get("_id") is not None
    ])

    return ats_result, recommendations
 