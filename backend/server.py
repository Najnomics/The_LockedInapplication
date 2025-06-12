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
from datetime import datetime, timedelta
import pytz
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

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

# Create the main app
app = FastAPI(title="LockedIn API", version="1.0.0")
api_router = APIRouter(prefix="/api")

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
    reminder_times: List[str]  # Format: ["09:00", "14:00", "20:00"]
    timezone: str = "GMT+1"
    created_at: datetime = Field(default_factory=datetime.utcnow)
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
    """Create professional HTML email template"""
    goals_html = "".join([f"<li style='margin: 5px 0; color: #333;'>{goal}</li>" for goal in goals])
    reminders_html = "".join([f"<li style='margin: 5px 0; color: #333;'>{time}</li>" for time in reminder_times])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to LockedIn</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 28px;">🔒 Welcome to LockedIn!</h1>
            <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Your AI-Powered Goal Reminder App</p>
        </div>
        
        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-top: none;">
            <h2 style="color: #333; margin-top: 0;">Hello {user_name}!</h2>
            <p>Thank you for joining LockedIn. We're excited to help you achieve your goals! 🎯</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #667eea; margin-top: 0;">🎯 Your Selected Goals:</h3>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    {goals_html}
                </ul>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #667eea; margin-top: 0;">⏰ Your Reminder Times (GMT+1):</h3>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    {reminders_html}
                </ul>
            </div>
            
            <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                <h3 style="color: #667eea; margin-top: 0;">📱 Phone Number Confirmation</h3>
                <p style="margin: 0;">We've registered your phone number: <strong>{phone_number}</strong></p>
                <p style="margin: 10px 0 0 0; font-size: 14px; color: #666;">You'll receive WhatsApp reminders at your scheduled times starting tomorrow!</p>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <p style="margin: 0; font-size: 14px; color: #856404;">
                    <strong>Important:</strong> Make sure to join our WhatsApp sandbox by sending "join" to +14155238886 on WhatsApp to receive your daily reminders.
                </p>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px; text-align: center;">
                Need help? Visit our dashboard to update your reminder times anytime!
            </p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #ddd; border-top: none;">
            <p style="margin: 0; color: #666; font-size: 12px;">
                © 2024 LockedIn. All rights reserved. Stay focused, stay locked in! 🔒
            </p>
        </div>
    </body>
    </html>
    """
    return html_content

async def send_welcome_email(email: str, user_name: str, goals: List[str], reminder_times: List[str], phone_number: str):
    """Send welcome email to new user"""
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
    """Send WhatsApp message via Twilio"""
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
    """Schedule daily WhatsApp reminders for user goals"""
    try:
        # Clear existing jobs for this user
        for job in scheduler.get_jobs():
            if user_phone in job.id:
                scheduler.remove_job(job.id)
        
        for i, reminder_time in enumerate(reminder_times):
            if i < len(goals):
                hour, minute = map(int, reminder_time.split(':'))
                # Convert GMT+1 to UTC (subtract 1 hour)
                utc_hour = (hour - 1) % 24
                
                goal = goals[i]
                reminder_text = f"🎯 LockedIn Daily Reminder\n\nTime to focus on: {goal}\n\nStay locked in and make progress today! 💪"
                
                trigger = CronTrigger(
                    hour=utc_hour,
                    minute=minute,
                    timezone=pytz.UTC
                )
                
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
@api_router.get("/")
async def root():
    return {"message": "LockedIn API is running! 🔒", "version": "1.0.0"}

@api_router.post("/users/signup", response_model=User)
async def signup_user(user_data: UserCreate):
    """Sign up a new user and send welcome email"""
    try:
        # Create user object
        user = User(**user_data.dict())
        
        # Save to database
        await db.users.insert_one(user.dict())
        logger.info(f"User {user.name} signed up successfully")
        
        # Send welcome email
        email_result = await send_welcome_email(
            email=user.email,
            user_name=user.name,
            goals=user.goals,
            reminder_times=user.reminder_times,
            phone_number=user.phone
        )
        
        if email_result["success"]:
            logger.info(f"Welcome email sent to {user.email}")
        else:
            logger.warning(f"Failed to send welcome email: {email_result.get('error', 'Unknown error')}")
        
        # Schedule daily reminders
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
    """Get user by phone number"""
    user = await db.users.find_one({"phone": phone})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.put("/users/reminder-times")
async def update_reminder_times(update_data: UpdateReminderTimes):
    """Update user's reminder times"""
    try:
        # Find user
        user = await db.users.find_one({"phone": update_data.phone})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update reminder times in database
        await db.users.update_one(
            {"phone": update_data.phone},
            {"$set": {"reminder_times": update_data.reminder_times}}
        )
        
        # Reschedule reminders
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
    """Test endpoint to send a WhatsApp message"""
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
    """Get all scheduled jobs (for debugging)"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time),
            "trigger": str(job.trigger)
        })
    return {"jobs": jobs, "count": len(jobs)}

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    scheduler.start()
    logger.info("LockedIn API started and scheduler is running!")

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
    client.close()
    logger.info("LockedIn API shutdown complete!")
