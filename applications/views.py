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
from applications.cloudinary import upload_audio
import tempfile

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
        job = request.data.get('job')

        print(ats)
        if new_status is None:
            return Response({'error': 'new_status is required'}, status=status.HTTP_400_BAD_REQUEST)
        if old_status is None:
            return Response({'error': 'old_status is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter applicants
        applicants = Application.objects.filter(ats_res__gte=ats, status=old_status, job__company=company, job__id=job)
        
        # Update and count affected applicants
        updated_count = applicants.update(status=new_status)
  
        if fail:
            fail_applicants = Application.objects.filter(ats_res__lt=ats, status=old_status, job__company=company, job__id=job)
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
                            job__company=company,
                            job__id =job
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
                            job__company=company,
                            job__id =job
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

  
   
    
        
    # @action(detail=True, methods=['post'])
    # def submit_audio(self, request, pk=None):
    #     try:
    #         application = self.get_object()
    #         audio_file = request.FILES.get('audio')
    #         question = request.data.get('question')
    #         print("audio_file", audio_file)
    #         print("question", question)
    #         print("application", application)
    #         # Validate audio file
    #         # if not audio_file or not audio_file.name.lower().endswith(('.wav', '.mp3')):
    #         #     return Response(
    #         #         {'error': 'Valid audio file required'},
    #         #         status=status.HTTP_400_BAD_REQUEST
    #         #     )
    #         if not audio_file:
    #             return Response({'error': 'No audio file received'}, status=400)
    #         if not question:
    #             return Response({'error': 'Question missing'}, status=400)
            
    #         print("audio_file", audio_file)
    #         print("audio_file.name", audio_file.name)
    #         print("audio_file.content_type", audio_file.content_type)
    #         try:
    #             # Upload to Cloudinary
    #             cloudinary_result = upload_audio(audio_file)
    #             print("cloudinary_result", cloudinary_result)
    #             audio_url = cloudinary_result['url']
    #         except Exception as e:
    #           return Response({'error': f'Cloudinary upload failed: {str(e)}'}, status=500)
     
     
     
     
     
     
     
     
            # # Prepare for FastAPI analysis
            # with tempfile.NamedTemporaryFile() as tmp:
            #     for chunk in audio_file.chunks():
            #         tmp.write(chunk)
            #     tmp.flush()
                
                # files = {'audio': open(tmp.name, 'rb')}
                # data = {
                #     'question': question,
                #     'job_description': application.job.description
                # }
                # print("data", data)
                # print("files", files)
              
        try:
            fastapi_response = requests.post(
                f"{FASTAPI_URL}/analyze_audio/",
                json={
                    "audio_url": audio_url,
                    "question": question
                }
            )
            if fastapi_response.status_code != 200:
                return Response({'error': 'Processing failed'}, status=500)
            analysis_result = fastapi_response.json()
        except Exception as e:
            return Response({'error': f'FastAPI request failed: {str(e)}'}, status=500)
        
        # Do whatever you need with `analysis_result` (save to model etc.)
        return Response({"message": "Analysis complete", "result": analysis_result})
            #     if response.status_code != 200:
        #         return Response(
        #             {'error': 'Analysis failed'},
        #             status=response.status_code
        #         )

        #     # Save results
        #     analysis_data = response.json()
        #     application.screening_res = json.dumps({
        #         **analysis_data,
        #         'audio_url': cloudinary_result['url']
        #     })
            
        #     if analysis_data['total_score'] >= 70:
        #         application.status = str(int(application.status) + 1)
                
        #     application.save()

        #     return Response(analysis_data)

        # except Exception as e:
        #     logger.error(f"Audio processing error: {str(e)}")
        #     return Response(
        #         {'error': 'Processing failed'},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )
        
        
        
        
    # views.py updates
    # @action(detail=True, methods=['post'])
    # def submit_audio(self, request, pk=None):
    #     try:
    #         application = self.get_object()
    #         audio_file = request.FILES.get('audio_file')
    #         question = request.POST.get('question')
            
            
            
    #         if 'audio_file' not in request.FILES:
    #                     return Response({'error': 'No audio file provided'}, status=400)
                    
    #         audio_file = request.FILES['audio_file']
                
    #             # Verify MIME type
    #         if audio_file.content_type not in ALLOWED_MIME_TYPES:
    #                 return Response({'error': 'Invalid audio format'}, status=400)
                    
    #             # Verify file signature
    #         header = audio_file.read(4)
    #         audio_file.seek(0)
            
    #         ALLOWED_SIGNATURES = [b'RIFF', b'OggS', b'ID3', b'\x1aE\xdf\xa3']
            
    #         if header[:4] not in [b'RIFF', b'OggS', b'ID3']:
    #                 return Response({'error': 'Invalid audio file signature'}, status=400)
                    

    #         # Upload to Cloudinary
    #         cloudinary_result = upload_audio(audio_file)
            
    #         # Send to FastAPI
    #         payload = {
    #             'audio_url': cloudinary_result['url'],
    #             'question': question,
    #             'job_description': application.job.description
    #         }
            
    #         response = httpx.post(
    #             f"{FASTAPI_URL}/analyze_interview/",
    #             files={'audio_file': audio_file},
    #             data={'question': question, 'job_description': application.job.description}
    #         )
            
    #         # Save results
    #         application.screening_res = json.dumps({
    #             'audio_analysis': response.json(),
    #             'cloudinary_url': cloudinary_result['url']
    #         })
    #         application.save()

    #         return Response(response.json())
            
    #     except Exception as e:
    #         return Response({"error": str(e)}, status=500)


    # def send_analysis_email(self, application, scores):
    #     """Helper method to send analysis results email"""
    #     try:
    #         company = application.job.company
    #         subject = f"Your Interview Results for {application.job.title}"
            
    #         # Format scores for email
    #         score_details = "\n".join(
    #             f"{key.replace('_', ' ').title()}: {value}%"
    #             for key, value in scores.items()
    #         )
            
    #         message = (
    #             f"Dear {application.user.username},\n\n"
    #             f"Your interview for {application.job.title} at {company.username} "
    #             f"has been analyzed. Here are your results:\n\n"
    #             f"{score_details}\n\n"
    #             f"Best regards,\n{company.username} Team"
    #         )
            
    #         send_mail(
    #             subject=subject,
    #             message=message,
    #             from_email=f'"{company.username} HR Team" <{company.email}>',
    #             recipient_list=[application.user.email],
    #             fail_silently=False,
    #         )
    #     except Exception as e:
    #         logger.error(f"Failed to send analysis email: {str(e)}")










 
def perform_create_for_admin(application):
        print(application)
        user_id = application.user.id
        job_id = application.job.id
        cv_url = application.user.cv.url.split('/raw/upload/')[-1].replace('.pdf', '')
        
        if not cv_url:
            raise ValueError("User CV not found")

        ats_url = f"{FASTAPI_URL}/ats/{user_id}/{job_id}/"
        ats_data = {"cv_url": cv_url, "job_id": job_id}
        try:
            ats_response = requests.post(ats_url, json=ats_data)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to ATS service: {e}")
            raise Exception("ATS Service is not reachable")
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
        print('Ats result', ats_result)
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
 
 
 
 
