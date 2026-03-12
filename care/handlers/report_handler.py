import logging
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from utils.gemini_client import (
    agenerate_with_image,
    GeminiQuotaError,
    GeminiAPIError,
)
from utils.helpers import download_photo, download_document_image, split_message

logger = logging.getLogger(__name__)

WAITING_FOR_REPORT = 0


async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to upload a medical report for analysis."""
    await update.message.reply_text(
        "📄 Medical Report Analyzer\n\n"
        "Please upload a clear photo of your lab or diagnostic report. "
        "Try to capture the entire page so I can read the values.\n\n"
        "I'll extract:\n"
        "• Each parameter and your value\n"
        "• Typical reference range\n"
        "• High/low indicators & health tips\n"
        "• Suggestions on what to discuss with your doctor\n\n"
        "📸 Send the report image now (or /cancel)."
    )
    return WAITING_FOR_REPORT


async def analyze_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze a medical report image and summarize findings."""
    image = None

    if update.message.photo:
        image = await download_photo(update.message.photo[-1])
    elif update.message.document and update.message.document.mime_type:
        if update.message.document.mime_type.startswith("image/"):
            image = await download_document_image(update.message.document)
        else:
            await update.message.reply_text(
                "⚠️ Please send the report as an image (JPG/PNG). PDF and other files "
                "aren't supported yet."
            )
            return WAITING_FOR_REPORT
    else:
        await update.message.reply_text(
            "I need a clear photo of the report. Please send an image or use /cancel."
        )
        return WAITING_FOR_REPORT

    await update.message.reply_text("🧪 Reading your report... please wait.")

    try:
        notes = update.message.caption or "No extra notes provided."

        prompt = f"""You are an experienced clinical pathologist.
Analyze the lab/diagnostic report in the image and produce a detailed yet readable summary for a patient.

Patient notes: {notes}

Format the response as plain text without markdown tables.

Sections to include:
━━━━━━━━━━━━━━━━━━
1. QUICK SNAPSHOT
• Brief overview of what the report measures and any standout concerns.

2. PARAMETER DETAILS
For each measurable parameter you can read:
• Parameter: [Name]
• Patient Value: [value + units]
• Typical Range: [adult reference range with units; say "typical range" if inferred]
• Interpretation: (Low/Normal/High) + short explanation of potential causes/effects
Mark abnormal results with ⚠️ and critical ones with 🚨.

3. KEY ANOMALIES
List only the parameters that are outside the normal range with a short action tip (hydration, diet, see doctor, etc.).

4. SUGGESTED NEXT STEPS
• Lifestyle or dietary suggestions
• When to repeat the test
• When to contact a doctor/specialist

5. DISCLAIMER
Remind the user this is informational and not a diagnosis.
"""

        try:
            analysis = await agenerate_with_image(prompt, image)
        except GeminiQuotaError:
            await update.message.reply_text(
                "⚠️ I'm getting too many report requests right now. "
                "Please wait half a minute and resend the photo."
            )
            return WAITING_FOR_REPORT
        except GeminiAPIError as error:
            logger.error("Report AI error: %s", error)
            await update.message.reply_text(
                "❌ I couldn't read the report due to an AI error. Please try again shortly."
            )
            return WAITING_FOR_REPORT
        analysis = analysis.replace("**", "")

        chunks = split_message(analysis, 3500)

        await update.message.reply_text("✅ Report analysis ready.")
        for chunk in chunks:
            await update.message.reply_text(chunk)

        await update.message.reply_text(
            "🙏 Always review lab results with your healthcare provider for a proper diagnosis."
        )

    except Exception as e:
        logger.error("Report analysis failed: %s", e, exc_info=True)
        await update.message.reply_text(
            f"❌ Sorry, I couldn't read the report ({e}). Please try again or /cancel."
        )
        return WAITING_FOR_REPORT

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel report analysis."""
    await update.message.reply_text("Cancelled. Use /report when you're ready.")
    return ConversationHandler.END


def get_handler():
    """Return the conversation handler for report analysis."""
    return ConversationHandler(
        entry_points=[CommandHandler("report", start_report)],
        states={
            WAITING_FOR_REPORT: [
                MessageHandler(filters.PHOTO, analyze_report),
                MessageHandler(filters.Document.IMAGE, analyze_report),
                MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_report),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="report_analyzer",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=300,
    )


def get_additional_handlers():
    """Return additional handlers (currently none)."""
    return []

