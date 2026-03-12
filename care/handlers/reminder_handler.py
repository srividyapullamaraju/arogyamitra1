
import logging
from datetime import time, datetime, timedelta, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)
from config import BOT_TIMEZONE

logger = logging.getLogger(__name__)

try:
    BOT_TZINFO = ZoneInfo(BOT_TIMEZONE)
except ZoneInfoNotFoundError:
    logger.warning(
        "Invalid BOT_TIMEZONE '%s'. Falling back to UTC for reminder scheduling.",
        BOT_TIMEZONE,
    )
    BOT_TZINFO = timezone.utc

# States
ASKING_MED_NAME, ASKING_DOSAGE, ASKING_TIMING, ASKING_DURATION = range(4)

# Time slots
TIME_SLOTS = {
    "Morning (8 AM)": "08:00",
    "Afternoon (1 PM)": "13:00",
    "Evening (6 PM)": "18:00",
    "Night (10 PM)": "22:00",
    "Custom time": "custom"
}


def _build_calendar_url(med_name: str, dosage: str, time_str: str, duration_days=None) -> str:
    """Generate a Google Calendar event URL for a medication reminder."""
    now = datetime.now(BOT_TZINFO)
    hours, minutes = map(int, time_str.split(':'))
    start = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    if start < now:
        start += timedelta(days=1)
    end = start + timedelta(minutes=5)

    fmt = lambda d: d.strftime('%Y%m%dT%H%M%S')

    params = {
        'action': 'TEMPLATE',
        'text': f'💊 {med_name} — {dosage}',
        'dates': f'{fmt(start)}/{fmt(end)}',
        'details': f'Take {med_name} ({dosage}).\nSet via ArogyaMitra CareGenie Bot.',
    }
    if duration_days and duration_days > 1:
        params['recur'] = f'RRULE:FREQ=DAILY;COUNT={duration_days}'

    return f'https://calendar.google.com/calendar/render?{urlencode(params)}'

def init_reminders_on_startup(application):
    """Load and schedule all active reminders from database on bot startup"""
    from database import DatabaseManager
    
    db = DatabaseManager()
    reminders = db.get_all_active_reminders()
    
    logger.info(f"Loading {len(reminders)} active reminders from database...")
    
    for reminder in reminders:
        try:
            schedule_reminder(application.job_queue, reminder['user_id'], reminder)
            logger.info(f"Scheduled reminder {reminder['id']} for user {reminder['user_id']}")
        except Exception as e:
            logger.error(f"Failed to schedule reminder {reminder['id']}: {e}")
    
    logger.info("All reminders loaded successfully")

async def start_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start setting up a medication reminder"""
    user_id = update.effective_user.id
    
    # Initialize reminder data
    context.user_data['reminder_setup'] = {}
    
    await update.message.reply_text(
        "💊 Medication Reminder Setup\n\n"
        "Let's set up a reminder for your medication.\n\n"
        "What is the name of the medication?\n"
        "(e.g., Amoxicillin, Paracetamol)"
    )
    
    return ASKING_MED_NAME

async def collect_med_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect medication name"""
    med_name = update.message.text
    context.user_data['reminder_setup']['med_name'] = med_name
    
    await update.message.reply_text(
        f"✅ Medicine: {med_name}\n\n"
        "What is the dosage?\n"
        "(e.g., 500mg, 1 tablet, 5ml)"
    )
    
    return ASKING_DOSAGE

