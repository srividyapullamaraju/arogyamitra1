import logging
import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from utils.gemini_client import (
    agenerate_text,
    agenerate_with_image,
    agenerate_with_audio,
    GeminiQuotaError,
    GeminiAPIError,
)
from utils.helpers import split_message, download_photo, download_audio_bytes
from database import DatabaseManager

logger = logging.getLogger(__name__)

# States
ASKING_SYMPTOMS, ASKING_FOLLOWUP, WAITING_FOR_IMAGE = range(3)

# Storage
user_consultations = {}


async def _handle_gemini_error(update: Update, error: Exception):
    """Notify user when Gemini fails."""
    logger.warning("Gemini error for user %s: %s", update.effective_user.id, error)
    if isinstance(error, GeminiQuotaError):
        message = (
            "⚠️ I'm receiving too many AI requests right now. "
            "Please wait about 30 seconds and try again."
        )
    else:
        message = (
            "❌ I couldn't reach the AI service just now. "
            "Please try again in a moment."
        )
    await update.message.reply_text(message)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start symptom checker"""
    user_id = update.effective_user.id
    user_consultations[user_id] = {
        "symptoms": [],
        "answers": [],
        "images": [],
        "question_count": 0,
        "conversation": ""
    }
    
    await update.message.reply_text(
        "🏥 Medical Symptom Checker\n\n"
        "I can help analyze your symptoms.\n\n"
        "⚠️ DISCLAIMER: Not a substitute for professional medical advice.\n\n"
        "📋 Quick Commands:\n"
        "• /start - Symptom check\n"
        "• /prescription - Analyze prescription\n"
        "• /report - Analyze medical report\n"
        "• /hospital - Find nearby hospitals\n"
        "• /encyclopedia - Medical information\n"
        "• /reminder - Set medication reminder\n"
        "• /myreminders - View reminders\n"
        "• /mytracking - View tracked conditions\n"
        "• /help - See all commands\n"
        "• /cancel - Cancel\n\n"
        "Please describe your main symptom:"
    )
    
    return ASKING_SYMPTOMS

async def collect_symptom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect initial symptom"""
    user_id = update.effective_user.id
    
    if update.message.photo:
        image = await download_photo(update.message.photo[-1])
        prompt = """Briefly describe what you see in 2-3 sentences.
Focus on observable features. Do NOT diagnose."""

        try:
            analysis = await agenerate_with_image(prompt, image)
        except (GeminiQuotaError, GeminiAPIError) as error:
            await _handle_gemini_error(update, error)
            await update.message.reply_text(
                "Please describe your main symptom in text so I can continue."
            )
            return ASKING_SYMPTOMS

        user_consultations[user_id]["conversation"] += f"Image: {analysis}\n\n"
        await update.message.reply_text(f"📸 I see: {analysis}")
    else:
        symptom = update.message.text
        user_consultations[user_id]["symptoms"].append(symptom)
        user_consultations[user_id]["conversation"] = f"Complaint: {symptom}\n\n"
    
    # Ask first question
    return await ask_question(update, user_id)


async def collect_symptom_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voice/audio when the bot is asking for initial symptoms.

    We transcribe the audio using Gemini and treat it like a typed symptom.
    """
    user_id = update.effective_user.id

    voice_or_audio = update.message.voice or update.message.audio
    if not voice_or_audio:
        # Fallback: keep asking for text if something unexpected happens
        await update.message.reply_text(
            "I couldn't read this audio message. Please type your main symptom."
        )
        return ASKING_SYMPTOMS

    try:
        audio_bytes = await download_audio_bytes(voice_or_audio)
        mime_type = getattr(voice_or_audio, "mime_type", "audio/ogg")

        transcript_prompt = (
            "You will be given a short medical symptom description as audio.\n"
            "Transcribe it accurately into plain text.\n"
            "Return ONLY the transcription without any extra words or formatting."
        )
        symptom_text = await agenerate_with_audio(transcript_prompt, audio_bytes, mime_type)
    except (GeminiQuotaError, GeminiAPIError) as error:
        await _handle_gemini_error(update, error)
        await update.message.reply_text(
            "I had trouble understanding the audio. Please type your main symptom instead."
        )
        return ASKING_SYMPTOMS

    user_consultations[user_id]["symptoms"].append(symptom_text)
    user_consultations[user_id]["conversation"] = f"Complaint: {symptom_text}\n\n"

    await update.message.reply_text(f"📝 I heard: {symptom_text}")

    # Ask first question using the transcribed text
    return await ask_question(update, user_id)

async def ask_question(update: Update, user_id):
    """Ask next question"""
    consultation = user_consultations[user_id]
    
    prompt = f"""Based on: {consultation['conversation']}
