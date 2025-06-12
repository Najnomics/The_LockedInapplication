from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import pytz
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
twilio_client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
sendgrid_client = SendGridAPIClient(api_key=os.environ["SENDGRID_API_KEY"])
scheduler = AsyncIOScheduler(timezone=pytz.UTC)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: str
    goals: List[str]
    reminder_times: List[str]
    timezone: str = "GMT+1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    goals: List[str]
    reminder_times: List[str]

class UpdateReminderTimes(BaseModel):
    phone: str
    reminder_times: List[str]

# Email Service Functions
def create_welcome_email_html(user_name: str, goals: List[str], reminder_times: List[str], phone_number: str) -> str:
    goals_html = "".join([f"<li style='margin: 5px 0; color: #333;'>{goal}</li>" for goal in goals])
    reminders_html = "".join([f"<li style='margin: 5px 0; color: #333;'>{time}</li>" for time in reminder_times])
    html_content = f"""... (unchanged HTML content) ..."""
    return html_content

async def send_welcome_email(email: str, user_name: str, goals: List[str], reminder_times: List[str], phone_number: str):
    try:
        html_content = create_welcome_email_html(user_name, goals, reminder_times, phone_number)
        message = Mail(
            from_email=os.environ["SENDER_EMAIL"],
            to_emails=email,
            subject=f"Welcome to LockedIn, {user_name}! Your Goals Await 🎯",
            html_content=html_content
        )
        response = sendgrid_client.send(message)
        logger.info(f"Welcome email sent to {email}, status: {response.status_code}")
        return {"success": True, "status_code": response.status_code}
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        return {"success": False, "error": str(e)}

# WhatsApp Service Functions
async def send_whatsapp_message(to: str, body: str):
    try:
        message = twilio_client.messages.create(
            from_=f'whatsapp:{os.environ["TWILIO_NUMBER"]}',
            body=body,
            to=f'whatsapp:{to}'
        )
        logger.info(f"WhatsApp message sent to {to}, SID: {message.sid}")
        return message.sid
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to}: {e}")
        return None

def schedule_daily_reminders(user_phone: str, goals: List[str], reminder_times: List[str]):
    try:
        for job in scheduler.get_jobs():
            if user_phone in job.id:
                scheduler.remove_job(job.id)
        for i, reminder_time in enumerate(reminder_times):
            if i < len(goals):
                hour, minute = map(int, reminder_time.split(':'))
                utc_hour = (hour - 1) % 24
                goal = goals[i]
                reminder_text = f"🎯 LockedIn Daily Reminder\n\nTime to focus on: {goal}\n\nStay locked in and make progress today! 💪"
                trigger = CronTrigger(hour=utc_hour, minute=minute, timezone=pytz.UTC)
                scheduler.add_job(
                    send_whatsapp_message,
                    trigger=trigger,
                    args=[user_phone, reminder_text],
                    id=f"reminder_{user_phone}_{hour}_{minute}_{i}",
                    replace_existing=True
                )
                logger.info(f"Scheduled reminder for {user_phone} at {reminder_time} GMT+1 (UTC: {utc_hour:02d}:{minute:02d}) for goal: {goal}")
        return True
    except Exception as e:
        logger.error(f"Error scheduling reminders for {user_phone}: {e}")
        return False

# API Routes
api_router = APIRouter(prefix="/api")

@api_router.get("/")
async def root():
    return {"message": "LockedIn API is running! 🔒", "version": "1.0.0"}

@api_router.post("/users/signup", response_model=User)
async def signup_user(user_data: UserCreate):
    try:
        user = User(**user_data.dict())
        await db.users.insert_one(user.dict())
        logger.info(f"User {user.name} signed up successfully")
        email_result = await send_welcome_email(user.email, user.name, user.goals, user.reminder_times, user.phone)
        if not email_result["success"]:
            logger.warning(f"Failed to send welcome email: {email_result.get('error', 'Unknown error')}")
        if schedule_daily_reminders(user.phone, user.goals, user.reminder_times):
            logger.info(f"Daily reminders scheduled for {user.phone}")
        else:
            logger.warning(f"Failed to schedule reminders for {user.phone}")
        return user
    except Exception as e:
        logger.error(f"Error during signup: {e}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@api_router.get("/users/{phone}", response_model=User)
async def get_user_by_phone(phone: str):
    user = await db.users.find_one({"phone": phone})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop('_id', None)
    return User(**user)

@api_router.put("/users/reminder-times")
async def update_reminder_times(update_data: UpdateReminderTimes):
    try:
        user = await db.users.find_one({"phone": update_data.phone})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await db.users.update_one({"phone": update_data.phone}, {"$set": {"reminder_times": update_data.reminder_times}})
        user_obj = User(**user)
        if schedule_daily_reminders(user_obj.phone, user_obj.goals, update_data.reminder_times):
            logger.info(f"Reminder times updated for {update_data.phone}")
            return {"message": "Reminder times updated successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reschedule reminders")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder times: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@api_router.post("/test/send-message")
async def test_send_message(phone: str, message: str):
    try:
        result = await send_whatsapp_message(phone, message)
        if result:
            return {"message": "Test message sent successfully", "sid": result}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test message")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/scheduler/jobs")
async def get_scheduled_jobs():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time),
            "trigger": str(job.trigger)
        })
    return {"jobs": jobs, "count": len(jobs)}

# App Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("LockedIn API started and scheduler is running!")
    yield
    scheduler.shutdown()
    client.close()
    logger.info("LockedIn API shutdown complete!")

app = FastAPI(title="LockedIn API", version="1.0.0", lifespan=lifespan)
app.include_router(api_router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
