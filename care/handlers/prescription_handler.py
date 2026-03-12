import logging
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from utils.gemini_client import agenerate_with_image, agenerate_text, GeminiQuotaError, GeminiAPIError
from utils.helpers import split_message, download_photo

logger = logging.getLogger(__name__)

# States
WAITING_FOR_PRESCRIPTION, ASKING_REMINDER_CONFIRMATION = range(2)


def make_medicine_calendar_url(med_name: str, dosage: str, time_str: str, duration_days: int = 30) -> str:
    """Generate a Google Calendar link for a medicine dose."""
    now = datetime.now()
    # Parse hour from time string like "08:00", "Morning", "After meals"
    hour_map = {
        "morning": 8, "breakfast": 8, "afternoon": 13,
        "lunch": 13, "evening": 18, "night": 21, "dinner": 19, "bedtime": 21
    }
    hour = 8  # default morning
    for key, val in hour_map.items():
        if key in time_str.lower():
            hour = val
            break
    # Try to parse HH:MM directly
    try:
        if ":" in time_str:
            parsed = datetime.strptime(time_str.strip(), "%H:%M")
            hour = parsed.hour
    except ValueError:
        pass

    start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if start < now:
        start += timedelta(days=1)
    end = start + timedelta(minutes=15)

    fmt = lambda d: d.strftime('%Y%m%dT%H%M%S')

    params = {
        'action': 'TEMPLATE',
        'text': f'💊 {med_name} — {dosage}',
        'dates': f'{fmt(start)}/{fmt(end)}',
        'details': f'Take {med_name} ({dosage}) — {time_str}.\nSet via CareGenie Bot.',
    }
    if duration_days and duration_days > 1:
        params['recur'] = f'RRULE:FREQ=DAILY;COUNT={duration_days}'

    return f'https://calendar.google.com/calendar/render?{urlencode(params)}'


async def start_prescription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start prescription analysis"""
    await update.message.reply_text(
        "💊 Prescription Analyzer\n\n"
        "Upload a clear photo of your prescription.\n\n"
        "I will provide:\n"
        "✅ Medication list\n"
        "✅ Dosage & timing\n"
        "✅ Purpose & side effects\n"
        "✅ Precautions\n"
        "📅 Google Calendar reminders\n\n"
        "📸 Send prescription image:"
    )
    return WAITING_FOR_PRESCRIPTION


async def analyze_prescription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze prescription image and offer calendar reminders"""
    if not update.message.photo:
        await update.message.reply_text("Please send a photo or use /cancel")
        return WAITING_FOR_PRESCRIPTION

    await update.message.reply_text("💊 Analyzing prescription...")

    try:
        image = await download_photo(update.message.photo[-1])

        # ── PASS 1: Human-readable analysis ──────────────────────────────
        analysis_prompt = """Analyze this PRESCRIPTION. For EACH medicine provide:

━━━━━━━━━━━━━━━━━━
💊 MEDICINE [NUMBER]

Name: [Brand/Generic]
Dosage: [Strength]

⏰ TIMING:
Morning: [Yes/No + quantity]
Afternoon: [Yes/No + quantity]
Night: [Yes/No + quantity]

When: [Before/After food]
Duration: [Days/weeks]

🎯 PURPOSE: [What it treats - simple explanation]

🚫 PRECAUTIONS:
• [Warning 1]
• [Warning 2]

━━━━━━━━━━━━━━━━━━

Repeat for EACH medicine. Keep it concise, clear, and specifically to the point.
Check which language the user is conversing in and track that language and respond in the same language for all subsequent answers.
Use plain text, DO NOT use markdown formatting like asterisks or hash symbols. Ask only relevant things."""

        try:
            analysis = await agenerate_with_image(analysis_prompt, image)
        except GeminiQuotaError:
            await update.message.reply_text(
                "⚠️ AI is handling too many requests right now. "
                "Please wait a few seconds and send the prescription again."
            )
            return WAITING_FOR_PRESCRIPTION
        except GeminiAPIError as error:
            logger.error("Prescription AI error: %s", error)
            await update.message.reply_text(
                "❌ I couldn't analyze that prescription. Please try again shortly."
            )
            return WAITING_FOR_PRESCRIPTION

        # Send analysis text
        analysis = analysis.replace('**', '').replace('*', '')
        chunks = split_message(analysis, 3500)
        await update.message.reply_text("✅ Analysis Complete\n")
        for chunk in chunks:
            await update.message.reply_text(chunk)

        await update.message.reply_text(
            "\n━━━━━━━━━━━━━━━━━━\n"
            "⚕️ REMEMBER:\n"
            "• Take medicines as prescribed\n"
            "• Complete full course\n"
            "• Store in cool, dry place\n\n"
            "📅 Generating Google Calendar reminders..."
        )

        # ── PASS 2: Extract structured JSON for calendar links ────────────
        json_prompt = f"""From this prescription analysis, extract each medicine's dosing schedule.
Return ONLY valid JSON, no markdown:
[
  {{"name": "MedicineName", "dosage": "500mg", "times": ["Morning", "Night"], "duration_days": 7}},
  ...
]

Analysis:
{analysis}"""

        try:
            raw_json = await agenerate_text(json_prompt)
            raw_json = raw_json.strip()
            if raw_json.startswith("```"):
                raw_json = raw_json.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            medicines = json.loads(raw_json)
        except Exception as e:
            logger.warning(f"Could not extract structured medicine data: {e}")
            medicines = []

        # ── Send calendar links ───────────────────────────────────────────
        if medicines:
            await update.message.reply_text("📅 Add medicine reminders to Google Calendar:")

            for med in medicines:
                name = med.get("name", "Medicine")
                dosage = med.get("dosage", "as prescribed")
                times = med.get("times", ["Morning"])
                duration = med.get("duration_days", 30)

                buttons = []
                for t in times:
                    url = make_medicine_calendar_url(name, dosage, t, duration)
                    buttons.append([InlineKeyboardButton(
                        text=f"📅 {name} — {t}",
                        url=url
                    )])

                await update.message.reply_text(
                    f"💊 {name} ({dosage}) — {duration} days",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )

            # Offer to set up automatic bot reminders
            await update.message.reply_text(
                "\nWould you like me to also automatically set up daily bot reminders for these medicines?\n\n"
                "Reply 'YES' to set automatic reminders, or 'NO' to skip."
            )

            # Store medicines in user_data for next message
            context.user_data['pending_medicines'] = medicines
            
            return ASKING_REMINDER_CONFIRMATION

        else:
            await update.message.reply_text(
                "📅 To set reminders manually, use /reminder\n\n"
                "Use /prescription for another analysis"
            )

    except Exception as e:
        logger.error(f"Prescription error: {e}")
        await update.message.reply_text(f"Error: {str(e)}\nTry again or /cancel")
        return WAITING_FOR_PRESCRIPTION

    return ConversationHandler.END


