import logging
from difflib import get_close_matches
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

# All available commands with descriptions
ALL_COMMANDS = {
    "/start": "🏥 Start symptom checker - Analyze your symptoms with AI",
    "/prescription": "💊 Prescription analyzer - Upload prescription image for analysis",
    "/report": "📄 Medical report analyzer - Upload lab/test report for analysis",
    "/hospital": "🏥 Find nearby hospitals - Share location to find nearest hospitals",
    "/pharmacy": "💊 Find nearby pharmacies - Share location to find nearest pharmacies",
    "/encyclopedia": "📚 Medical encyclopedia - Get information about diseases/conditions",
    "/reminder": "⏰ Set medication reminder - Create daily medication reminders",
    "/myreminders": "📋 View reminders - See all your active medication reminders",
    "/stopreminder": "🛑 Stop reminder - Cancel a medication reminder",
    "/mytracking": "📊 View tracking - See all your tracked health conditions",
    "/stoptracking": "🛑 Stop tracking - Cancel health condition tracking",
    "/tips": "💡 Health tips - Get precautions and advice for symptoms or conditions",
    "/help": "❓ Show this help message - List all available commands",
    "/cancel": "❌ Cancel - Cancel current operation",
}

# Command names without slash for matching
COMMAND_NAMES = [cmd[1:] for cmd in ALL_COMMANDS.keys()]


def _find_closest_command(user_input: str) -> str:
    """Find the closest matching command using fuzzy matching."""
    # Remove leading slash if present
    user_input = user_input.lstrip("/").lower()
    
    # Try exact match first
    if user_input in [name.lower() for name in COMMAND_NAMES]:
        return f"/{user_input}"
    
    # Find close matches
    matches = get_close_matches(user_input, COMMAND_NAMES, n=3, cutoff=0.6)
    if matches:
        return f"/{matches[0]}"
    
    return None


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message with all available commands."""
    message = "🏥 **Medical Assistant Bot - Commands**\n\n"
    message += "Here are all available commands:\n\n"
    
    # Group commands by category
    message += "**📋 Health Analysis:**\n"
    message += f"{ALL_COMMANDS['/start']}\n"
    message += f"{ALL_COMMANDS['/prescription']}\n"
    message += f"{ALL_COMMANDS['/report']}\n"
    message += f"{ALL_COMMANDS['/encyclopedia']}\n\n"
    
    message += "**🏥 Services:**\n"
    message += f"{ALL_COMMANDS['/hospital']}\n"
    message += f"{ALL_COMMANDS['/pharmacy']}\n\n"
    
    message += "**💡 Advice:**\n"
    message += f"{ALL_COMMANDS['/tips']}\n\n"
    
    message += "**⏰ Reminders:**\n"
    message += f"{ALL_COMMANDS['/reminder']}\n"
    message += f"{ALL_COMMANDS['/myreminders']}\n"
    message += f"{ALL_COMMANDS['/stopreminder']}\n\n"
    
    message += "**📊 Tracking:**\n"
    message += f"{ALL_COMMANDS['/mytracking']}\n"
    message += f"{ALL_COMMANDS['/stoptracking']}\n\n"
    
    message += "**🛠️ Utilities:**\n"
    message += f"{ALL_COMMANDS['/help']}\n"
    message += f"{ALL_COMMANDS['/cancel']}\n\n"
    
    message += "💡 **Tip:** Type any command to use it. If you make a typo, I'll suggest the correct command!"
    
    await update.message.reply_text(message, parse_mode="Markdown")


async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands and suggest corrections."""
    user_text = update.message.text
    
    # Check if it looks like a command (starts with /)
    if not user_text.startswith("/"):
        return  # Not a command, let other handlers deal with it
    
    # Extract command name
    command_parts = user_text.split()
    user_command = command_parts[0] if command_parts else user_text
    
    # Find closest match
    suggested = _find_closest_command(user_command)
    
    if suggested:
        message = f"❓ Unknown command: `{user_command}`\n\n"
        message += f"Did you mean: {suggested}?\n\n"
        message += f"💡 {ALL_COMMANDS.get(suggested, 'Try this command')}\n\n"
        message += "Type /help to see all available commands."
    else:
        message = f"❓ Unknown command: `{user_command}`\n\n"
        message += "Available commands:\n"
        message += "• /start - Symptom checker\n"
        message += "• /prescription - Prescription analyzer\n"
        message += "• /report - Report analyzer\n"
        message += "• /hospital - Find hospitals\n"
        message += "• /pharmacy - Find pharmacies\n"
        message += "• /tips - Health tips & precautions\n"
        message += "• /encyclopedia - Medical encyclopedia\n"
        message += "• /reminder - Set reminders\n"
        message += "• /myreminders - View reminders\n"
        message += "• /mytracking - View tracking\n"
        message += "• /help - Show all commands\n\n"
        message += "Type /help for detailed information."
    
    await update.message.reply_text(message, parse_mode="Markdown")


def get_handler():
    """Return the help command handler."""
    return CommandHandler("help", help_command)


def get_additional_handlers():
    """Return additional handlers for unknown commands."""
    # This handler should be registered LAST to catch unknown commands
    # It will be added separately in main.py after all other handlers
    return []

