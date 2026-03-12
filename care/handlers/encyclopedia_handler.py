import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from utils.gemini_client import agenerate_text, GeminiQuotaError, GeminiAPIError
from utils.helpers import split_message

logger = logging.getLogger(__name__)


async def encyclopedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provide medical encyclopedia summaries."""
    try:
        # Handle case where args might be None
        args = context.args or []
        query = " ".join(args).strip()

        if not query:
            await update.message.reply_text(
                "📚 Usage: /encyclopedia <disease or medical topic>\n"
                "Example: /encyclopedia dengue fever\n\n"
                "Type /help to see all commands."
            )
            return

        logger.info("Encyclopedia query: %s from user %s", query, update.effective_user.id)
        await update.message.reply_text(f"🔎 Looking up {query} ...")

        prompt = f"""You are a concise medical encyclopedia.
Provide an easy-to-read overview about: {query}

Structure the response as plain text sections:
1. OVERVIEW (what it is)
2. COMMON SYMPTOMS
3. CAUSES & RISK FACTORS
4. DIAGNOSIS
5. TREATMENT OPTIONS
6. WHEN TO SEEK EMERGENCY CARE
7. PREVENTION / SELF-CARE

Use short sentences, avoid markdown bullets, and mention that the info is not a diagnosis."""

        try:
            response = await agenerate_text(prompt)
        except GeminiQuotaError:
            await update.message.reply_text(
                "⚠️ Too many requests at the moment. Please try /encyclopedia again in a few seconds."
            )
            return
        except GeminiAPIError as exc:
            logger.error("Encyclopedia AI error: %s", exc, exc_info=True)
            await update.message.reply_text(
                "❌ I couldn't fetch that information right now. Please try again soon."
            )
            return
        except Exception as exc:
            logger.error("Unexpected error in encyclopedia: %s", exc, exc_info=True)
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )
            return

        if not response:
            await update.message.reply_text(
                "❌ I couldn't get information about that topic. Please try a different query."
            )
            return

        response = response.replace("**", "")
        chunks = split_message(response, 3500)
        
        for chunk in chunks:
            await update.message.reply_text(chunk)

        await update.message.reply_text(
            "ℹ️ This information is educational only. Always consult a healthcare professional for diagnosis or treatment."
        )
        
    except Exception as exc:
        logger.error("Critical error in encyclopedia handler: %s", exc, exc_info=True)
        try:
            await update.message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
        except Exception:
            pass


def get_handler():
    """Return the command handler for /encyclopedia"""
    return CommandHandler("encyclopedia", encyclopedia)


def get_additional_handlers():
    return []

