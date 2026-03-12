import logging
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from utils.gemini_client import agenerate_text, GeminiQuotaError, GeminiAPIError
from utils.helpers import split_message

logger = logging.getLogger(__name__)

WAITING_FOR_TOPIC = 0


async def start_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for /tips command."""
    # Check if user provided an argument immediately, e.g. /tips having fever
    if context.args:
        topic = " ".join(context.args)
        return await analyze_tips_topic(update, context, topic)

    await update.message.reply_text(
        "💡 Health Tips & Precautions\n\n"
        "What do you need advice for today?\n"
        "For example, you can reply with 'having fever' or 'lower back pain'."
    )

    return WAITING_FOR_TOPIC


async def receive_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive topic text from user."""
    topic = update.message.text
    return await analyze_tips_topic(update, context, topic)


async def analyze_tips_topic(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    """Generate and send AI response based on topic."""
    await update.message.reply_text("💡 Fetching structured health tips...")

    prompt = f"""Provide health advice and precautions for: "{topic}"

Please follow these strict rules to format your output:
- Start with 💡 PRECAUTIONS
- Give bullet points on what SHOULD be done.
- Keep the language exactly to the point and concise.
- Check which language the user is conversing in ("{topic}") and track that language, responding strictly in the same language. 
- Do NOT use any Markdown (like asterisks or hash symbols).
- Only provide relevant suggestions."""

    try:
        response = await agenerate_text(prompt)
    except GeminiQuotaError:
        await update.message.reply_text(
            "⚠️ AI is handling too many requests right now. "
            "Please wait a few seconds and try again."
        )
        return ConversationHandler.END
    except GeminiAPIError as error:
        logger.error("Tips AI error: %s", error)
        await update.message.reply_text(
            "❌ I couldn't generate advice for that topic right now. Please try again shortly."
        )
        return ConversationHandler.END

    # Remove markdown just in case the AI ignored instructions
    response = response.replace('**', '').replace('*', '').replace('###', '').replace('##', '').replace('__', '')
    
    chunks = split_message(response)
    
    for chunk in chunks:
        await update.message.reply_text(chunk)
        
    await update.message.reply_text(
        "\n⚕️ Remember: This advice is not a substitute for professional medical care. "
        "Use /tips for advice on another subject."
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the tips conversation."""
    await update.message.reply_text("Cancelled tips request.")
    return ConversationHandler.END


def get_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("tips", start_tips)],
        states={
            WAITING_FOR_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="health_tips",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=300,
    )


def get_additional_handlers():
    return []
