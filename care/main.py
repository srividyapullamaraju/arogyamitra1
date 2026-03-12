import logging
from datetime import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from telegram import Update
from telegram.ext import Application, Defaults, ContextTypes, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN, BOT_TIMEZONE
from handlers import (
    symptom_handler,
    prescription_handler,
    reminder_handler,
    report_handler,
    hospital_handler,
    pharmacy_handler,
    encyclopedia_handler,
    tips_handler,
    help_handler,
)
from database import DatabaseManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def _get_bot_timezone():
    try:
        return ZoneInfo(BOT_TIMEZONE)
    except ZoneInfoNotFoundError:
        logger.warning(
            "Invalid BOT_TIMEZONE '%s'. Falling back to UTC.",
            BOT_TIMEZONE,
        )
        return timezone.utc

async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update %s caused error: %s", update, context.error)
    if update and getattr(update, "effective_message", None):
        try:
            await update.effective_message.reply_text(
                "⚠️ Something went wrong. Please try again."
            )
        except Exception:
            pass


def main():
    logger.info("Starting Medical Assistant Bot...")
    
    db = DatabaseManager()
    logger.info("Database initialized")
    
    tzinfo = _get_bot_timezone()
    defaults = Defaults(tzinfo=tzinfo)
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .defaults(defaults)
        .build()
    )
    
    # Register handlers in correct order:
    # 1. Simple CommandHandlers first (highest priority)
    # 2. ConversationHandlers last (lower priority)
    
    # Simple command handlers (registered first for priority)
    application.add_handler(help_handler.get_handler())
    for handler in help_handler.get_additional_handlers():
        application.add_handler(handler)
    
    logger.info("Registering /encyclopedia command handler...")
    enc_handler = encyclopedia_handler.get_handler()
    logger.info("Encyclopedia handler created: %s", type(enc_handler).__name__)
    application.add_handler(enc_handler)
    logger.info("✅ /encyclopedia handler registered successfully")
    for handler in encyclopedia_handler.get_additional_handlers():
        application.add_handler(handler)
    
    # Conversation handlers (registered after command handlers)
    application.add_handler(prescription_handler.get_handler())

    application.add_handler(report_handler.get_handler())
    for handler in report_handler.get_additional_handlers():
        application.add_handler(handler)

    application.add_handler(hospital_handler.get_handler())
    for handler in hospital_handler.get_additional_handlers():
        application.add_handler(handler)
        
    application.add_handler(pharmacy_handler.get_handler())
    for handler in pharmacy_handler.get_additional_handlers():
        application.add_handler(handler)
        
    application.add_handler(tips_handler.get_handler())
    for handler in tips_handler.get_additional_handlers():
        application.add_handler(handler)
    
    application.add_handler(reminder_handler.get_handler())
    for handler in reminder_handler.get_additional_handlers():
        application.add_handler(handler)
    
    application.add_handler(symptom_handler.get_handler())
    for handler in symptom_handler.get_additional_handlers():
        application.add_handler(handler)
    
    # Error handler
    application.add_error_handler(handle_error)
    
    # Unknown command handler (must be registered LAST to catch typos)
    from handlers.help_handler import handle_unknown_command
    application.add_handler(
        MessageHandler(
            filters.COMMAND & ~filters.Regex(
                r"^(start|prescription|report|hospital|pharmacy|tips|encyclopedia|reminder|myreminders|stopreminder|mytracking|stoptracking|help|cancel)$"
            ),
            handle_unknown_command
        )
    )
    
    reminder_handler.init_reminders_on_startup(application)
    
    logger.info("✅ Bot is running!")
    print("🏥 Medical Assistant Bot READY!")
    print("📸 Image analysis ✓")
    print("💊 Prescription analyzer ✓")
    print("⏰ Medication reminders ✓")
    print("📊 Health tracking ✓")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()