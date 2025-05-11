import os
import smtplib
from email.message import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
import logging

logger = logging.getLogger(__name__)

def generate_pdf_report(data: dict, filename: str) -> bool:
    try:
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom style for the report
        styles.add(ParagraphStyle(
            name='Justify',
            alignment=TA_JUSTIFY,
            fontSize=10,
            leading=14
        ))
        
        content = []
        
        # Title
        content.append(Paragraph("Interview Analysis Report", styles['Title']))
        content.append(Spacer(1, 12))
        
        # Scores Summary
        content.append(Paragraph("Scores Summary:", styles['Heading2']))
        scores = [
            ('Answer Relevance', data.get('answer_score', 0)),
            ('Pronunciation', data.get('pronunciation_score', 0)),
            ('Grammar', data.get('grammar_score', 0)),
            # ('Eye Contact', data.get('eye_contact_score', 0)),
            ('Professional Attire', data.get('attire_score', 0)),
            ('Total Score', data.get('total_score', 0))
        ]
        
        for name, score in scores:
            content.append(Paragraph(f"<b>{name}:</b> {score}/10", styles['Normal']))
            content.append(Spacer(1, 5))
        
        content.append(Spacer(1, 15))
        
        # Question and Answers section
        content.append(Paragraph("Question:", styles['Heading3']))
        content.append(Paragraph(data.get('question', 'No question provided'), styles['Justify']))
        content.append(Spacer(1, 10))
        
        content.append(Paragraph("Your Answer:", styles['Heading3']))
        content.append(Paragraph(data.get('user_answer', 'No answer provided'), styles['Justify']))
        content.append(Spacer(1, 10))
        
        content.append(Paragraph("Ideal Answer:", styles['Heading3']))
        content.append(Paragraph(data.get('ideal_answer', 'No ideal answer generated'), styles['Justify']))
        content.append(Spacer(1, 10))
        
        if data.get('feedback'):
            content.append(Paragraph("Feedback:", styles['Heading3']))
            content.append(Paragraph(data['feedback'], styles['Justify']))
            content.append(Spacer(1, 10))
        
        doc.build(content)
        print(f"Successfully generated PDF at {filename}")
        return True
    except Exception as e:
        print(f"PDF generation failed: {str(e)}")
        return False

def send_email_with_attachment(to_email: str, subject: str, data: dict, attachment_path: str) -> bool:
    try:
        if not os.path.exists(attachment_path):
            logger.error(f"Attachment not found: {attachment_path}")
            return False

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = 'hebagassem911@gmail.com'
        msg['To'] = to_email

        # Plain text version
        text = f"""Dear Applicant,
        
Here is your interview analysis report:

Best regards,
Recruitment Team"""

        # HTML version
        html = f"""<html>
            <body>
                <p>Dear Applicant,</p>
                <p>Here is your interview analysis report:</p>
                <h3>Question:</h3>
                <p>{data.get('question', '')}</p>
                <h3>Your Answer:</h3>
                <p>{data.get('user_answer', '')}</p>
                <h3>Ideal Answer:</h3>
                <p>{data.get('ideal_answer', '')}</p>
                <h3>Feedback:</h3>
                <p>{data.get('feedback', '')}</p>
                <p>Best regards,<br>Recruitment Team</p>
            </body>
        </html>"""

        # Attach both versions
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        # Add PDF attachment
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename="Interview_Report.pdf")
            msg.attach(part)

        # Send email with timeout
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()
            server.login('hebagassem911@gmail.com', 'smue mdmk uoov zctr')  # Use app password
            server.send_message(msg)
            logger.info(f"Email successfully sent to {to_email}")
            return True

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
    except Exception as e:
        logger.error(f"Email sending error: {str(e)}")
    return False



# Question: {data.get('question', '')}
# Your Answer: {data.get('user_answer', '')}
# Ideal Answer: {data.get('ideal_answer', '')}
# Feedback: {data.get('feedback', '')}