async def handle_reminder_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's response to automatic reminder setup"""
    from database import DatabaseManager
    from handlers.reminder_handler import schedule_reminder
    
    user_id = update.effective_user.id
    response = update.message.text.lower().strip()
    
    medicines = context.user_data.get('pending_medicines', [])
    
    if response in ['yes', 'y', 'ok', 'sure', 'yeah', 'yep', 'yup']:
        db = DatabaseManager()
        db.add_user(user_id, update.effective_user.username, update.effective_user.first_name)
        
        reminders_set = 0
        for med in medicines:
            name = med.get("name", "Medicine")
            dosage = med.get("dosage", "as prescribed")
            times = med.get("times", ["Morning"])
            duration_days = med.get("duration_days", 30)
            duration_label = f"{duration_days} days"
            
            for t in times:
                # Map standard times to generic HH:MM for DB
                t_lower = t.lower()
                hour_map = {
                    "morning": 8, "breakfast": 8, "afternoon": 13,
                    "lunch": 13, "evening": 18, "night": 21, "dinner": 19, "bedtime": 21
                }
                
                hour = 8 # default
                for key, val in hour_map.items():
                    if key in t_lower:
                        hour = val
                        break
                
                # Check HH:MM
                if ":" in t:
                    try:
                        parsed = datetime.strptime(t.strip(), "%H:%M")
                        hour = parsed.hour
                    except ValueError:
                        pass
                
                time_str = f"{hour:02d}:00"
                
                # Add to DB
                reminder_id = db.add_reminder(
                    user_id=user_id,
                    med_name=name,
                    dosage=dosage,
                    time=time_str,
                    time_label=t,
                    duration_days=duration_days,
                    duration_label=duration_label
                )
                
                # Schedule
                reminder_data = {
                    'id': reminder_id,
                    'med_name': name,
                    'dosage': dosage,
                    'time': time_str,
                    'time_label': t,
                    'duration_days': duration_days,
                    'duration_label': duration_label
                }
                schedule_reminder(context.job_queue, user_id, reminder_data)
                reminders_set += 1
                
        await update.message.reply_text(
            f"✅ Successfully set {reminders_set} automatic bot reminders!\n\n"
            f"Commands:\n"
            f"/myreminders - View all reminders\n"
            f"/stopreminder - Stop a reminder\n\n"
            f"Use /prescription for another analysis"
        )
    else:
        await update.message.reply_text(
            "OK, no automatic bot reminders set.\n\n"
            "Use /prescription for another analysis"
        )
        
    # Clean up
    context.user_data.pop('pending_medicines', None)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel prescription analysis"""
    context.user_data.pop('pending_medicines', None)
    await update.message.reply_text("Cancelled. Use /prescription to try again.")
    return ConversationHandler.END


def get_handler():
    """Return the conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("prescription", start_prescription)],
        states={
            WAITING_FOR_PRESCRIPTION: [
                MessageHandler(filters.PHOTO, analyze_prescription),
                MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_prescription)
            ],
            ASKING_REMINDER_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reminder_confirmation)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="prescription_analyzer",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=300,
    )
