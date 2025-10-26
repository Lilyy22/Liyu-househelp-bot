import logging
import os
import re
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
MAIN_MENU, INFO, SETTINGS, LANGUAGE, SERVICE_TYPE, SERVICES, SERVICES_OTHER, CONTACT_CHECK, NAME_CONFIRM, PHONE, LOCATION, CONFIRMATION, POST_SUBMISSION = range(13)

# Main menu options
MAIN_MENU_OPTIONS = {
    'english': [["🚀 Start", "ℹ️ Info", "⚙️ Settings"]],
    'amharic': [["🚀 ጀምር", "ℹ️ መረጃ", "⚙️ ማስተካከያ"]]
}

# Language selection menu
LANGUAGE_MENU = [["🇬🇧 English", "🇪🇹 Amharic"]]

# Menu options in both languages
MENU_TEXT = {
    'english': {
        'service_type_menu': [["⏰ Permanent", "🔄 Temporary"]],
        'main_services_menu': [
            ["🧹 Full House Work", "🏠 House Cleaning"],
            ["👕 Laundry Service", "🍳 Cooking Service"],
            ["👶 Child Care", "👵 Elder Care"]
        ],
        'name_confirm_menu': [
            ["✅ Use My Telegram Name", "✏️ Enter Different Name"]
        ],
        'confirmation_menu': [
            ["✅ Confirm & Submit Request"],
            ["✏️ Edit Service Type", "✏️ Edit Services"],
            ["✏️ Edit Name", "✏️ Edit Phone"],
            ["✏️ Edit Location", "❌ Cancel Request"]
        ],
        'back_to_menu': [["🏠 Back to Main Menu"]],
        'settings_menu': [["🌍 Change Language"], ["🏠 Back to Main Menu"]]
    },
    'amharic': {
        'service_type_menu': [["⏰ ቋሚ", "🔄 ጊዜያዊ"]],
        'main_services_menu': [
            ["🧹 ሙሉ የቤት ስራ", "🏠 የቤት ፅዳት"],
            ["👕 የልብስ እጥበት", "🍳 ምግብ አብሳይ"],
            ["👶 ህጻናት እንክብካቤ", "👵 የአዛውንት እንክብካቤ"]
        ],
        'name_confirm_menu': [
            ["✅ የቴሌግራም ስሜን ተጠቀም", "✏️ ሌላ ስም አስገባ"]
        ],
        'confirmation_menu': [
            ["✅ አረጋግጥ እና ላክ"],
            ["✏️ አገልግሎት አይነት ቀይር", "✏️ አገልግሎቶች ቀይር"],
            ["✏️ ስም ቀይር", "✏️ ስልክ ቀይር"],
            ["✏️ አድራሻ ቀይር", "❌ ሰርዝ"]
        ],
        'back_to_menu': [["🏠 ወደ ዋና ገፅ ተመለስ"]],
        'settings_menu': [["🌍 ቋንቋ ቀይር"], ["🏠 ወደ ዋና ገፅ ተመለስ"]]
    }
}

