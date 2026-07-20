import os
import json
import time
import smtplib
from datetime import datetime, date
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from supabase import create_client

load_dotenv()
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")
DELAY_SECONDS = 3

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

IST = ZoneInfo("Asia/Kolkata")
BATCH_SIZE = 100

START_DATE = date(2026, 7, 14)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESUME_PATH = os.path.join(BASE_DIR, "Arpit_Kumar_Singh_IIT_BHU.pdf")
FILE_PATH = os.path.join(
    BASE_DIR,
    "..",
    "contact",
    "contacts_cron.json"
)

with open(FILE_PATH, "r") as file:
    contacts = json.load(file)

# CONTACTS = [
#     {"name":"","email":"dekuizuku7567@gmail.com","company":"fukrey group"},
#     {"name":"ezra bridger","email":"arpitkumarsingh7567@gmail.com","company":"the ghost"}
# ]

CONTACTS=contacts

def todays_batch():
    today_ist = datetime.now(IST).date()

    if today_ist.weekday() >= 5:
        print("Weekend. Skipping.")
        return []

    response = (
        supabase.table("cron_job")
        .select("value")
        .eq("id", 1)
        .single()
        .execute()
    )

    batch_number = response.data["value"]

    print("Current Batch Number:", batch_number)

    start_idx = batch_number * 100
    end_idx = start_idx + 100

    if len(CONTACTS)<=start_idx:
        return []
    
    batch = CONTACTS[start_idx:end_idx]

    print("Starting Index:", start_idx)
    print("Ending Index:", end_idx)
    print("Contacts:", batch)

    response = (
        supabase
        .table("cron_job")
        .update(
            {
                "value": batch_number + 1
            }
        )
        .eq("id", 1)
        .execute()
    )

    print(response.data)

    return batch

def build_message(company_name: str, to_email: str, name:str) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = f"Application for Software Developer/AI Engineer Role at {company_name}"

    recipient_name = name.strip() if name.strip() else "Hiring Team"

    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Dear {recipient_name},</p>
 
    <p>
        I am <b>Arpit Kumar Singh</b>, a <b>B.Tech graduate from IIT (BHU), Varanasi</b>,
        with experience in building <b>AI-powered applications, LLM-based systems,
        RAG pipelines, and scalable backend services</b>.
    </p>

    <p>
        I have worked with technologies like <b>Python, Django, FastAPI, LangChain,
        LangGraph, Qdrant, and vector databases</b> to develop intelligent and
        production-ready software solutions.
    </p>

    <p>
        I would love to contribute my skills to <b>{company_name}</b> as an
        <b>AI Engineer / Software Developer</b>. Please find my resume attached below.
    </p>

    <p>
        Best regards,<br/>
        <b>Arpit Kumar Singh</b><br/>
        &#128222; +91-8090474152<br/>
        &#128279;
        <a href="https://www.linkedin.com/in/arpit-kumar-singh-21371824b" target="_blank">
        LinkedIn Profile
        </a>
    </p>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    if os.path.exists(RESUME_PATH):
        with open(RESUME_PATH, "rb") as f:
            part = MIMEApplication(f.read(), Name="Arpit_Kumar_Singh_IIT_BHU.pdf")
        part["Content-Disposition"] = 'attachment; filename="Arpit_Kumar_Singh_IIT_BHU.pdf"'
        msg.attach(part)

    return msg


def run_my_task():
    batch = todays_batch()
    sent = []
    errors = []

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)

        for i, contact in enumerate(batch):
            try:
                msg = build_message(contact["company"], contact["email"], contact["name"])
                server.sendmail(
                    GMAIL_USER,
                    contact["email"],
                    msg.as_string()
                )
                sent.append(contact["email"])
            except Exception as e:
                errors.append({
                    "email": contact["email"],
                    "error": str(e)
                })

            if i < len(batch) - 1:
                time.sleep(DELAY_SECONDS)

    return {
        "batch_size": len(batch),
        "sent": sent,
        "errors": errors
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = run_my_task()

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
        return
    
# run_my_task()