Questions asked: {consultation['question_count']}

If 4-5 questions asked, respond: READY_FOR_DIAGNOSIS
Otherwise, ask ONE clear follow-up question.

check which language the user is conversing in and track that language and respond in the same language for all subsequent questions and answers."""

    try:
        response = await agenerate_text(prompt)
    except (GeminiQuotaError, GeminiAPIError) as error:
        await _handle_gemini_error(update, error)
        await update.message.reply_text("Use /start to try the symptom checker again.")
        if user_id in user_consultations:
            del user_consultations[user_id]
        return ConversationHandler.END
    
    if "READY_FOR_DIAGNOSIS" in response:
        return await provide_diagnosis(update, user_id)
    
    consultation["current_question"] = response
    consultation["question_count"] += 1
    
    await update.message.reply_text(f"📋 Q{consultation['question_count']}: {response}")
    return ASKING_FOLLOWUP

async def collect_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect answer to question"""
    user_id = update.effective_user.id
    
    # Check if user is responding to tracking confirmation
    if user_id in user_consultations and 'awaiting_tracking_confirmation' in user_consultations[user_id]:
        return await handle_tracking_confirmation(update, context)
    
    answer = update.message.text
    
    consultation = user_consultations[user_id]
    consultation["answers"].append({"q": consultation["current_question"], "a": answer})
    consultation["conversation"] += f"Q: {consultation['current_question']}\nA: {answer}\n\n"
    
    return await ask_question(update, user_id)


async def collect_answer_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voice/audio when the bot is asking follow-up questions.

    We transcribe the audio using Gemini and treat it like a typed answer.
    """
    user_id = update.effective_user.id

    # Check if user is responding to tracking confirmation
    if user_id in user_consultations and 'awaiting_tracking_confirmation' in user_consultations[user_id]:
        # For tracking confirmation, it's safer to require text YES/NO
        await update.message.reply_text(
            "Please reply with YES or NO in text so I can set up your reminders correctly."
        )
        return ASKING_FOLLOWUP

    voice_or_audio = update.message.voice or update.message.audio
    if not voice_or_audio:
        await update.message.reply_text(
            "I couldn't read this audio message. Please type your answer."
        )
        return ASKING_FOLLOWUP

    try:
        audio_bytes = await download_audio_bytes(voice_or_audio)
        mime_type = getattr(voice_or_audio, "mime_type", "audio/ogg")

        transcript_prompt = (
            "You will be given a short spoken answer to a medical question as audio.\n"
            "Transcribe it accurately into plain text.\n"
            "Return ONLY the transcription without any extra words or formatting."
        )
        answer_text = await agenerate_with_audio(transcript_prompt, audio_bytes, mime_type)
    except (GeminiQuotaError, GeminiAPIError) as error:
        await _handle_gemini_error(update, error)
        await update.message.reply_text(
            "I had trouble understanding the audio. Please type your answer instead."
        )
        return ASKING_FOLLOWUP

    consultation = user_consultations[user_id]
    consultation["answers"].append({"q": consultation["current_question"], "a": answer_text})
    consultation["conversation"] += f"Q: {consultation['current_question']}\nA: {answer_text}\n\n"

    await update.message.reply_text(f"📝 I heard: {answer_text}")

    return await ask_question(update, user_id)

async def provide_diagnosis(update: Update, user_id):
    """Provide final diagnosis"""
    consultation = user_consultations[user_id]
    
    prompt = f"""Based on: {consultation['conversation']}

Provide assessment:

🔍 POSSIBLE CONDITIONS (2-3 most likely) and probability of each condition.

💡 REASONING (why you think so)

⚠️ SEVERITY (Urgent/Moderate/Mild)

👨‍⚕️ RECOMMENDATIONS (what to do next)

🚨 WARNING SIGNS (symptoms requiring immediate attention)

🏠 SELF-CARE (safe home remedies if applicable)

check which language the user is conversing in and track that language and respond in the same language for all subsequent questions and answers.

provide general medicine name and dosage if applicable.

📅 FOLLOW-UP SCHEDULE
Based on this condition, recommend follow-up check dates.
Format EXACTLY as: "FOLLOWUP: Day 3, Day 7, Day 14" (adjust days based on severity)
- If urgent/severe: Day 1, Day 3, Day 7
- If moderate: Day 3, Day 7, Day 14
- If mild: Day 7, Day 14

