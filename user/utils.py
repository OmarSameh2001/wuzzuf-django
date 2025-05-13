# from django.core.mail import send_mail
# import random
# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()

# def send_otp_email(email):
#     try:
#         otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
#         message = f'Your OTP code is: {otp}'
#         subject = 'Your OTP Code'

#         print(f"Sending OTP to {email}")

#         # Send the email
#         result = send_mail(
#             subject,
#             message,
#             'hebagassem911@gmail.com',  # Sender's email address
#             [email],  # Recipient's email address
#             fail_silently=False,
#         )
        
#         result = requests.post(os.getenv('MAIL_SERVICE') + 'send-otp', json={"email": email})
#         result.raise_for_status()
        
#         return result.json()['otp']  # Return OTP only if email is sent successfully
    
#     except Exception as e:
#         print(f"Failed to send OTP email to {email}: {e}")  # Debugging
#         return None
# def send_company_verified(email, name):
#     try:
#         result = requests.post(os.getenv('MAIL_SERVICE') + 'send-verification-email', json={"email": email, "name": name})
#         result.raise_for_status()
#         return result.json()['otp']  # Return OTP only if email is sent successfully
#     except Exception as e:
#         print(f"Failed to send company verified email to {email}: {e}")  # Debugging
#         return None
import fitz
from io import BytesIO
import requests
import time
import openai
import os
from dotenv import load_dotenv
import json

load_dotenv()

def format_cv_url(cv_url):
    if cv_url.startswith("http"):
        return cv_url.split("/")[-1].replace(".pdf", "")
    return cv_url
def extract_text_from_pdf_cloud(public_id: str):
    """Downloads and extracts text from a Cloudinary-hosted PDF file using its public_id."""
    try:
        pdf_url = f"https://res.cloudinary.com/dkvyfbtdl/raw/upload/{public_id}.pdf"
        print("Downloading PDF from:", pdf_url)

        response = requests.get(pdf_url)
        response.raise_for_status()  # Ensure the request was successful
        print("PDF downloaded successfully.")
       
        pdf_stream = BytesIO(response.content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        text = "\n".join([page.get_text("text") for page in doc])
        # print ("text",text)
        doc.close()

        return text.strip() if text else "No text found in PDF."
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing error: {e}")   

def parse_cv(cv_url: str, user_id: int):
        try:
            parsed = {}
            public_id = format_cv_url(cv_url)
            text = extract_text_from_pdf_cloud(public_id)
            prompt = f"""
                    You are an intelligent CV parser. From the following resume text, return a valid JSON object with the following keys:

                    1. "Summary": Generate a professional 5–7 midium length sentence summary based on the full CV content. This must be an original synthesis, not copied from the CV. Clearly identify the candidate's job specialization or target role based on their skills and experience (e.g., "Machine Learning Engineer" or "Full-Stack Developer"). Also include a brief summary of the types of projects they have worked on, highlighting key technologies or outcomes.
                    2. "About": Extract the **first personal paragraph or section** that appears after the contact information (name, email, phone, location). This is typically an unlabeled personal introduction, profile, or "About Me" paragraph.
                    3. "Skills": A list of technical and soft skills.
                    4. "Education": A list of objects with: degree, school, startDate, endDate, fieldOfStudy.
                    5. "Experience": A list of objects with: title, company, startDate, endDate.

                    Return only valid JSON, no markdown or explanation.

                    CV Text:
                    {text[:3000]}
                    """

            start_time = time.time()
            openai.api_key = os.getenv('OPEN_AI')
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000
            )
            duration = round(time.time() - start_time, 2)
            print(f"✅ OpenAI API call succeeded in {duration} seconds")

            result = response.choices[0].message.content.strip()
            # print("🧠 Raw OpenAI Response:\n", result)

            # Parse JSON from response
            json_start = result.find('{')
            json_str = result[json_start:].split("```")[0]
            parsed = json.loads(json_str)
            print("🧠 Parsed OpenAI Response:\n", parsed)
            
            # Normalize missing fields
            parsed.setdefault("About", "")
            parsed.setdefault("Summary", "")
            parsed.setdefault("Skills", [])
            parsed.setdefault("Education", [])
            parsed.setdefault("Experience", [])

            # Normalize skills list
            parsed["Skills"] = [s.strip() for s in parsed["Skills"] if isinstance(s, str)]

            # Ensure Education and Experience entries have required keys
            for edu in parsed["Education"]:
                edu.setdefault("degree", "")
                edu.setdefault("school", "")
                edu.setdefault("startDate", "")
                edu.setdefault("endDate", "")
                edu.setdefault("fieldOfStudy", "")
            
            for exp in parsed["Experience"]:
                if isinstance(exp, dict):
                    exp.setdefault("title", "")
                    exp.setdefault("company", "")
                    exp.setdefault("startDate", "")
                    exp.setdefault("endDate", "")
                else:
                    # fallback in case it is just a string
                    parsed["Experience"] = [{
                        "title": exp,
                        "company": "",
                        "startDate": "",
                        "endDate": ""
                    }]        
                    # } for exp in parsed["Experience"]]
                    break

            return parsed if parsed else {}
        
        except Exception as e:
            print("❌ GPT API failed:", e)
            return {"error": str(e)}