# Text content in both languages
TEXTS = {
    'english': {
        'initial_welcome': (
            "👋 Welcome to Liyu Househelp! 🏠\n\n"
            "Hello {user_name}! We're delighted to have you here.\n\n"
            "🌟 Your Trusted Home Service Partner\n\n"
            "We connect you with professional, verified staff for all your household needs.\n\n"
            "What would you like to do?\n"
            "🚀 Start - Request a service\n"
            "ℹ️ Info - Learn more about us\n"
            "⚙️ Settings - Adjust your preferences\n\n"
            "Choose an option below to continue:"
        ),
        'info_text': (
            "ℹ️ About Liyu Househelp 🏠\n\n"
            "🌟 Who We Are:\n"
            "Liyu Househelp is Ethiopia's premier home services provider. We've been connecting families "
            "with trusted household staff since 2020.\n\n"
            "🛠️ Our Services:\n"
            "• 🧹 Full House Work - Complete household management\n"
            "• 🏠 House Cleaning - Deep cleaning & maintenance\n"
            "• 👕 Laundry Service - Washing, drying & ironing\n"
            "• 🍳 Cooking Service - Meal preparation & cooking\n"
            "• 👶 Child Care - Professional baby sitting\n"
            "• 👵 Elder Care - Senior assistance & companionship\n"
            "💫 Why Choose Us?\n"
            "✅ All staff are background-checked & verified\n"
            "✅ Flexible permanent & temporary options\n"
            "✅ Affordable & transparent pricing\n"
            "✅ 24/7 customer support\n"
            "✅ Satisfaction guaranteed\n\n"
            "📞 Contact Us:\n"
            "Phone: 0966214878\n"
            "Email: info@liyuagency.com\n"
            "Hours: 8:00 AM - 8:00 PM (Daily)\n\n"
            "📍 Location:\n"
            "Addis Ababa, Ethiopia\n\n"
            "Ready to get started? Click 🚀 Start from the main menu!"
        ),
        'settings_text': (
            "⚙️ Settings 🔧\n\n"
            "Customize your experience:\n\n"
            "🌍 Language: {current_language}\n"
            "Change your preferred language for all interactions.\n\n"
            "What would you like to adjust?"
        ),
        'language_changed': (
            "✅ Language Updated!\n\n"
            "Your language has been changed to English.\n"
            "All future messages will be in English.\n\n"
            "Returning to main menu..."
        ),
        'service_type_prompt': (
            "👋 Hello {user_name}! Let's find the perfect service for you! 🏠\n\n"
            "Are you looking for a domestic worker?\n\n"
            "Please choose your service type:\n\n"
            "⏰ Permanent - Regular ongoing service\n"
            "   • Fixed schedule (daily/weekly)\n"
            "   • Consistent staff member\n"
            "   • Monthly payment plan\n"
            "   • Long-term commitment\n\n"
            "🔄 Temporary - One-time or short-term service\n"
            "   • Flexible timing\n"
            "   • On-demand booking\n"
            "   • Pay per service\n"
            "   • No long-term commitment\n\n"
            "Select your preferred option:"
        ),
        'service_type_selected': {
            "⏰ Permanent": "✅ Permanent Service - Regular ongoing service with fixed schedule",
            "🔄 Temporary": "✅ Temporary Service - One-time or short-term flexible service",
            "⏰ ቋሚ": "✅ Permanent Service - Regular ongoing service with fixed schedule",
            "🔄 ጊዜያዊ": "✅ Temporary Service - One-time or short-term flexible service"
        },
        'services_prompt': (
            "{service_description}\n\n"
            "Now, what specific service do you need?\n\n"
            "Choose from our available services:\n\n"
            "• 🧹 Full House Work - Complete home management\n"
            "• 🏠 House Cleaning - Deep cleaning services\n"
            "• 👕 Laundry Service - Washing & ironing\n"
            "• 🍳 Cooking Service - Meal preparation\n"
            "• 👶 Child Care - Baby sitting & care\n"
            "• 👵 Elder Care - Senior assistance\n"
            "Select the service you need:"
        ),
        'service_details': {
            "🧹 Full House Work": "🧹 Full House Work - Complete household maintenance and cleaning",
            "🏠 House Cleaning": "🏠 House Cleaning - Deep cleaning and sanitation services",
            "👕 Laundry Service": "👕 Laundry Service - Washing, drying, and ironing",
            "🍳 Cooking Service": "🍳 Cooking Service - Meal preparation and cooking",
            "👶 Child Care": "👶 Child Care - Child minding and baby sitting",
            "👵 Elder Care": "👵 Elder Care - Senior assistance and care",
            "🧹 ሙሉ የቤት ስራ": "🧹 ሙሉ የቤት ስራ - ሙሉ የቤት ጥገና እና ፍጽምና",
            "🏠 የቤት ፅዳት": "🏠 የቤት ፅዳት - ጥልቅ የፍጽምና እና ማጽጃ አገልግሎቶች",
            "👕 የልብስ እጥበት": "👕 የልብስ እጥበት - ማጠብ፣ ማድረቅ እና ማራት",
            "🍳 ምግብ አብሳይ": "🍳 ምግብ አብሳይ - ምግብ አቀራረብ እና ዝግጅት",
            "👶 የህጻን እንክብካቤ": "👶 የህጻን እንክብካቤ - ህጻናት እንክብካቤ እና ትንክሻ",
            "👵 የአዛውንት እንክብካቤ": "👵 የአዛውንት እንክብካቤ - ለአዛውንት እገዛ እና እንክብካቤ"
        },
        'name_prompt': (
            "{service_details}\n\n"
            "Great choice! Now let's get your contact information.\n\n"
            "We detected your name from Telegram:\n"
            "👤 {detected_name}\n\n"
            "Would you like to use this name?"
        ),
        'name_manual_prompt': (
            "✏️ Please enter your full name:\n\n"
            "We need your name to:\n"
            "• Address you properly\n"
            "• Keep accurate records\n"
            "• Provide personalized service\n\n"
            "Type your full name below:"
        ),
        'name_invalid': (
            "❌ Invalid name entered.\n\n"
            "Please enter a valid full name with at least 2 characters.\n\n"
            "Examples:\n"
            "• Abebe Kebede\n"
            "• Meron Tekle\n"
            "• John Smith\n\n"
            "Try again:"
        ),
        'name_confirmed': (
            "✅ Thank you, {name}!\n\n"
            "Now we need your phone number.\n\n"
            "We'll use this to:\n"
            "• Contact you about your service\n"
            "• Send confirmation details\n"
            "• Provide updates\n\n"
            "How would you like to share your phone number?"
        ),
        'phone_prompt': (
            "📱 Share Your Phone Number\n\n"
            "Click the '📱 Share My Phone Number' button below.\n\n"
            "This is the fastest and most secure way!\n\n"
            "Your number will be automatically shared with us."
        ),
        'phone_manual_prompt': (
            "✏️ Enter Your Phone Number\n\n"
            "Please type your Ethiopian phone number:\n\n"
            "📞 Accepted Formats:\n"
            "• +251912345678\n"
            "• 0912345678\n"
            "• 912345678\n\n"
            "Type your number below:"
        ),
        'phone_invalid': (
            "❌ Invalid phone number.\n\n"
            "Please enter a valid Ethiopian phone number.\n\n"
            "📞 Valid Formats:\n"
            "• +251912345678 (with country code)\n"
            "• 0912345678 (with leading zero)\n"
            "• 912345678 (without leading zero)\n\n"
            "Note: Number must start with 9 and have 9 digits.\n\n"
            "Try again:"
        ),
        'location_prompt': (
            "📍 Share Your Location\n\n"
            "Click the '📍 Share My Location' button below to share your address.\n\n"
            "This helps us:\n"
            "• Assign the nearest staff member\n"
            "• Provide accurate service timing\n"
            "• Plan efficient routes\n\n"
            "Your location is kept secure and only used for service purposes."
        ),
        'location_manual_prompt': (
            "✏️ Enter Your Address\n\n"
            "Please provide your home address or location details:\n\n"
            "📍 Include:\n"
            "• Street name and number\n"
            "• Neighborhood/Area\n"
            "• City/District\n"
            "• Any landmarks or directions\n\n"
            "Example: Bole, Addis Ababa - Near Bole Medhanealem Church\n\n"
            "Type your address below:"
        ),
        'location_invalid': (
            "❌ Invalid address entered.\n\n"
            "Please provide a more detailed address with at least 5 characters.\n\n"
            "Include:\n"
            "• Street/Area name\n"
            "• Neighborhood\n"
            "• City/District\n\n"
            "Try again:"
        ),
        'location_confirmed': (
            "✅ Location Saved!\n\n"
            "📍 Your Address: {location}\n\n"
            "We'll use this to assign the best staff member for your area.\n\n"
            "Let's review your complete request..."
        ),
        'confirmation_summary': (
            "📋 Review Your Service Request\n\n"
            "Please verify all information is correct:\n\n"
            "👤 Name: {name}\n"
            "📞 Phone: {phone} {phone_status}\n"
            "📍 Location: {location}\n"
            "⚡ Service Type: {service_type}\n"
            "🛠️ Service: {services}\n\n"
            "What would you like to do?\n\n"
            "✅ Confirm - Submit your request\n"
            "✏️ Edit - Change any information\n"
            "❌ Cancel - Start over\n\n"
            "Choose an option below:"
        ),
        'success_message': (
            "🎉 Success! Request Submitted! 🎉\n\n"
            "Thank you, {name}!\n\n"
            "✅ Your service request has been received and is being processed.\n\n"
            "📋 Request Summary:\n"
            "• Service Type: {service_type}\n"
            "• Service: {services}\n"
            "• Contact: {phone}\n"
            "• Location: {location}\n\n"
            "⏰ What Happens Next?\n\n"
            "Our team will review your request and We'll call you within 24 hours\n"
            "📞 Need Immediate Help?\n"
            "Call us: 0966214878\n"
            "💬 Questions?\n"
            "Use /help anytime for assistance.\n\n"
            "Thank you for choosing Liyu Househelp! 🌟\n"
            "We look forward to serving you!"
        ),
        'cancelled': (
            "❌ Request Cancelled\n\n"
            "Your service request has been cancelled.\n"
            "No information has been saved.\n\n"
            "Want to try again?\n"
            "• Use /start to begin a new request\n"
            "• Use /help for assistance\n\n"
            "Thank you for considering Liyu Househelp! 🏠\n"
            "We're here whenever you need us."
        ),
        'help': (
            "🤖 Liyu Househelp Bot - Help Guide 📖\n\n"
            "Available Commands:\n"
            "• /start - Open main menu\n"
            "• /help - Show this help message\n"
            "• /cancel - Cancel current operation\n\n"
            "🏠 Main Menu Options:\n\n"
            "🚀 Start - Request a Service\n"
            "Begin the process to request household staff.\n\n"
            "ℹ️ Info - About Us\n"
            "Learn about Liyu Househelp and our services.\n\n"
            "⚙️ Settings - Preferences\n"
            "Change language and other settings.\n\n"
            "🛠️ Our Services:\n"
            "• 🧹 Full House Work\n"
            "• 🏠 House Cleaning\n"
            "• 👕 Laundry Service\n"
            "• 🍳 Cooking Service\n"
            "• 👶 Child Care\n"
            "• 👵 Elder Care\n"
            "📋 Service Types:\n"
            "• Permanent - Regular ongoing service\n"
            "• Temporary - One-time or short-term\n\n"
            "📞 Contact Support:\n"
            "Phone: 0966214878\n"
            "Email: info@liyuagency.com\n"
            "Hours: 8:00 AM - 8:00 PM\n\n"
            "Liyu Househelp - Your Trusted Home Service Partner 🌟"
        )
    },
    'amharic': {
        'initial_welcome': (
            "👋 ወደ ልዩ አጋዥ እንኳን በደህና መጡ! 🏠\n\n"
            "ሰላም {user_name}! \n"
            "ለሁሉም የቤት ውስጥ ፍላጎቶ የሰለጠኑ እና የተረጋገጠ መረጃ ካላቸው አጋዦች ጋር እናገናኝዎታለን።\n\n"
            "ምን ማድረግ ይፈልጋሉ?\n"
            "🚀 ጀምር - አገልግሎት ይጠይቁ\n"
            "ℹ️ መረጃ - ስለ እኛ ይወቁ\n"
            "⚙️ ማስተካከያ - ምርጫዎችን ያስተካክሉ\n\n"
            "ለመቀጠል ከዚህ በታች አንድ አማራጭ ይምረጡ:"
        ),
        'info_text': (
            "እኛ ማን ነን:\n"
            "ልዩ አጋዥ የኢትዮጵያ ቀዳሚ የቤት አገልግሎት አቅራቢ ነው። ቤተሰቦችን ከታመኑ የቤት አጋዦች ጋር እናገናኛለን።\n\n"
            "🛠️አገልግሎቶቻችን:\n\n"
            "• 🧹ሙሉ የቤት ስራ\n"
            "• 🏠የቤት ፅዳት\n"
            "• 👕የልብስ እጥበት\n"
            "• 🍳የምግብ አብሳይ\n"
            "• 👶ህጻናት እንክብካቤ\n"
            "• 👵የአዛውንት እንክብካቤ\n\n"
            "💫ለምን እኛን መምረጥ?\n\n"
            "✅ ሁሉም አጋዦች የተፈተኑ እና የተረጋገጡ ናቸው\n"
            "✅ ተለዋዋጭ ቋሚ እና ጊዜያዊ አማራጮች\n"
            "✅ ተመጣጣኝ እና ግልጽ ዋጋ\n"
            "✅ 24/7 የደንበኛ ድጋፍ\n\n"
            "📞 ያግኙን:\n"
            "ስልክ: 0966214878\n"
            "ኢሜይል: info@liyuagency.com\n"
            "ሰዓታት: ከጠዋት 8:00 እስከ ማታ 8:00 (በየቀኑ)\n\n"
            "📍አድራሻ:\n"
            "አዲስ አበባ፣ ኢትዮጵያ\n\n"
            "ለመጀመር ዝግጁ ነዎት? ከዋና ገፅ 🚀ጀምር ን ይጫኑ!"
        ),
        'settings_text': (
            "⚙️ማስተካከያ\n\n"
            "ቋንቋ ይቀይሩ።\n\n"
        ),
        'language_changed': (
            "✅ ቋንቋ ተቀይሯል!\n\n"
            "ቋንቋዎ ወደ አማርኛ ተቀይሯል።\n"
            "ወደ ዋና ገፅ በመመለስ ላይ..."
        ),
        'service_type_prompt': (
            "እባክዎ የሚፈልጉትን የአገልግሎት አይነትዎን ይምረጡ:\n\n"
        ),
        'service_type_selected': {
            "⏰ Permanent": "✅ ቋሚ አገልግሎት",
            "🔄 Temporary": "✅ ጊዜያዊ አገልግሎት",
            "⏰ ቋሚ": "✅ ቋሚ አገልግሎት",
            "🔄 ጊዜያዊ": "✅ ጊዜያዊ አገልግሎት"
        },
        'services_prompt': (
            "የሚፈልጉትን አገልግሎት ይምረጡ:"
        ),
        'service_details': {
            "🧹 Full House Work": "🧹 ሙሉ የቤት ስራ",
            "🏠 House Cleaning": "🏠 የቤት ፅዳት ",
            "👕 Laundry Service": "👕 የልብስ እጥበት",
            "🍳 Cooking Service": "🍳 ምግብ አብሳይ",
            "👶 Child Care": "👶 ህጻናት እንክብካቤ",
            "👵 Elder Care": "👵 የአዛውንት እንክብካቤ",
            "🧹 ሙሉ የቤት ስራ": "🧹 ሙሉ የቤት ስራ",
            "🏠 የቤት ፅዳት": "🏠 የቤት ፅዳት ",
            "👕 የልብስ እጥበት": "👕 የልብስ እጥበት",
            "🍳 ምግብ አብሳይ": "🍳 ምግብ አብሳይ",
            "👶 የህጻን እንክብካቤ": "👶 ህጻናት እንክብካቤ",
            "👵 የአዛውንት እንክብካቤ": "👵 የአዛውንት እንክብካቤ"
        },
        'name_prompt': (
            "{service_details}\n\n"
            "በጣም ጥሩ ምርጫ! አሁን የእርስዎን መረጃ እናግኝ።\n\n"
            "ከቴሌግራም ስምዎን አገኘን:\n"
            "👤 {detected_name}\n\n"
            "ይህን ስም መጠቀም ይፈልጋሉ?"

        ),
        'name_manual_prompt': (
            "✏️ እባክዎ ሙሉ ስምዎን ያስገቡ:\n\n"
            "ስምዎ የሚያስፈልገን:\n"
            "• ትክክለኛ መዝገቦችን ለመያዝ\n"
            "• ግላዊ አገልግሎት ለመስጠት\n\n"
            "ሙሉ ስምዎን ከዚህ በታች ይፃፉ:"
        ),
        'name_invalid': (
            "❌ ልክ ያልሆነ ስም ገብቷል።\n\n"
            "እባክዎ ቢያንስ 2 ፊደሎች ያለው ትክክለኛ ሙሉ ስም ያስገቡ።\n\n"
            "ምሳሌዎች:\n"
            "• አበበ ከበደ\n"
            "• መሮን ተክሌ\n"
            "• ጆን ስሚዝ\n\n"
            "እንደገና ይሞክሩ:"
        ),
        'name_confirmed': (
            "✅ እናመሰግናለን {name}!\n\n"
            "አሁን የስልክ ቁጥርዎ ያስፈልገናል።\n\n"
            "ይህን እንጠቀማለን:\n"
            "የስልክ ቁጥርዎን እንዴት ማጋራት ይፈልጋሉ?"
        ),
        'phone_prompt': (
            "📱 የስልክ ቁጥርዎን ያጋሩ\n\n"
            "ከዚህ በታች ያለውን 'ስልክ ቁጥሬን አጋራ' ቁልፍ ይጫኑ።\n\n"
            "ይህ በጣም ፈጣን እና ደህንነቱ የተጠበቀ መንገድ ነው!\n\n"
        ),
        'phone_manual_prompt': (
            "📞 የስልክ ቁጥርዎን ያስገቡ\n\n"
            "እባክዎ የኢትዮጵያ ስልክ ቁጥርዎን ይፃፉ:\n\n"
            " የተቀበሉ ቅጾች:\n"
            "• +251912345678\n"
            "• 0912345678\n"
            "• 912345678\n\n"
            "ቁጥርዎን ከዚህ በታች ይፃፉ:"
        ),
        'phone_invalid': (
            "❌ ልክ ያልሆነ ስልክ ቁጥር።\n\n"
            "እባክዎ ትክክለኛ የኢትዮጵያ ስልክ ቁጥር ያስገቡ።\n\n"
            "📞 ትክክለኛ ቅጾች:\n"
            "• +251912345678 (ከአገር ኮድ ጋር)\n"
            "• 0912345678 (ከመሪ ዜሮ ጋር)\n"
            "• 912345678 (ያለ መሪ ዜሮ)\n\n"
            "ማስታወሻ: ቁጥር በ9 መጀመር እና 9 አሃዞች ሊኖረው ይገባል።\n\n"
            "እንደገና ይሞክሩ:"
        ),
        'location_prompt': (
            "📍 አድራሻዎን ያጋሩ\n\n"
            "ከዚህ በታች ያለውን '📍 አድራሻ አጋራ' ቁልፍ ይጫኑ።\n\n"
            "ይህ ይረዳናል:\n"
            "• ለእርስዎ ቅርብ አጋዥ ለመመደብ\n"
            "• ትክክለኛ የአገልግሎት ጊዜ ለመስጠት\n"
            "• ቅልጥፍና ለመጠበቅ\n\n"
            "አድራሻዎ ደህንነቱ የተጠበቀ ነው እና ለአገልግሎት ዓላማ ብቻ ጥቅም ላይ ይውላል።"
        ),
        'location_manual_prompt': (
            "አድራሻዎን ያስገቡ\n\n"
            "እባክዎ የቤትዎን አድራሻ ወይም አድራሻ ይስጡ:\n\n"
            "• የመንገድ ስም እና ቁጥር\n"
            "• ሰፈር/አካባቢ\n"
            "• ከተማ/ወረዳ\n"
            "• ምልክቶች ወይም አቅጣጫዎች\n\n"
            "ምሳሌ: ቦሌ፣ አዲስ አበባ - ቦሌ መድሃኔዓለም ቤተ ክርስቲያን አጠገብ\n\n"
            "አድራሻዎን ከዚህ በታች ይፃፉ:"
        ),
        'location_invalid': (
            "❌ ልክ ያልሆነ አድራሻ ገብቷል።\n\n"
            "እባክዎ ቢያንስ 5 ፊደሎች ያለው ዝርዝር አድራሻ ይስጡ።\n\n"
            "ያካትቱ:\n"
            "• መንገድ/አካባቢ ስም\n"
            "• ሰፈር\n"
            "• ከተማ/ወረዳ\n\n"
            "እንደገና ይሞክሩ:"
        ),
        'location_confirmed': (
            "✅ አድራሻ ተቀምጧል!\n\n"
            "📍 አድራሻዎ: {location}\n\n"
            "ለእርስዎ አካባቢ ምርጥ አጋዥ ለመመደብ ይህን እንጠቀማለን።\n\n"
            "ሙሉ ጥያቄዎን እናረጋግጥ..."
        ),
        'confirmation_summary': (
            "📋 እባክዎ ሁሉም መረጃ ትክክል መሆኑን ያረጋግጡ:\n\n"
            "👤 ስም: {name}\n"
            "📞 ስልክ: {phone} {phone_status}\n"
            "📍 አድራሻ: {location}\n"
            "⚡ የአገልግሎት አይነት: {service_type}\n"
            "🛠️ አገልግሎት: {services}\n\n"
            "\n\n"
            "✅ አረጋግጥ - ሁሉም መረጃ ትክክል ነው\n"
            "✏️ አስተካክል - ማንኛውንም መረጃ ይቀይሩ\n"
            "❌ ሰርዝ - እንደገና ይጀምሩ\n\n"
            "ከዚህ በታች አንድ አማራጭ ይምረጡ:"
        ),
        'success_message': (
            "እናመሰግናለን {name}! 🎉!\n\n"
            "✅ የአገልግሎት ጥያቄዎ በሂደት ላይ ነው።\n\n"
            "• የአገልግሎት አይነት: {service_type}\n"
            "• አገልግሎት: {services}\n"
            "• ስልክ: {phone}\n"
            "• አድራሻ: {location}\n\n"
            "ቡድናችን ጥያቄዎን አይቶ በ24 ሰዓታት ውስጥ እንደውልዎታለን!\n"
            "📞 አፋጣኝ እገዛ ይፈልጋሉ?\n"
            "ይደውሉልን: 0966214878\n"
            "💬 ለጥያቄዎች?\n"
            "በማንኛውም ጊዜ /help ይጠቀሙ።\n\n"
            "ልዩ አጋዥን ስለመረጡ እናመሰግናለን! 🌟\n"
        ),
        'cancelled': (
            "❌ የአገልግሎት ጥያቄዎ ተሰርዟል።\n"
            "ምንም መረጃ አልተቀመጠም።\n\n"
            "እንደገና መሞከር ይፈልጋሉ?\n"
            "• አዲስ ጥያቄ ለመጀመር /start ይጠቀሙ\n"
            "• ለእገዛ /help ይጠቀሙ\n\n"
        ),
        'help': (
            "🤖 የልዩ አጋዥ ቦት - የእገዛ መመሪያ 📖\n\n"
            "• /start - ዋና ገፅ ክፈት\n"
            "• /help - የእገዛ ገፅ ክፈት\n"
            "• /cancel - ውጣ\n\n"
            "🏠 የዋና ገፅ አማራጮች:\n\n"
            "🚀 ጀምር - አገልግሎት ጠይቅ\n"
            "ℹ️ መረጃ - ስለ ልዩ አጋዥ እና አገልግሎቶቻችን ይወቁ\n"
            "⚙️ ማስተካከያ - ቋንቋ ይቀይሩ።\n"
            "📞 ድጋፍ ያግኙ:\n"
            "ስልክ: 0966214878\n"
            "ኢሜይል: info@liyuagency.com\n"
        )
    }
}

