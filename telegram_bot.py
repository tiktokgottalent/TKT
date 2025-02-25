import logging
import warnings
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler

# Suppress warnings for a cleaner log
warnings.filterwarnings("ignore", category=UserWarning)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define states for the conversation
AGREEMENT, PHONE, AGE, TALENT, REGISTRATION_CODE = range(5)

# Start command
async def start(update: Update, context):
    logger.debug("Start command triggered.")
    await update.message.reply_text("Welcome to TikTok Got Talent! Please read the agreement policy.")
    await show_agreement(update, context)
    return AGREEMENT

# Agreement policy
async def show_agreement(update: Update, context):
    agreement_text = """
    **TikTok Got Talent Agreement Policy**
    - Participants must be 18+ with a valid ID.
    - Perform original, legal content.
    - Audience engagement determines winners.
    - 40% of TikTok gifts may be shared.
    - Vote manipulation or offensive behavior leads to removal.
    """
    keyboard = [[InlineKeyboardButton("Agree", callback_data="agree")],
                [InlineKeyboardButton("Decline", callback_data="decline")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(agreement_text, reply_markup=reply_markup)

# Handle agreement response
async def handle_agreement(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "agree":
        await query.edit_message_text("You agreed to the policy. Please share your phone number.")
        keyboard = [[KeyboardButton("Share Phone Number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await query.message.reply_text("Tap the button below to share your phone number:", reply_markup=reply_markup)
        return PHONE
    else:
        await query.edit_message_text("You declined the policy. Registration stopped.")
        return ConversationHandler.END

# Handle phone number
async def handle_phone(update: Update, context):
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Please use the button to share your phone number.")
        return PHONE
    
    context.user_data["phone"] = contact.phone_number
    logger.debug(f"Phone number received: {contact.phone_number}")
    await update.message.reply_text("Please enter your age:")
    return AGE

# Handle age
async def handle_age(update: Update, context):
    try:
        age = int(update.message.text)
        if age < 18:
            await update.message.reply_text("You must be 18 or older. Please re-enter your age.")
            return AGE
        context.user_data["age"] = age
        await show_talent_categories(update, context)
        return TALENT
    except ValueError:
        await update.message.reply_text("Please enter a valid age.")
        return AGE

# Show talent categories
async def show_talent_categories(update: Update, context):
    keyboard = [[InlineKeyboardButton("Singing", callback_data="singing")],
                [InlineKeyboardButton("Dancing", callback_data="dancing")],
                [InlineKeyboardButton("Magic", callback_data="magic")],
                [InlineKeyboardButton("Other", callback_data="other")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select your talent category:", reply_markup=reply_markup)

# Handle talent selection
async def handle_talent(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    # Debugging print
    logger.debug(f"Talent selected: {query.data}")

    if query.data == "other":
        await query.edit_message_text("Please type your talent manually.")
        return TALENT
    
    context.user_data["talent"] = query.data
    
    # Check if bot moves forward
    await update.callback_query.message.reply_text("Generating your registration code...")
    await generate_registration_code(update, context)
    return REGISTRATION_CODE


# Generate registration code
import os
import json

# File to store category-wise registration counts
REG_COUNT_FILE = "registration_counts.json"

# Function to load registration counts from file
def load_registration_counts():
    if os.path.exists(REG_COUNT_FILE):
        with open(REG_COUNT_FILE, "r") as file:
            return json.load(file)
    return {"SING": 0, "DANC": 0, "MAG": 0, "OTH": 0}  # Default counts

# Function to update and save registration counts
def increment_registration_count(category):
    counts = load_registration_counts()
    counts[category] += 1  # Increment the count for the selected category
    
    with open(REG_COUNT_FILE, "w") as file:
        json.dump(counts, file)  # Save updated counts
    
    return counts[category]  # Return the updated count for numbering

async def generate_registration_code(update: Update, context):
    if "phone" not in context.user_data or "talent" not in context.user_data:
        await update.message.reply_text("Error: Missing required details. Please restart registration.")
        return ConversationHandler.END

    # Define category abbreviations
    talent_map = {
        "singing": "SING",
        "dancing": "DANC",
        "magic": "MAG",
        "other": "OTH"
    }

    talent = context.user_data["talent"].lower()
    category_code = talent_map.get(talent, "OTH")  # Default to "OTH" if not found

    # Get the registration number specific to the talent category
    reg_number = increment_registration_count(category_code)
    formatted_number = f"{reg_number:03d}"  # Format as three-digit (001, 002, ...)

    # Generate the final registration code
    registration_code = f"TKT-{category_code}-{formatted_number}"
    context.user_data["registration_code"] = registration_code

    logger.debug(f"✅ Registration code generated: {registration_code}")

    # Send the registration code to the user
    await update.callback_query.message.reply_text(f"🎉 Registration Complete! Your code: `{registration_code}`", parse_mode="Markdown")

    return ConversationHandler.END



# Main function
def main():
    application = Application.builder().token("7682496291:AAG-HvMBugcIV-bcfYNVgJKMnpSAQ20dvhE").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AGREEMENT: [CallbackQueryHandler(handle_agreement)],
            PHONE: [MessageHandler(filters.CONTACT, handle_phone)],
            AGE: [MessageHandler(filters.TEXT, handle_age)],
            TALENT: [CallbackQueryHandler(handle_talent), MessageHandler(filters.TEXT, handle_talent)],
            REGISTRATION_CODE: [MessageHandler(filters.TEXT, generate_registration_code)]
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
