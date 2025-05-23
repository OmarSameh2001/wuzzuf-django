from .models import Application
from .serializers import ApplicationSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from jobs.models import Job 
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ApplicationFilter
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
from applications.cloudinary import upload_video
import tempfile
from rest_framework.decorators import api_view
import cloudinary.uploader
from datetime import datetime
from io import StringIO
from .email import send_bulk_application_emails, send_schedule_email, send_contract, send_assessment_email
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd
logger = logging.getLogger(__name__)
import threading
import os
from dotenv import load_dotenv
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action, parser_classes
from django.core.mail import EmailMultiAlternatives
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.core.mail import EmailMultiAlternatives
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import textwrap
import json
from answers.models import Answer
from questions.models import Question
from wuzzuf.queue import send_to_queue
load_dotenv()

NODE_SERVICE_URL=os.environ.get("MAIL_SERVICE")
FASTAPI_URL = os.environ.get("FAST_API") 

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
        6: "Offer Interview",
        7: "Contract Signing",
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
        #     """Override update method to handle custom logic."""
        instance = self.get_object()
        print("instance", request.data['status'], instance.ats_res)
        if int(request.data['status']) > 1 and instance.ats_res is None:
            try:
                print("perform_create_for_admin")
                res = perform_create_for_admin(instance)
            except Exception as e:
                logger.error(f"Error in ATS processing: {e}")
        print(request.data)
        # return super().update(request, *args, **kwargs)
        for field, value in request.data.items():
            setattr(instance, field, value)

        # print("instance", res)
        # instance.save()    
        # print("Updated object:", instance)
        return super().update(request, *args, **kwargs)
    
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Handle ATS logic if status has changed
        status = request.data.get('status')
        if status and int(status) > 1 and instance.ats_res is None:
            try:
                perform_create_for_admin(instance)
            except Exception as e:
                logger.error(f"Error in ATS processing: {e}")

        # Update instance fields
        for field, value in request.data.items():
            setattr(instance, field, value)

        instance.save()  # This will update `updated_at`
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

        
    def destroy(self, request, *args, **kwargs):
        application = self.get_object()
        # if application.user != self.request.user:
        #     return Response({"error": "You are not the owner of this application"}, status=status.HTTP_403_FORBIDDEN)
        
        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
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
            
            try:
                # Send emails
                if not fail:
                    status_text = self.STATUS_MAP.get(new_status, 'Status Updated')
                    send_bulk_application_emails(applications, status_text, fail)
                else:
                    send_bulk_application_emails(applications, self.FAILURE_MESSAGES.get(new_status), fail=True)
            except Exception as e:
                logger.error(f"Email error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            # sender = f'"{company.username} HR Team" <{company.email}>'
            # email_errors = []
            
            # for app in applications:
            #     try:
            #         message = message_template.format(username=app.user.username)
            #         send_mail(
            #             subject,
            #             message,
            #             sender,
            #             [app.user.email],
            #             fail_silently=False,
            #         )
            #     except Exception as e:
            #         email_errors.append(f"Failed to send email to {app.user.email}: {str(e)}")
            #         logger.error(f"Email error for {app.user.email}: {str(e)}")
            
            response_data = {
                "message": f"Updated {updated_count} applications",
                "status": new_status,
                "failed": fail,
                # "email_errors": email_errors if email_errors else None
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Bulk update error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

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

            try:
                if fail:
                    send_bulk_application_emails(application, fail=True)
                else:
                    status_text = self.STATUS_MAP.get(new_status, 'Status Updated')
                    send_bulk_application_emails(application, status_text, fail)
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
            interview_time = make_aware(datetime.strptime(interview_time_str, "%Y-%m-%d %H:%M"))
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

        # subject = f"{interview_types[interview_phase]} Invitation from {company.username}"
        # message = (
        #     f"Dear {application.user.username},\n\n"
        #     f"{company.username} has scheduled your {interview_types[interview_phase]} "
        #     f"for {interview_time.strftime('%Y-%m-%d %H:%M')}.\n"
        #     f"Meeting Link: {interview_link}\n\n"
        #     f"Best regards,\n{company.username} Team"
        # )
        # sender = f'"{company.username} Recruitment" <{company.email}>'
        try:
            # send_mail(
            #     subject=subject,
            #     message=message,
            #     from_email=sender,
            #     recipient_list=[application.user.email],
            #     fail_silently=False,
            # )
            response = send_schedule_email(application.user, company, interview_types[interview_phase], interview_link, interview_time.strftime('%Y-%m-%d %H:%M'))
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
        send_assessment_email(application.user, application.job.company, assessment_link)
        return Response({"message": "Assessment link updated successfully"}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['post'])
    def update_status_by_ats(self, request):
        try:
            ats = int(request.data.get('ats', 0))
            new_status = request.data.get('new_status')
            fail = request.data.get('fail', False) in ['true', 'True', True, '1', 1]
            old_status = request.data.get('old_status')
            company = request.data.get('company')
            job = request.data.get('job')
        

            # print(ats)
            if new_status is None:
                return Response({'error': 'new_status is required'}, status=status.HTTP_400_BAD_REQUEST)
            if old_status is None:
                return Response({'error': 'old_status is required'}, status=status.HTTP_400_BAD_REQUEST)
        # Process success
            success_apps = list(Application.objects.filter(
                ats_res__gte=ats, 
                status=old_status, 
                job__company=company, 
                job__id=job, 
                fail=False
            ))
            
            for app in success_apps:
              app.status = new_status
              app.save()
    
            # updated_count = success_apps.update(status=new_status)
            email_errors_success = send_bulk_application_emails(success_apps, self.STATUS_MAP.get(int(new_status), 'Updated'), fail=False)
             # Process failure
            fail_count = 0
            email_errors_fail = []
            if fail:
                fail_apps = list(Application.objects.filter(
                    ats_res__lt=ats, 
                    status=old_status, 
                    job__company=company, 
                    job__id=job, 
                    fail=False
                ))
                
                for app in fail_apps:
                    app.fail = True
                    app.save()

                fail_count = len(fail_apps)
                    
                email_errors_fail = []
                if fail:
                      email_errors_fail = send_bulk_application_emails(fail_apps, fail=True)
            
            return Response({
                'message': f'{len(success_apps)} applicants updated, {fail_count} marked as failed.',
                # 'email_errors': email_errors_success + email_errors_fail if (email_errors_success or email_errors_fail) else None
            })

        except Exception as e:
           return Response({'error': f'Error processing request: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        #     try:
        #         updated_count = 0
        #         # Filter applicants
        #         applicants = Application.objects.filter(ats_res__gte=ats, status=old_status, job__company=company, job__id=job, fail=False)
                
        #         # Update and count affected applicants
        #         updated_count = applicants.update(status=new_status)
        #     except Exception as e:
        #         return Response({'error': f'Error updating applicants: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        #     try:
        #         fail_count = 0
        #         if fail:
        #             fail_applicants = Application.objects.filter(ats_res__lt=ats, status=old_status, job__company=company, job__id=job, fail=False)
        #             fail_count = fail_applicants.update(fail=True)
        #     except Exception as e:
        #         return Response({'error': f'Error marking applicants as failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        #     return Response({
        #         'message': f'{updated_count} applicants updated, {fail_count} marked as failed.',
        #         'ATS': ats,
        #         'new_status': new_status
        #     })
        # except Exception as e:
        #     return Response({'error': f'Error processing request: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


    # @action(detail=True, methods=['post'])
    # @parser_classes([MultiPartParser, FormParser])
    # def submit_video(self, request, pk=None):
    #     """Handle video interview submission"""
    #     try:
    #         # 2. Get application and validate inputs
    #         application = self.get_object()
    #         print(application)
    #         video_file = request.FILES.get('video')
    #         # print(video_file)
    #         question = request.POST.get('question')
    #         print(question)
    #         if not video_file or not question:
    #             return Response(
    #                 {'error': 'Video and question are required'}, 
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         # 3. Upload to Cloudinary
    #         cloudinary_result = upload_video(video_file)
    #         # print('cloudinary_result',cloudinary_result)
            
    #         # 4. Send to FastAPI for analysis
    #         payload = {
    #             'video_url': cloudinary_result['url'],
    #             'question': question,
    #             'job_description': application.job.description
    #         }
    #         # print("PAYLOAD",payload)
    #         response = httpx.post(
    #             f"{FASTAPI_URL}/analyze-interview/",
    #             json=payload,
    #             timeout=120.0
    #         )
    #         print("FASTAPI RESPONSE",response)
        
    #         response.raise_for_status()
    #         scores = response.json()
           
    #         # 5. Save results and generate report

    #         application.screening_res = json.dumps({
    #             'total_score': scores.get('total_score', 0),
    #             # 'cloudinary_data': cloudinary_result,
    #             # 'analysis_date': datetime.now().isoformat()
    #         })

    #         if scores.get('total_score', 0) >= 60:
    #             application.status = str(int(application.status) + 1)

    #         application.save()

    #         # Generate and email PDF
    #         pdf_filename = f"interview_report_{application.user.name}.pdf"
             
    #         # # Use temporary directory context manager
    #         # with tempfile.TemporaryDirectory() as tmpdirname:
    #         #     pdf_path = os.path.join(tmpdirname, pdf_filename)
                
    #         # In your Django view:
    #         with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
    #             pdf_path = tmp_file.name 
    #         # Attempt PDF generation
    #         if generate_pdf_report(scores, pdf_path):
    #             # Track email success
    #             email_sent = send_email_with_attachment(
    #                 to_email=application.user.email,
    #                 subject="Your Interview Analysis Report",
    #                 data={
    #                     'question': scores.get('question', ''),
    #                     'user_answer': scores.get('user_answer', ''),
    #                     'ideal_answer': scores.get('ideal_answer', ''),
    #                     'answer_score': scores.get('answer_score', 0),
    #                     'pronunciation_score': scores.get('pronunciation_score', 0),
    #                     'grammar_score': scores.get('grammar_score', 0),
    #                     'eye_contact_score': scores.get('eye_contact_score', 0),
    #                     'attire_score': scores.get('attire_score', 0),
    #                     'total_score': scores.get('total_score', 0),
    #                     'feedback': scores.get('feedback', '')
    #                     },
    #                 attachment_path=pdf_path
    #             )
    #             try:
    #                 os.unlink(pdf_path)  # Clean up the temp file
    #             except OSError:
    #                 logger.error(f"Failed to delete temp file: {str(e)}")
                
    #             if not email_sent:
    #                 logger.warning("Analysis succeeded but email failed")
    #         else:
    #             logger.error("PDF generation failed completely")

    #     #     # 5. Save results
    #     #     application.screening_res = json.dumps({
    #     #         'video_analysis': scores,
    #     #         'cloudinary_data': cloudinary_result,
    #     #         'analysis_date': datetime.now().isoformat()
    #     #     })
            
    #     #     if scores.get('total_score', 0) >= 70:
    #     #         application.status = str(int(application.status) + 1)
            
    #     #     application.save()

    #         # 6. Return results
    #         return Response({
    #             **scores,
    #             'video_url': cloudinary_result['url']
    #         })

    #     except httpx.ConnectError:
    #         return Response(
    #             {'error': 'Analysis service unavailable'},
    #             status=status.HTTP_503_SERVICE_UNAVAILABLE
    #         )
    #     except Exception as e:
    #         logger.error(f"Video submission error: {str(e)}")
    #         return Response(
    #             {'error': 'Processing failed'},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )

        
    @action(detail=True, methods=['post'])
    @parser_classes([MultiPartParser, FormParser])
    def submit_video(self, request, pk=None):
        """Handle video interview submission"""
        try:
            # 1. Get application and validate inputs
            print('oooooo')
            # application = self.get_object()
            # print(application)
            
            video_file = request.FILES.get('video')
            question_id = request.data.get('question_id')
            application_id = request.data.get('application_id')
            print(application_id)
            application = Application.objects.get(id=application_id)
            if(application.screening_res is not None):
                return Response(
                    {'error': 'Video already submitted'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            print(video_file, question_id, application)
             
            applicant_email = application.user.email
             
            if not video_file or not question_id:
                return Response(
                    {'error': 'Video and question are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            question = Question.objects.get(id=question_id)
            # 2. Upload video to Cloudinary
            cloudinary_result = upload_video(video_file)
            #print('cloudinary_result',cloudinary_result)
            # 3. Send video URL + question to FastAPI for analysis
            payload = {
                'video_url': cloudinary_result['url'],
                'job_id': application.job.id,
                'application_id': application_id,
                'applicant_email': applicant_email,
                'question_id': question_id,
                'question_text': question.text,
            }

            
            # def analyze_interview(): 
            #     requests.post(
            #     f"{FASTAPI_URL}/analyze-interview/",
            #     json=payload,
            #     timeout=120.0
            # )

            send_to_queue('application_queue', 'post', 'analyze-interview/', payload)


            # threading.Thread(target=analyze_interview).start()

            # # 4. Save results in application
            # application.screening_res = json.dumps({
            #     'total_score': scores.get('total_score', 0),
            # })

            # if scores.get('total_score', 0) >= 60:
            #     application.status = str(int(application.status) + 1)

            # application.save()

            # # 5. Forward scores to Node.js PDF/email service
            # email_payload = {
            #     'email': application.user.email,
            #     'question': scores.get('question', ''),
            #     'user_answer': scores.get('user_answer', ''),
            #     'ideal_answer': scores.get('ideal_answer', ''),
            #     'answer_score': scores.get('answer_score', 0),
            #     'pronunciation_score': scores.get('pronunciation_score', 0),
            #     'grammar_score': scores.get('grammar_score', 0),
            #     'attire_score': scores.get('attire_score', 0),
            #     'total_score': scores.get('total_score', 0),
            #     'feedback': scores.get('feedback', '')
            # }

            # try:
            #     print(f"MAIL_SERVICE = {NODE_SERVICE_URL}")
            #     email_response = httpx.post(
            #         # f"{NODE_SERVICE_URL}send-report",
            #         f"http://localhost:5000/send-report",
            #         json=email_payload,
            #         timeout=30.0
            #     )
            #     email_response.raise_for_status()
            # except Exception as e:
            #     logger.error(f"Failed to send report via Node.js service: {e}")
    
      ##################un comment this part if you don't want to save the answer in the database###############        
            Answer.objects.create(
                question=question,
                application=application,
                answer_text='submited',
            )
            # 6. Return results
            return Response({
                'message': 'Video submitted successfully and analysis in progress',
            })

        except httpx.ConnectError:
            return Response(
                {'error': 'Analysis service unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Video submission error: {str(e)}")
            return Response(
                {'error': 'Processing failed', 'str': {str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['post'])
    def update_status_by_csv(self, request):
        success = int(request.data.get('success', 50))
        new_status = request.data.get('new_status')
        fail = str(request.data.get('fail', 'false')).lower() in ['true', '1', 'yes']
        old_status = request.data.get('old_status')
        company = request.data.get('company')
        job = request.data.get('job')

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
            
            
            
            updated_apps = []
            failed_apps = []

            # updated_count = 0
            # fail_count = 0
            # success_emails = []
            # fail_emails = []

            for _, row in df.iterrows():
                # print('email', row['email'])
                # print('score', row['score'])
                email = row['email'].strip()
                try:
                    score = float(row['score'])
                except ValueError:
                    continue
                
                # print("email", email)
                # print("score", score)
                
                try:
                    applicant = Application.objects.get(
                        user__email=email,
                        status=old_status,
                        job__company=company,
                        job__id=job,
                        fail=False
                    )
                    # print("score>= success",score>= success)    
                    if score >= success:
                        applicant.status = new_status
                        applicant.save()
                        updated_apps.append(applicant)
                    elif score < success and fail:
                        applicant.fail = True
                        applicant.save()
                        failed_apps.append(applicant)
                except ObjectDoesNotExist:
                    continue

            email_errors_success = send_bulk_application_emails(updated_apps, self.STATUS_MAP.get(int(new_status), 'Updated'), fail=False)
            email_errors_fail = send_bulk_application_emails(failed_apps, fail=True) if fail else []
         
            return Response({
                'message': f'{len(updated_apps)} applicants updated and {len(failed_apps)} applicants marked as failed.',
                # 'email_errors': email_errors_success + email_errors_fail if (email_errors_success or email_errors_fail) else None
            })

        except Exception as e:
            return Response({'error': f'Error processing file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def meetings(self, request):
        page_size = request.query_params.get('page_size', 10)
        job = request.query_params.get('job')
        status = request.query_params.get('status')
        date = request.query_params.get('date')
        if date:
            try:
                date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

        if not job:
            return Response({"error": "Job ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        applications = Application.objects.filter(job=job, fail=False)

        if status:
            applications = applications.filter(status=status)
            
            if status == '4':
                if date:
                    applications = applications.filter(interview_time=date)
                else:
                    applications = applications.filter(interview_time__isnull=False)
            elif status == '5':
                if date:
                    applications = applications.filter(hr_time=date)
                else:
                    applications = applications.filter(hr_time__isnull=False)
            elif status == '6':
                if date:
                    applications = applications.filter(offer_time=date)
                else:
                    applications = applications.filter(offer_time__isnull=False)

        if not applications.exists():
            return Response({"error": "No applications found for this job and status"}, status=400)

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(applications, request)
        serializer = ApplicationSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_contract(self, request):
        application = request.query_params.get('application')
        application = Application.objects.get(id=application)
        if not application:
            return Response({"error": "No applications found for this job and status"}, status=400)

        application.salary = request.data.get('salary')
        application.insurance = request.data.get('insurance')
        application.termination = request.data.get('termination')
        application.save()
        print(application)
        send_contract(application)
        return Response({"message": "Contract set successfully"})


 
def perform_create_for_admin(application):
        print(application)
        user_id = application.user.id
        job_id = application.job.id
        cv_url = application.user.cv.url.split('/raw/upload/')[-1].replace('.pdf', '')
        
        if not cv_url:
            raise ValueError("User CV not found")

        # ats_url = f"{FASTAPI_URL}/ats/{user_id}/{job_id}"
        ats_data = {"cv_url": cv_url, "job_id": job_id, "application_id": application.id}
        # def ats_background():
        #     try:
        #         ats_response = requests.post(ats_url, json=ats_data)
        #         ats_result = ats_response.json()
        #         if ats_response.status_code != 200:
        #             logger.error(f"ATS Service Error: {ats_result.get('detail', 'Unknown Error')}")
        #     except requests.exceptions.RequestException as e:
        #         logger.error(f"Error connecting to ATS service: {e}")
        send_to_queue('application_queue', 'post', f'ats/{user_id}/{job_id}', ats_data)
        # threading.Thread(target=ats_background).start()

        # application.ats_res = ats_result.get("match_percentage", 0)
    # recommendations_list = recommendations.get("recommendations", [])
    # application.screening_res = json.dumps([job.get("id") or job.get("_id") for job in recommendations_list if job.get("id") is not None or job.get("_id") is not None])
        application.save()
        # print('Ats result', ats_result)
        return True#, recommendations
 
    
async def perform_create_async(application):
    user_id = application.user.id
    job_id = application.job.id
    cv_url = application.user.cv.url.split('/raw/upload/')[-1].replace('.pdf', '')

    if not cv_url:
        raise ValueError("User CV not found")

    ats_url = f"{FASTAPI_URL}/ats/{user_id}/{job_id}/"
    print("ats_url", ats_url)
    ats_data = {"cv_url": cv_url, "job_id": job_id, 'application_id': application.id}

    async with httpx.AsyncClient() as client:
        print(ats_url)
        ats_response = await client.post(ats_url, json=ats_data)
        ats_result = ats_response.json()

        if ats_response.status_code != 200:
            raise Exception(f"ATS Service Error: {ats_result.get('detail', 'Unknown Error')}")
        if ats_response.status_code != 200:
            raise Exception(f"ATS Service Error: {ats_result.get('detail', 'Unknown Error')}")

        # recommendation_url = f"{FASTAPI_URL}/recom/?user_id={user_id}&cv_url={cv_url}"
        # recommendation_response = await client.get(recommendation_url)
        # recommendations = recommendation_response.json()

        # if recommendation_response.status_code != 200:
        #     raise Exception(f"Recommendation Service Error: {recommendations.get('detail', 'Unknown Error')}")
        # if recommendation_response.status_code != 200:
        #     raise Exception(f"Recommendation Service Error: {recommendations.get('detail', 'Unknown Error')}")

    # Store results before saving
    # application.ats_res = ats_result.get("match_percentage", 0)
    # recommendations_list = recommendations.get("recommendations", [])
    # application.screening_res = json.dumps([
    #     job.get("id") or job.get("_id") for job in recommendations_list if job.get("id") is not None or job.get("_id") is not None
    # ])

    return ats_result#, recommendations
 