async def collect_dosage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect dosage information"""
    dosage = update.message.text
    context.user_data['reminder_setup']['dosage'] = dosage
    
    # Create keyboard with time slots
    keyboard = [[slot] for slot in TIME_SLOTS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Dosage: {dosage}\n\n"
        "When should I remind you?\n"
        "Select a time slot:",
        reply_markup=reply_markup
    )
    
    return ASKING_TIMING

async def collect_timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect timing information"""
    selected_slot = update.message.text
    
    if selected_slot == "Custom time":
        await update.message.reply_text(
            "Please enter custom time in 24-hour format\n"
            "Example: 14:30 for 2:30 PM",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data['reminder_setup']['custom_time'] = True
        return ASKING_TIMING
    elif selected_slot in TIME_SLOTS:
        reminder_time = TIME_SLOTS[selected_slot]
        context.user_data['reminder_setup']['time'] = reminder_time
        context.user_data['reminder_setup']['time_label'] = selected_slot
    elif context.user_data['reminder_setup'].get('custom_time'):
        # Validate custom time format
        try:
            hours, minutes = update.message.text.split(':')
            hours, minutes = int(hours), int(minutes)
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                reminder_time = f"{hours:02d}:{minutes:02d}"
                context.user_data['reminder_setup']['time'] = reminder_time
                context.user_data['reminder_setup']['time_label'] = f"Custom ({reminder_time})"
            else:
                raise ValueError
        except:
            await update.message.reply_text(
                "❌ Invalid time format. Please use HH:MM format\n"
                "Example: 14:30"
            )
            return ASKING_TIMING
    else:
        await update.message.reply_text("Please select a valid time slot")
        return ASKING_TIMING
    
    # Ask for duration
    await update.message.reply_text(
        f"✅ Time: {context.user_data['reminder_setup']['time_label']}\n\n"
        "For how many days should I remind you?\n"
        "(Enter a number, e.g., 7 for one week, or 'ongoing' for indefinite)",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ASKING_DURATION

async def collect_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect duration and save reminder"""
    from database import DatabaseManager
    
    user_id = update.effective_user.id
    duration_text = update.message.text.lower()
    
    if duration_text == 'ongoing':
        duration_days = None
        duration_label = "Ongoing"
    else:
        try:
            duration_days = int(duration_text)
            duration_label = f"{duration_days} days"
        except ValueError:
            await update.message.reply_text(
                "❌ Please enter a valid number or 'ongoing'"
            )
            return ASKING_DURATION
    
    # Get reminder data
    reminder_data = context.user_data['reminder_setup']
    
    # Save to database
    db = DatabaseManager()
    db.add_user(user_id, update.effective_user.username, update.effective_user.first_name)
    
    reminder_id = db.add_reminder(
        user_id=user_id,
        med_name=reminder_data['med_name'],
        dosage=reminder_data['dosage'],
        time=reminder_data['time'],
        time_label=reminder_data['time_label'],
        duration_days=duration_days,
        duration_label=duration_label
    )
    
    # Add ID to reminder data for scheduling
    reminder_data['id'] = reminder_id
    reminder_data['duration_days'] = duration_days
    reminder_data['duration_label'] = duration_label
    
    # Schedule the reminder
    schedule_reminder(context.job_queue, user_id, reminder_data)
    
    # Build Google Calendar link
    cal_url = _build_calendar_url(
        reminder_data['med_name'],
        reminder_data['dosage'],
        reminder_data['time'],
        duration_days
    )

    # Confirmation message
    await update.message.reply_text(
        "✅ Reminder Set Successfully!\n\n"
        f"💊 Medicine: {reminder_data['med_name']}\n"
        f"💉 Dosage: {reminder_data['dosage']}\n"
        f"⏰ Time: {reminder_data['time_label']}\n"
        f"📅 Duration: {duration_label}\n"
        f"🆔 Reminder ID: #{reminder_id}\n\n"
        "I'll remind you daily via Telegram too.\n\n"
        f"📅 Add to Google Calendar:\n{cal_url}\n\n"
        "Commands:\n"
        "/myreminders - View all reminders\n"
        "/stopreminder - Stop a reminder"
    )
    
    # Clear setup data
    context.user_data.pop('reminder_setup', None)
    
    return ConversationHandler.END

def schedule_reminder(job_queue, user_id: int, reminder_data: dict):
    """Schedule a daily reminder"""
    time_str = reminder_data['time']
    hours, minutes = map(int, time_str.split(':'))
    
    # Create time object
    reminder_time = time(hour=hours, minute=minutes, tzinfo=BOT_TZINFO)
    
    # Schedule daily job
    job_name = f"reminder_{user_id}_{reminder_data['id']}"
    
    job_queue.run_daily(
        send_reminder,
        time=reminder_time,
        days=(0, 1, 2, 3, 4, 5, 6),  # All days
        data={'user_id': user_id, 'reminder': reminder_data},
        name=job_name,
    )
    
    logger.info(f"Scheduled reminder {job_name} for user {user_id}")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send the actual reminder notification"""
    job = context.job
    user_id = job.data['user_id']
    reminder = job.data['reminder']
    
    # Build a fresh calendar link for today
    cal_url = _build_calendar_url(
        reminder['med_name'],
        reminder['dosage'],
        reminder.get('time', '08:00')
    )

    message = (
        f"⏰ Medication Reminder!\n\n"
        f"💊 {reminder['med_name']}\n"
        f"💉 Dosage: {reminder['dosage']}\n"
        f"📋 Take your medication now!\n\n"
        f"📅 Add to Calendar:\n{cal_url}\n\n"
        f"🆔 Reminder ID: #{reminder['id']}"
    )
    
    try:
        await context.bot.send_message(chat_id=user_id, text=message)
        logger.info(f"Sent reminder to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send reminder to user {user_id}: {e}")

async def view_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all active reminders"""
    from database import DatabaseManager
    
    user_id = update.effective_user.id
    db = DatabaseManager()
    reminders = db.get_user_reminders(user_id)
    
    if not reminders:
        await update.message.reply_text(
            "📭 You don't have any active reminders.\n\n"
            "Use /reminder to set one!"
        )
        return
    
    message = "📋 Your Active Reminders:\n\n"
    
    for reminder in reminders:
        cal_url = _build_calendar_url(
            reminder['med_name'],
            reminder['dosage'],
            reminder.get('time', '08:00')
        )
        message += (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 #{reminder['id']}\n"
            f"💊 {reminder['med_name']}\n"
            f"💉 {reminder['dosage']}\n"
            f"⏰ {reminder['time_label']}\n"
            f"📅 {reminder['duration_label']}\n"
            f"📅 Add to Calendar:\n{cal_url}\n"
        )
    
    message += "\n━━━━━━━━━━━━━━━━━━\n"
    message += "Use /stopreminder to stop a reminder"
    
    await update.message.reply_text(message)

async def stop_reminder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the process to stop a reminder"""
    from database import DatabaseManager
    
    user_id = update.effective_user.id
    db = DatabaseManager()
    reminders = db.get_user_reminders(user_id)
    
    if not reminders:
        await update.message.reply_text(
            "📭 You don't have any active reminders to stop."
        )
        return ConversationHandler.END
    
    # Show reminders with IDs
    message = "Which reminder would you like to stop?\n\n"
    
    for reminder in reminders:
        message += (
            f"🆔 #{reminder['id']}: {reminder['med_name']} "
            f"at {reminder['time_label']}\n"
        )
    
    message += "\nReply with the reminder ID number (e.g., 1)"
    
    await update.message.reply_text(message)
    return 0  # Waiting for ID

async def stop_reminder_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and stop the reminder"""
    from database import DatabaseManager
    
    user_id = update.effective_user.id
    
    try:
        reminder_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid reminder ID number")
        return 0
    
    # Get reminder from database
    db = DatabaseManager()
    reminders = db.get_user_reminders(user_id)
    
    reminder_to_remove = None
    for reminder in reminders:
        if reminder['id'] == reminder_id:
            reminder_to_remove = reminder
            break
    
    if not reminder_to_remove:
        await update.message.reply_text("❌ Reminder ID not found")
        return 0
    
    # Deactivate in database
    db.deactivate_reminder(reminder_id)
    
    # Remove scheduled job
    job_name = f"reminder_{user_id}_{reminder_id}"
    jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()
    
    await update.message.reply_text(
        f"✅ Reminder stopped!\n\n"
        f"💊 {reminder_to_remove['med_name']}\n"
        f"⏰ {reminder_to_remove['time_label']}\n\n"
        "The reminder has been deleted."
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel reminder setup"""
    context.user_data.pop('reminder_setup', None)
    await update.message.reply_text(
        "❌ Reminder setup cancelled.\n\n"
        "Use /reminder to start again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def get_handler():
    """Return the conversation handler for reminders"""
    reminder_conv = ConversationHandler(
        entry_points=[CommandHandler("reminder", start_reminder)],
        states={
            ASKING_MED_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_med_name)],
            ASKING_DOSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_dosage)],
            ASKING_TIMING: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_timing)],
            ASKING_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_duration)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="reminder_setup",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=300,
    )
    
    return reminder_conv

def get_additional_handlers():
    """Return additional command handlers"""
    return [
        CommandHandler("myreminders", view_reminders),
        ConversationHandler(
            entry_points=[CommandHandler("stopreminder", stop_reminder_start)],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_reminder_confirm)]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            name="stop_reminder",
            persistent=False,
            allow_reentry=True,
            conversation_timeout=300,
        )
    ]