# Database initialization
DATABASE_FILE = 'liyu_agency.db'

def init_database():
    """Initialize SQLite database with required tables."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create service_requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                location TEXT,
                service_type TEXT NOT NULL,
                services TEXT NOT NULL,
                phone_source TEXT,
                location_source TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")

def save_user_to_db(telegram_id, username, first_name, last_name):
    """Save or update user in database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (telegram_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ User {telegram_id} saved to database")
    except Exception as e:
        logger.error(f"❌ Error saving user: {e}")

def save_service_request_to_db(telegram_id, name, phone, location, service_type, services, phone_source, location_source):
    """Save service request to database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get user_id from telegram_id
        cursor.execute('SELECT user_id FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        user_id = result[0] if result else None
        
        # Insert service request
        cursor.execute('''
            INSERT INTO service_requests 
            (user_id, name, phone, location, service_type, services, phone_source, location_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, phone, location, service_type, services, phone_source, location_source))
        
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Service request #{request_id} saved to database")
        return request_id
    except Exception as e:
        logger.error(f"❌ Error saving service request: {e}")
        return None

def get_user_language(context):
    """Get user's selected language."""
    return context.user_data.get('language', 'amharic')

def get_text(context, text_key, kwargs):
    """Get text in user's selected language."""
    language = get_user_language(context)
    text = TEXTS[language].get(text_key, '')
    if isinstance(text, dict):
        # For nested dictionaries like service_details
        key = kwargs.get('key', '')
        return text.get(key, '')
    if kwargs:
        return text.format(**kwargs)  # ← FIXED: added ** to unpack dict
    return text

def get_menu(context, menu_key):
    """Get menu in user's selected language."""
    language = get_user_language(context)
    return MENU_TEXT[language].get(menu_key, [])

def get_main_menu(context):
    """Get main menu in user's selected language."""
    language = get_user_language(context)
    return MAIN_MENU_OPTIONS[language]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the conversation with main menu."""
    context.user_data.clear()

    user = update.message.from_user
    
    if 'language' not in context.user_data:
        context.user_data['language'] = 'amharic'
    
    # Store user info from Telegram
    context.user_data['user_info'] = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'user_id': user.id
    }
    
    # Auto-detect name from Telegram profile
    detected_name = user.first_name
    if user.last_name:
        detected_name += f" {user.last_name}"
    
    context.user_data['detected_name'] = detected_name
    
    # Add logo and phone number to the welcome message
    welcome_text = get_text(context, 'initial_welcome', {'user_name': user.first_name})
    
    welcome_with_contact = (
        f"{welcome_text}"
    )
    
    await update.message.reply_text(
        welcome_with_contact,
        reply_markup=ReplyKeyboardMarkup(
            get_main_menu(context),
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selections."""
    choice = update.message.text
    language = get_user_language(context)
    
    # Check for Start button
    if choice in ["🚀 Start", "🚀 ጀምር", "/start"]:
        user = update.message.from_user
        await update.message.reply_text(
            get_text(context, 'service_type_prompt', {'user_name': user.first_name}),
            reply_markup=ReplyKeyboardMarkup(
                get_menu(context, 'service_type_menu'),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return SERVICE_TYPE
    
    # Check for Info button
    elif choice in ["ℹ️ Info", "ℹ️ መረጃ"]:
        await update.message.reply_text(
            get_text(context, 'info_text', {}),
            reply_markup=ReplyKeyboardMarkup(
                get_menu(context, 'back_to_menu'),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return INFO
    
    # Check for Settings button
    elif choice in ["⚙️ Settings", "⚙️ ማስተካከያ"]:
        current_lang = "English" if language == 'english' else "አማርኛ (Amharic)"
        await update.message.reply_text(
            get_text(context, 'settings_text', {'current_language':current_lang}),
            reply_markup=ReplyKeyboardMarkup(
                get_menu(context, 'settings_menu'),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return SETTINGS
    
    # Default: show main menu again
    else:
        await update.message.reply_text(
            "Please select an option from the menu:" if language == 'english' else "እባክዎ ከገፅ አንድ አማራጭ ይምረጡ:",
            reply_markup=ReplyKeyboardMarkup(
                get_main_menu(context),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return MAIN_MENU

async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle info section navigation."""
    choice = update.message.text
    
    if choice in ["🏠 Back to Main Menu", "🏠 ወደ ዋና ገፅ ተመለስ"]:
        user = update.message.from_user
        await update.message.reply_text(
            get_text(context, 'initial_welcome', {'user_name': user.first_name}),
            reply_markup=ReplyKeyboardMarkup(
                get_main_menu(context),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return MAIN_MENU
    
    return INFO

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings section."""
    choice = update.message.text
    
    if choice in ["🌍 Change Language", "🌍 ቋንቋ ቀይር"]:
        await update.message.reply_text(
            "🌍 Select Your Language / ቋንቋዎን ይምረጡ:\n\n"
            "Choose your preferred language for all interactions:",
            reply_markup=ReplyKeyboardMarkup(
                LANGUAGE_MENU,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return LANGUAGE
    
    elif choice in ["🏠 Back to Main Menu", "🏠 ወደ ዋና ገፅ ተመለስ"]:
        user_info = context.user_data.get('user_info', {})
        user_name = user_info.get('first_name', 'there')
        await update.message.reply_text(
            get_text(context, 'initial_welcome', {'user_name':user_name}),
            reply_markup=ReplyKeyboardMarkup(
                get_main_menu(context),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return MAIN_MENU
    
    return SETTINGS

async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection from settings."""
    choice = update.message.text
    
    if choice == "🇬🇧 English":
        context.user_data['language'] = 'english'
        language_name = "English"
    elif choice == "🇪🇹 Amharic":
        context.user_data['language'] = 'amharic'
        language_name = "አማርኛ (Amharic)"
    else:
        # Default fallback
        context.user_data['language'] = 'amharic'
        language_name = "አማርኛ (Amharic)"
    
    # Send language change confirmation
    if context.user_data['language'] == 'english':
        await update.message.reply_text(
            f"✅ Language Updated!\n\n"
            f"Your language has been changed to {language_name}.\n"
            f"All future messages will be in English.\n\n"
            f"Returning to main menu..."
        )
    else:
        await update.message.reply_text(
            f"✅ ቋንቋ ተቀይሯል!\n\n"
            f"ቋንቋዎ ወደ {language_name} ተቀይሯል።\n"
            f"ወደ ዋና ገፅ በመመለስ ላይ..."
        )
    
    # Return to main menu
    user_info = context.user_data.get('user_info', {})
    user_name = user_info.get('first_name', 'there')
    await update.message.reply_text(
        get_text(context, 'initial_welcome', {'user_name':user_name}),
        reply_markup=ReplyKeyboardMarkup(
            get_main_menu(context),
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return MAIN_MENU

async def service_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store service type and show services menu."""
    service_type = update.message.text
    context.user_data['service_type'] = service_type
    
    if context.user_data.get('editing_from_confirmation', False):
        context.user_data['editing_from_confirmation'] = False
        return await show_confirmation(update, context)
    
    service_description = get_text(context, 'service_type_selected', {'key':service_type})
    
    await update.message.reply_text(
        get_text(context, 'services_prompt', {'service_description':service_description}),
        reply_markup=ReplyKeyboardMarkup(
            create_service_selection_menu(context),
            one_time_keyboard=False,
            resize_keyboard=True
        )
    )
    return SERVICES

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store services with multiple selection support."""
    choice = update.message.text
    language = get_user_language(context)
    
    # Remove the checkmark prefix if it exists
    if choice.startswith("✓ "):
        choice = choice[2:]  # Remove "✓ " prefix
    
    # Initialize selected_services list if not exists
    if 'selected_services' not in context.user_data:
        context.user_data['selected_services'] = []
    
    # Get the service menu options
    service_menu = get_menu(context, 'main_services_menu')
    all_services = []
    for row in service_menu:
        all_services.extend(row)
    
    if choice in ["✅ Done Selecting", "✅ ምርጫ ጨርሻለሁ"]:
        if not context.user_data['selected_services']:
            await update.message.reply_text(
                "⚠️ Please select at least one service!" if language == 'english' else "⚠️ እባክዎ ቢያንስ አንድ አገልግሎት ይምረጡ!",
                reply_markup=ReplyKeyboardMarkup(
                    create_service_selection_menu(context),
                    one_time_keyboard=False,
                    resize_keyboard=True
                )
            )
            return SERVICES
        
        # Store services as comma-separated string for display
        context.user_data['services'] = ', '.join(context.user_data['selected_services'])
        
        if context.user_data.get('editing_from_confirmation', False):
            context.user_data['editing_from_confirmation'] = False
            return await show_confirmation(update, context)
        
        if 'saved_contact_info' in context.user_data:
            saved_info = context.user_data['saved_contact_info']
            saved_name = saved_info.get('name', 'Not found')
            saved_phone = saved_info.get('phone', 'Not found')
            
            contact_check_menu = [
                ["✅ Use Saved Info" if language == 'english' else "✅ የተቀመጠውን መረጃ ተጠቀም"],
                ["✏️ Update Info" if language == 'english' else "✏️ መረጃ አዘምን"]
            ]
            
            await update.message.reply_text(
                f"👤 {'We have your contact information on file' if language == 'english' else 'የእርስዎን የመገኛ መረጃ አለን'}:\n\n"
                f"📝 {'Name' if language == 'english' else 'ስም'}: {saved_name}\n"
                f"📞 {'Phone' if language == 'english' else 'ስልክ'}: {saved_phone}\n\n"
                f"{'Would you like to use this information or update it?' if language == 'english' else 'ይህን መረጃ መጠቀም ወይም ማዘመን ይፈልጋሉ?'}",
                reply_markup=ReplyKeyboardMarkup(
                    contact_check_menu,
                    one_time_keyboard=True,
                    resize_keyboard=True
                )
            )
            return CONTACT_CHECK
        
        # Continue to name confirmation for new users
        detected_name = context.user_data.get('detected_name', '')
        service_details = context.user_data['services']
        
        await update.message.reply_text(
            get_text(context, 'name_prompt', {
                'service_details': service_details,
                'detected_name': detected_name
            }),
            reply_markup=ReplyKeyboardMarkup(
                get_menu(context, 'name_confirm_menu'),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return NAME_CONFIRM
    
    elif choice in ["📝 Other (Specify)", "📝 ሌላ (ይግለጹ)"]:
        await update.message.reply_text(
            "✏️ Please describe the service you need:" if language == 'english' else "✏️ የሚፈልጉትን አገልግሎት ይግለጹ:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SERVICES_OTHER
    
    elif choice in all_services:
        full_house_work = "🧹 Full House Work" if language == 'english' else "🧹 ሙሉ የቤት ስራ"
        
        # If "Full House Work" is selected, clear all other selections
        if choice == full_house_work:
            context.user_data['selected_services'] = [choice]
            await update.message.reply_text(
                f"✅ {choice}\n\n"
                f"{'Note: Full House Work includes all services, so other selections have been cleared.' if language == 'english' else 'ማስታወሻ: ሙሉ የቤት ስራ ሁሉንም አገልግሎቶች ያካትታል፣ ስለዚህ ሌሎች ምርጫዎች ተሰርዘዋል።'}\n\n"
                f"{'Click ✅ Done Selecting when ready.' if language == 'english' else '✅ ምርጫ ጨርሻለሁ ን ይጫኑ።'}",
                reply_markup=ReplyKeyboardMarkup(
                    create_service_selection_menu(context),
                    one_time_keyboard=False,
                    resize_keyboard=True
                )
            )
        else:
            # Remove "Full House Work" if user selects other services
            if full_house_work in context.user_data['selected_services']:
                context.user_data['selected_services'].remove(full_house_work)
            
            # Toggle selection
            if choice in context.user_data['selected_services']:
                context.user_data['selected_services'].remove(choice)
                status = "❌ Removed" if language == 'english' else "❌ ተወግዷል"
            else:
                context.user_data['selected_services'].append(choice)
                status = "✅ Added" if language == 'english' else "✅ ታክሏል"
            
            # Show current selections
            selected_count = len(context.user_data['selected_services'])
            selected_text = "\n".join([f"  • {s}" for s in context.user_data['selected_services']])
            
            await update.message.reply_text(
                f"{status}: {choice}\n\n"
                f"{'Selected Services' if language == 'english' else 'የተመረጡ አገልግሎቶች'} ({selected_count}):\n{selected_text if selected_text else ('  None' if language == 'english' else '  ምንም')}\n\n"
                f"{'Select more services or click ✅ Done Selecting.' if language == 'english' else 'ተጨማሪ አገልግሎቶችን ይምረጡ ወይም ✅ ምርጫ ጨርሻለሁ ን ይጫኑ።'}",
                reply_markup=ReplyKeyboardMarkup(
                    create_service_selection_menu(context),
                    one_time_keyboard=False,
                    resize_keyboard=True
                )
            )
        
        return SERVICES
    
    return SERVICES

def create_service_selection_menu(context):
    """Create service selection menu with checkmarks for selected items."""
    language = get_user_language(context)
    selected = context.user_data.get('selected_services', [])
    
    # Base services
    if language == 'english':
        services = [
            ["🧹 Full House Work", "🏠 House Cleaning"],
            ["👕 Laundry Service", "🍳 Cooking Service"],
            ["👶 Child Care", "👵 Elder Care"],
            ["🐕 Pet Care", "🌿 Gardening"],
            ["📝 Other (Specify)"],
            ["✅ Done Selecting"]
        ]
    else:
        services = [
            ["🧹 ሙሉ የቤት ስራ", "🏠 የቤት ፅዳት"],
            ["👕 የልብስ እጥበት", "🍳 ምግብ አብሳይ"],
            ["👶 የህጻን እንክብካቤ", "👵 የአዛውንት እንክብካቤ"],
            ["🐕 የቤት እንስሳት", "🌿 የአትክልት ስራ"],
            ["📝 ሌላ (ይግለጹ)"],
            ["✅ ምርጫ ጨርሻለሁ"]
        ]
    
    # Add checkmarks to selected items
    for i, row in enumerate(services[:-2]):  # Exclude "Other" and "Done" rows
        for j, service in enumerate(row):
            if service in selected:
                services[i][j] = f"✓ {service}"
    
    return services

async def services_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom 'Other' service input."""
    other_service = update.message.text.strip()
    language = get_user_language(context)
    
    if len(other_service) < 3:
        await update.message.reply_text(
            "❌ Please provide a more detailed description (at least 3 characters)." if language == 'english' else "❌ እባክዎ የበለጠ ዝርዝር መግለጫ ይስጡ (ቢያንስ 3 ፊደሎች)።"
        )
        return SERVICES_OTHER
    
    # Add "Other" service to selections
    other_label = f"📝 Other: {other_service}"
    if 'selected_services' not in context.user_data:
        context.user_data['selected_services'] = []
    
    context.user_data['selected_services'].append(other_label)
    
    await update.message.reply_text(
        f"✅ {'Added custom service' if language == 'english' else 'ብጁ አገልግሎት ታክሏል'}: {other_service}\n\n"
        f"{'You can select more services or click ✅ Done Selecting.' if language == 'english' else 'ተጨማሪ አገልግሎቶችን መምረጥ ወይም ✅ ምርጫ ጨርሻለሁ ን መጫን ይችላሉ።'}",
        reply_markup=ReplyKeyboardMarkup(
            create_service_selection_menu(context),
            one_time_keyboard=False,
            resize_keyboard=True
        )
    )
    
    return SERVICES

async def contact_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle returning user contact info choice."""
    choice = update.message.text
    language = get_user_language(context)
    
    if choice in ["✅ Use Saved Info", "✅ የተቀመጠውን መረጃ ተጠቀም"]:
        # Load saved contact info
        saved_info = context.user_data['saved_contact_info']
        context.user_data['name'] = saved_info['name']
        context.user_data['phone'] = saved_info['phone']
        context.user_data['location'] = saved_info.get('location', 'Not provided')
        context.user_data['phone_source'] = saved_info.get('phone_source', 'manual_entry')
        
        # Go directly to confirmation
        return await show_confirmation(update, context)
    
    elif choice in ["✏️ Update Info", "✏️ መረጃ አዘምን"]:
        # Continue to name confirmation to update info
        detected_name = context.user_data.get('detected_name', '')
        service_details = context.user_data['services']
        
        await update.message.reply_text(
            get_text(context, 'name_prompt', {
                'service_details': service_details,
                'detected_name': detected_name
            }),
            reply_markup=ReplyKeyboardMarkup(
                get_menu(context, 'name_confirm_menu'),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return NAME_CONFIRM
    
    return CONTACT_CHECK

async def name_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name confirmation with menu."""
    choice = update.message.text
    detected_name = context.user_data.get('detected_name', '')
    
    name_confirm_menu = get_menu(context, 'name_confirm_menu')
    
    if choice == name_confirm_menu[0][0]:  # "Use My Telegram Name" equivalent
        context.user_data['name'] = detected_name
        
        if context.user_data.get('editing_from_confirmation', False):
            context.user_data['editing_from_confirmation'] = False
            return await show_confirmation(update, context)
        
        # Create phone sharing keyboard
        phone_keyboard = [
            [KeyboardButton("📱 Share My Phone Number" if get_user_language(context) == 'english' else "📱 ስልክ ቁጥሬን አጋራ", request_contact=True)],
            ["✏️ Enter Phone Manually" if get_user_language(context) == 'english' else "✏️ ስልክ ቁጥር አስገባ"]
        ]
        
        await update.message.reply_text(
            get_text(context, 'name_confirmed', {'name':detected_name}),
            reply_markup=ReplyKeyboardMarkup(
                phone_keyboard,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return PHONE
    
    elif choice == name_confirm_menu[0][1]:  # "Enter Different Name" equivalent
        await update.message.reply_text(
            get_text(context, 'name_manual_prompt'),
            reply_markup=ReplyKeyboardRemove()
        )
        return NAME_CONFIRM
    
    else:
        # User typed a name manually
        name = update.message.text.strip()
        if len(name) < 2:
            await update.message.reply_text(
                get_text(context, 'name_invalid'),
                reply_markup=ReplyKeyboardMarkup(
                    get_menu(context, 'name_confirm_menu'),
                    one_time_keyboard=True,
                    resize_keyboard=True
                )
            )
            return NAME_CONFIRM
        
        context.user_data['name'] = name
        
        if context.user_data.get('editing_from_confirmation', False):
            context.user_data['editing_from_confirmation'] = False
            return await show_confirmation(update, context)
        
        # Create phone sharing keyboard
        phone_keyboard = [
            [KeyboardButton("📱 Share My Phone Number" if get_user_language(context) == 'english' else "📱 ስልክ ቁጥሬን አጋራ", request_contact=True)],
            ["✏️ Enter Phone Manually" if get_user_language(context) == 'english' else "✏️ ስልክ ቁጥር አስገባ"]
        ]
        
        await update.message.reply_text(
            get_text(context, 'name_confirmed', {'name':name}),
            reply_markup=ReplyKeyboardMarkup(
                phone_keyboard,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number collection with contact sharing."""
    if update.message.contact:
        # User shared contact - this is the preferred method
        phone_number = update.message.contact.phone_number
        context.user_data['phone'] = phone_number
        context.user_data['phone_source'] = 'contact_shared'
        
        return await ask_for_location(update, context)
    
    choice = update.message.text
    
    if choice in ["📱 Share My Phone Number", "📱 ስልክ ቁጥሬን አጋራ"]:
        await update.message.reply_text(
            get_text(context, 'phone_prompt', {})
        )
        return PHONE
    
    elif choice in ["✏️ Enter Phone Manually", "✏️ ስልክ ቁጥር አስገባ"]:
        await update.message.reply_text(
            get_text(context, 'phone_manual_prompt'),
            reply_markup=ReplyKeyboardRemove()
        )
        return PHONE
    
    else:
        # User entered phone number manually
        phone_input = update.message.text.strip()
        cleaned_phone = re.sub(r'[^\d+]', '', phone_input)
        
        # Ethiopian phone number validation
        ethiopian_pattern = r'^(\+251|251|0)?9\d{8}$'
        
        if not re.match(ethiopian_pattern, cleaned_phone):
            await update.message.reply_text(
                get_text(context, 'phone_invalid', {})
            )
            return PHONE
        
        # Format phone number consistently
        if cleaned_phone.startswith('0'):
            phone_number = '+251' + cleaned_phone[1:]
        elif cleaned_phone.startswith('251'):
            phone_number = '+' + cleaned_phone
        elif cleaned_phone.startswith('9'):
            phone_number = '+251' + cleaned_phone
        else:
            phone_number = cleaned_phone
        
        context.user_data['phone'] = phone_number
        context.user_data['phone_source'] = 'manual_entry'
        
        return await ask_for_location(update, context)

async def ask_for_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user for their phone."""
    language = get_user_language(context)
    
    # Create phone sharing keyboard
    phone_keyboard = [
        [KeyboardButton("📍 Share My Phone" if language == 'english' else "📍 ስልክ ቁጥር አጋራ", request_phone=True)],
        ["✏️ Enter Phone Manually" if language == 'english' else "✏️ ስልክ ቁጥር አስገባ"]
    ]
    
    await update.message.reply_text(
        get_text(context, 'phone_manual_prompt', {}),
        reply_markup=ReplyKeyboardMarkup(
            phone_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return PHONE

async def ask_for_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user for their location."""
    language = get_user_language(context)
    
    # Create location sharing keyboard
    location_keyboard = [
        [KeyboardButton("📍 Share My Location" if language == 'english' else "📍 አድራሻ አጋራ", request_location=True)],
        ["✏️ Enter Address Manually" if language == 'english' else "✏️ አድራሻ አስገባ"]
    ]
    
    await update.message.reply_text(
        get_text(context, 'location_prompt', {}),
        reply_markup=ReplyKeyboardMarkup(
            location_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location collection."""
    language = get_user_language(context)
    
    if update.message.location:
        # User shared location via GPS
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        location_text = f"📍 GPS: {lat}, {lon}"
        context.user_data['location'] = location_text
        context.user_data['location_source'] = 'gps'
        
        await update.message.reply_text(
            get_text(context, 'location_confirmed', {'location':location_text})
        )
        return await show_confirmation(update, context)
    
    choice = update.message.text
    
    if choice in ["📍 Share My Location", "📍 አድራሻ አጋራ"]:
        await update.message.reply_text(
            "📍 Please click the location button above to share your location." if language == 'english' else "📍 አድራሻ ለመጋራት ከላይ ያለውን ቁልፍ ይጫኑ።"
        )
        return LOCATION
    
    elif choice in ["✏️ Enter Address Manually", "✏️ አድራሻ አስገባ"]:
        await update.message.reply_text(
            get_text(context, 'location_manual_prompt', {}),
            reply_markup=ReplyKeyboardRemove()
        )
        return LOCATION
    
    else:
        # User entered address manually
        address = update.message.text.strip()
        
        if len(address) < 5:
            await update.message.reply_text(
                get_text(context, 'location_invalid', {})
            )
            return LOCATION
        
        context.user_data['location'] = address
        context.user_data['location_source'] = 'manual_entry'
        
        await update.message.reply_text(
            get_text(context, 'location_confirmed', {'location':address})
        )
        return await show_confirmation(update, context)

async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation menu with all collected information."""
    name = context.user_data.get('name', 'Not provided')
    service_type = context.user_data.get('service_type', 'Not provided')
    services = context.user_data.get('services', 'Not provided')
    phone = context.user_data.get('phone', 'Not provided')
    location = context.user_data.get('location', 'Not provided')
    phone_source = context.user_data.get('phone_source', 'manual_entry')
    location_source = context.user_data.get('location_source', 'manual_entry')
    
    phone_status = "(✅ Verified)" if phone_source == 'contact_shared' else "(📝 Manual)"
    if get_user_language(context) == 'amharic':
        phone_status = "(✅ ተረጋገጧል)" if phone_source == 'contact_shared' else "(📝 በእጅ)"
    
    await update.message.reply_text(
        get_text(context, 'confirmation_summary', {
            'name': name,
            'phone': phone,
            'phone_status': phone_status,
            'service_type': service_type,
            'services': services,
            'location': location
        }),
        reply_markup=ReplyKeyboardMarkup(
            get_menu(context, 'confirmation_menu'),
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CONFIRMATION

async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle final confirmation with menu."""
    choice = update.message.text
    confirmation_menu = get_menu(context, 'confirmation_menu')
    
    # Debug logging
    logger.info(f"Confirmation handler called with choice: {choice}")
    logger.info(f"Expected confirmation button: {confirmation_menu[0][0]}")
    logger.info(f"Match result: {choice == confirmation_menu[0][0]}")
    
    if choice == confirmation_menu[0][0]:  # "Confirm & Submit Request" equivalent
        # Get all collected data
        name = context.user_data.get('name', 'Not provided')
        service_type = context.user_data.get('service_type', 'Not provided')
        services = context.user_data.get('services', 'Not provided')
        phone = context.user_data.get('phone', 'Not provided')
        location = context.user_data.get('location', 'Not provided')
        phone_source = context.user_data.get('phone_source', 'manual_entry')
        location_source = context.user_data.get('location_source', 'manual_entry')
        
        context.user_data['saved_contact_info'] = {
            'name': name,
            'phone': phone,
            'location': location,
            'phone_source': phone_source
        }
        
        user_info = context.user_data.get('user_info', {})
        telegram_id = user_info.get('user_id')
        username = user_info.get('username')
        first_name = user_info.get('first_name')
        last_name = user_info.get('last_name')
        
        save_user_to_db(telegram_id, username, first_name, last_name)
        
        request_id = save_service_request_to_db(
            telegram_id, name, phone, location, 
            service_type, services, phone_source, location_source
        )
        
        # Log the submission
        logger.info(f"New service request #{request_id} - Name: {name}, Phone: {phone}, Location: {location}, Type: {service_type}, Service: {services}")
        
        # Final success message
        await update.message.reply_text(
            get_text(context, 'success_message', {
                'name': name,
                'service_type': service_type,
                'services': services,
                'location': location,
                'phone': phone
            }))
        
        language = get_user_language(context)
        post_submission_menu = [
            ["🔄 New Request" if language == 'english' else "🔄 አዲስ ጥያቄ"],
            ["🏠 Main Menu" if language == 'english' else "🏠 ዋና ገፅ"]
        ]
        
        await update.message.reply_text(
            "What would you like to do next?" if language == 'english' else "ቀጥሎ ምን ማድረግ ይፈልጋሉ?",
            reply_markup=ReplyKeyboardMarkup(
                post_submission_menu,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        
        # Clear only the request data, keep saved contact info and language
        saved_contact = context.user_data.get('saved_contact_info')
        user_info = context.user_data.get('user_info')
        detected_name = context.user_data.get('detected_name')
        language_pref = context.user_data.get('language')
        
        context.user_data.clear()
        
        if saved_contact:
            context.user_data['saved_contact_info'] = saved_contact
        if user_info:
            context.user_data['user_info'] = user_info
        if detected_name:
            context.user_data['detected_name'] = detected_name
        if language_pref:
            context.user_data['language'] = language_pref
        
        return POST_SUBMISSION
    
    elif choice == confirmation_menu[1][0]:  # "Edit Service Type" equivalent
        context.user_data['editing_from_confirmation'] = True
        user_info = context.user_data.get('user_info', {})
        user_name = user_info.get('first_name', 'there')
        await update.message.reply_text(
            get_text(context, 'service_type_prompt', {'user_name':user_name}),
            reply_markup=ReplyKeyboardMarkup(
                get_menu(context, 'service_type_menu'),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return SERVICE_TYPE
    
    elif choice == confirmation_menu[1][1]:  # "Edit Services" equivalent
        context.user_data['editing_from_confirmation'] = True
        service_description = get_text(context, 'service_type_selected', {'key':context.user_data.get('service_type', '')})
        await update.message.reply_text(
            get_text(context, 'services_prompt', {'service_description':service_description}),
            reply_markup=ReplyKeyboardMarkup(
                create_service_selection_menu(context),
                one_time_keyboard=False,
                resize_keyboard=True
            )
        )
        return SERVICES
    
    elif choice == confirmation_menu[2][0]:  # "Edit Name" equivalent
        context.user_data['editing_from_confirmation'] = True
        detected_name = context.user_data.get('detected_name', '')
        services = context.user_data.get('services', '')
        service_details = get_text(context, 'service_details', {'key':services})
        await update.message.reply_text(
            get_text(context, 'name_prompt', {
                'service_details': service_details,
                'detected_name': detected_name
            }),
            reply_markup=ReplyKeyboardMarkup(
                get_menu(context, 'name_confirm_menu'),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return NAME_CONFIRM
    
    elif choice == confirmation_menu[2][1]:  # "Edit Phone" equivalent
        context.user_data['editing_from_confirmation'] = True
        # Create phone sharing keyboard
        phone_keyboard = [
            [KeyboardButton("📱 Share My Phone Number" if get_user_language(context) == 'english' else "📱 ስልክ ቁጥሬን አጋራ", request_contact=True)],
            ["✏️ Enter Phone Manually" if get_user_language(context) == 'english' else "✏️ ስልክ ቁጥር አስገባ"]
        ]
        
        await update.message.reply_text(
            get_text(context, 'name_confirmed', {'name':context.user_data.get('name', '')}),
            reply_markup=ReplyKeyboardMarkup(
                phone_keyboard,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return PHONE
    
    elif choice == confirmation_menu[3][0]:  # "Edit Location" equivalent
        context.user_data['editing_from_confirmation'] = True
        language = get_user_language(context)
        location_keyboard = [
            [KeyboardButton("📍 Share My Location" if language == 'english' else "📍 አድራሻ አጋራ", request_location=True)],
            ["✏️ Enter Address Manually" if language == 'english' else "✏️ አድራሻ አስገባ"]
        ]
        
        await update.message.reply_text(
            get_text(context, 'location_prompt', {}),
            reply_markup=ReplyKeyboardMarkup(
                location_keyboard,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return LOCATION
    
    elif choice == confirmation_menu[3][1]:  # "Cancel Request" equivalent
        await update.message.reply_text(
            get_text(context, 'cancelled', {}),
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    else:
        # Fallback: if choice doesn't match, show confirmation again
        logger.warning(f"Unmatched choice in confirmation: {choice}")
        return await show_confirmation(update, context)

async def post_submission_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle post-submission menu choices."""
    choice = update.message.text
    language = get_user_language(context)
    
    if choice in ["🔄 New Request", "🔄 አዲስ ጥያቄ"]:
        # Start a new request
        user_info = context.user_data.get('user_info', {})
        user_name = user_info.get('first_name', 'there')
        await update.message.reply_text(
            get_text(context, 'service_type_prompt', {'user_name':user_name}),
            reply_markup=ReplyKeyboardMarkup(
                get_menu(context, 'service_type_menu'),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return SERVICE_TYPE
    
    elif choice in ["🏠 Main Menu", "🏠 ዋና ገፅ"]:
        # Return to main menu
        user_info = context.user_data.get('user_info', {})
        user_name = user_info.get('first_name', 'there')
        await update.message.reply_text(
            get_text(context, 'initial_welcome', {'user_name':user_name}),
            reply_markup=ReplyKeyboardMarkup(
                get_main_menu(context),
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return MAIN_MENU
    
    return POST_SUBMISSION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    await update.message.reply_text(
        get_text(context, 'cancelled', {}),
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message."""
    if 'language' not in context.user_data:
        context.user_data['language'] = 'amharic'
    
    await update.message.reply_text(
        get_text(context, 'help', {}),
        reply_markup=ReplyKeyboardMarkup(
            get_main_menu(context),
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages and guide users to /start."""
    user = update.message.from_user
    
    # Set default language if not set
    if 'language' not in context.user_data:
        context.user_data['language'] = 'amharic'
    
    # Use proper text system for consistent language
    language = get_user_language(context)
    if language == 'amharic':
        message_text = (
            f"👋 ሰላም {user.first_name}! ወደ ልዩ አጋዥ እንኳን በደህና መጡ! 🏠\n\n"
            "የቤት አገልግሎቶችን ለመያዝ እዚህ ነኝ።\n\n"
            "ዋና ገፅን ለመክፈት /start ይጠቀሙ።"
        )
    else:
        message_text = (
            f"👋 Hello {user.first_name}! Welcome to Liyu Househelp! 🏠\n\n"
            "I'm here to help you book our home services.\n\n"
            "Please use /start to open the main menu."
        )
    
    await update.message.reply_text(
        message_text,
        reply_markup=ReplyKeyboardMarkup(
            get_main_menu(context),
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

def main():
    """Start the client service bot."""
    # Get token from environment variables
    TOKEN = os.getenv('BOT_TOKEN_CLIENT')
    
    if not TOKEN:
        logger.error("❌ BOT_TOKEN_CLIENT not found in environment variables!")
        logger.error("Please check your .env file")
        return
    
    # Initialize database
    init_database()
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)
            ],
            INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, info_handler)
            ],
            SETTINGS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler)
            ],
            LANGUAGE: [
                MessageHandler(filters.Regex('^(🇬🇧 English|🇪🇹 Amharic)$'), language_selection)
            ],
            SERVICE_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, service_type)
            ],
            SERVICES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, services)
            ],
            SERVICES_OTHER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, services_other)
            ],
            CONTACT_CHECK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_check)
            ],
            NAME_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name_confirm)
            ],
            PHONE: [
                MessageHandler(filters.TEXT | filters.CONTACT, phone)
            ],
            LOCATION: [
                MessageHandler(filters.TEXT | filters.LOCATION, location)
            ],
            CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)
            ],
            POST_SUBMISSION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, post_submission_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel),  CommandHandler('start', start) ]
    )

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    print("Liyu Househelp Client Service Bot is starting...")
    print("Token loaded from environment variables")
    print("Welcome to Liyu Househelp!")
    print("Multi-language support: English & Amharic")
    print("Bot is ready to accept service requests!")
    print("Features:")
    print("   • Main Menu with Start, Info, and Settings")
    print("   • Complete button-based navigation")
    print("   • Full Amharic translations")
    print("   • Phone number sharing with contact button")
    print("   • Multiple service selection support")
    print("   • 'Other' service option")
    print("   • Returning user recognition with saved contact info")
    print("   • Post-submission menu for easy navigation")
    print("   • Location collection with GPS and manual address entry")
    print("Press Ctrl+C to stop the bot")
    
    try:
        # 👇 this line changed
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        print("❌ Bot failed to start. Please check your token and internet connection.")


if __name__ == '__main__':
    main()