Keep explanations clear and concise. Do NOT use markdown formatting like asterisks or hash symbols."""

    try:
        diagnosis = await agenerate_text(prompt)
    except (GeminiQuotaError, GeminiAPIError) as error:
        await _handle_gemini_error(update, error)
        await update.message.reply_text("Please try /start again in a little while.")
        del user_consultations[user_id]
        return ConversationHandler.END
    
    # Remove any remaining markdown
    diagnosis = diagnosis.replace('**', '').replace('*', '').replace('###', '').replace('##', '').replace('__', '')
    
    chunks = split_message(diagnosis)
    
    await update.message.reply_text("✅ Assessment Complete")
    for chunk in chunks:
        await update.message.reply_text(chunk)
    
    # Extract follow-up schedule and offer to set tracking
    followup_days = extract_followup_days(diagnosis)
    
    if followup_days:
        # Save consultation to database
        db = DatabaseManager()
        db.add_user(user_id, update.effective_user.username, update.effective_user.first_name)
        db.save_consultation(user_id, consultation['conversation'], diagnosis)
        
        # Offer to set up automatic tracking
        followup_text = ", ".join([f"Day {d}" for d in followup_days])
        
        await update.message.reply_text(
            f"\n📅 Recommended Follow-ups: {followup_text}\n\n"
            "Would you like me to automatically remind you to check your progress?\n\n"
            "Reply 'YES' to set automatic reminders, or 'NO' to skip."
        )
        
        # Store for next message
        user_consultations[user_id]['awaiting_tracking_confirmation'] = {
            'followup_days': followup_days,
            'diagnosis': diagnosis
        }
        
        return ASKING_FOLLOWUP  # Keep in conversation to receive yes/no
    
    await update.message.reply_text(
        "\n⚕️ Consult a healthcare provider for proper diagnosis.\n\n"
        "Use /start for new consultation."
    )
    
    del user_consultations[user_id]
    return ConversationHandler.END

def extract_followup_days(diagnosis: str) -> list:
    """Extract follow-up days from diagnosis"""
    # Look for "FOLLOWUP: Day X, Day Y" pattern
    match = re.search(r'FOLLOWUP:?\s*(.+?)(?:\n|$)', diagnosis, re.IGNORECASE)
    if match:
        followup_text = match.group(1)
        days = re.findall(r'Day (\d+)', followup_text, re.IGNORECASE)
        return [int(d) for d in days] if days else []
    
    # Fallback: look for any "Day X" mentions
    days = re.findall(r'Day (\d+)', diagnosis, re.IGNORECASE)
    if days:
        return [int(d) for d in days[:3]]  # Max 3 follow-ups
    
    return []

async def handle_tracking_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's response to tracking setup"""
    user_id = update.effective_user.id
    response = update.message.text.lower().strip()
    
    tracking_context = user_consultations[user_id]['awaiting_tracking_confirmation']
    
    if response in ['yes', 'y', 'ok', 'sure', 'yeah', 'yep', 'yup']:
        # Set up automatic tracking
        followup_days = tracking_context['followup_days']
        diagnosis = tracking_context['diagnosis']
        
        # Extract condition type from diagnosis
        condition_type = "Health condition"
        lines = diagnosis.split('\n')
        for i, line in enumerate(lines):
            if "POSSIBLE CONDITIONS" in line or "🔍" in line:
                if i + 1 < len(lines):
                    condition_type = lines[i + 1].strip()
                    # Take first condition only
                    if ',' in condition_type:
                        condition_type = condition_type.split(',')[0]
                    break
        
        # Save to database
        db = DatabaseManager()
        tracking_id = db.add_health_tracking(
            user_id=user_id,
            condition_type=condition_type,
            initial_description=user_consultations[user_id]['conversation'],
            initial_image_path=None,
            initial_analysis=diagnosis,
            followup_days=",".join(map(str, followup_days))
        )
        
        # Schedule reminders
        for day in followup_days:
            reminder_time = datetime.now() + timedelta(days=day)
            reminder_time = reminder_time.replace(hour=10, minute=0, second=0, microsecond=0)
            
            context.job_queue.run_once(
                send_tracking_reminder,
                when=reminder_time,
                data={
                    'user_id': user_id,
                    'tracking_id': tracking_id,
                    'day_number': day,
                    'condition_type': condition_type
                },
                name=f"tracking_{user_id}_{tracking_id}_{day}"
            )
        
        followup_dates = "\n".join([
            f"• Day {d} ({(datetime.now() + timedelta(days=d)).strftime('%b %d, %Y')})"
            for d in followup_days
        ])
        
        await update.message.reply_text(
            f"✅ Automatic reminders set!\n\n"
            f"🆔 Tracking ID: #{tracking_id}\n\n"
            f"📅 I'll remind you on:\n{followup_dates}\n\n"
            f"On each date, I'll ask you to:\n"
            f"• Send updated photo (if applicable)\n"
            f"• Describe current status\n\n"
            f"I'll compare with your initial symptoms and assess progress.\n\n"
            f"Commands:\n"
            f"/mytracking - View all tracked conditions\n"
            f"/stoptracking - Stop tracking"
        )
    else:
        await update.message.reply_text(
            "OK, no reminders set.\n\n"
            "⚕️ Remember to consult a healthcare provider.\n\n"
            "Use /start for a new symptom check."
        )
    
    # Clean up
    del user_consultations[user_id]
    return ConversationHandler.END

async def send_tracking_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send follow-up reminder"""
    job = context.job
    user_id = job.data['user_id']
    tracking_id = job.data['tracking_id']
    day_number = job.data['day_number']
    condition_type = job.data['condition_type']
    
    message = (
        f"⏰ Health Check Reminder\n\n"
        f"📋 Condition: {condition_type}\n"
        f"🆔 Tracking ID: #{tracking_id}\n"
        f"📅 Day {day_number} Follow-up\n\n"
        f"Time to check your progress!\n\n"
        f"Please reply with:\n"
        f"📸 Updated photo (if applicable)\n"
        f"OR\n"
        f"✍️ Description of current status\n\n"
        f"I'll compare with your initial symptoms and assess healing."
    )
    
    try:
        await context.bot.send_message(chat_id=user_id, text=message)
        logger.info(f"Sent tracking reminder to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send reminder: {e}")

async def view_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all tracked conditions"""
    user_id = update.effective_user.id
    db = DatabaseManager()
    
    trackings = db.get_user_trackings(user_id)
    
    if not trackings:
        await update.message.reply_text(
            "📭 You don't have any tracked conditions.\n\n"
            "Tracked conditions are set up automatically after symptom checks when you say YES to reminders."
        )
        return
    
    message = "📋 Your Tracked Conditions:\n\n"
    
    for tracking in trackings:
        status = "✅ Active" if tracking['is_active'] else "⏹️ Stopped"
        message += (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 #{tracking['id']}\n"
            f"📋 {tracking['condition_type']}\n"
            f"📅 Started: {tracking['created_at'][:10]}\n"
            f"Status: {status}\n"
        )
    
    message += "\n━━━━━━━━━━━━━━━━━━\n"
    message += "Use /stoptracking to stop monitoring a condition"
    
    await update.message.reply_text(message)

async def stop_tracking_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start stop tracking process"""
    user_id = update.effective_user.id
    db = DatabaseManager()
    
    trackings = db.get_user_trackings(user_id, active_only=True)
    
    if not trackings:
        await update.message.reply_text("📭 No active tracked conditions.")
        return ConversationHandler.END
    
    message = "Which condition would you like to stop tracking?\n\n"
    
    for tracking in trackings:
        message += f"🆔 #{tracking['id']}: {tracking['condition_type']}\n"
    
    message += "\nReply with tracking ID number"
    
    await update.message.reply_text(message)
    return 0

async def stop_tracking_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and stop tracking"""
    user_id = update.effective_user.id
    
    try:
        tracking_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid tracking ID")
        return 0
    
    db = DatabaseManager()
    success = db.deactivate_tracking(tracking_id, user_id)
    
    if success:
        # Remove scheduled reminders
        current_jobs = context.job_queue.jobs()
        for job in current_jobs:
            if job.name and job.name.startswith(f"tracking_{user_id}_{tracking_id}_"):
                job.schedule_removal()
        
        await update.message.reply_text(
            f"✅ Stopped tracking condition #{tracking_id}\n\n"
            "All follow-up reminders have been cancelled."
        )
    else:
        await update.message.reply_text("❌ Tracking ID not found")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel consultation"""
    user_id = update.effective_user.id
    if user_id in user_consultations:
        del user_consultations[user_id]
    await update.message.reply_text("Cancelled. Use /start to begin again.")
    return ConversationHandler.END

def get_handler():
    """Return the conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING_SYMPTOMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_symptom),
                MessageHandler(filters.PHOTO, collect_symptom),
                MessageHandler((filters.VOICE | filters.AUDIO) & ~filters.COMMAND, collect_symptom_voice),
            ],
            ASKING_FOLLOWUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_answer),
                MessageHandler((filters.VOICE | filters.AUDIO) & ~filters.COMMAND, collect_answer_voice),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="symptom_checker",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=600,
    )

def get_additional_handlers():
    """Return additional command handlers"""
    return [
        CommandHandler("mytracking", view_tracking),
        ConversationHandler(
            entry_points=[CommandHandler("stoptracking", stop_tracking_start)],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_tracking_confirm)]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            name="stop_tracking",
            persistent=False
        )
    ]