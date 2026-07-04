import os
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ContextTypes
)

# ── CONFIG ────────────────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")

CH1_ID   = os.getenv("CH1_ID")
CH1_LINK = os.getenv("CH1_LINK")

CH2_ID   = os.getenv("CH2_ID")
CH2_LINK = os.getenv("CH2_LINK")

CH3_ID   = os.getenv("CH3_ID")
CH3_LINK = os.getenv("CH3_LINK")

CH4_ID   = os.getenv("CH4_ID")
CH4_LINK = os.getenv("CH4_LINK")

CH5_ID   = os.getenv("CH5_ID")
CH5_LINK = os.getenv("CH5_LINK")

CH6_ID   = os.getenv("CH6_ID")
CH6_LINK = os.getenv("CH6_LINK")

AUTO_DELETE_SECONDS = 10 * 60  # 10 minutes

# ── VERIFY KE BAD DIKHNE WALA MESSAGE ────────────────────────────────────────

HELLO_MESSAGE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━
UPLOAD ID FIX SOLUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1️⃣
Take a screenshot of the "Upload Your ID" or document review
 message for your records.

━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2️⃣
Review the document you submitted and make sure: • The name is clearly visible
* The date of birth is readable
* The document is valid and unexpired
* The image is clear and uncropped

━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3️⃣
If your document is rejected, carefully read the reason provided by Instagram.

━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4️⃣
Prepare an alternative valid government-issued ID if available, or resubmit a clearer image of the original document.

━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5️⃣
If you believe the rejection was a mistake, contact Instagram or Meta Support and explain your situation clearly.

━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6️⃣
Include: • Username
* Account email/phone number
* Screenshot of the error message
* A brief explanation of why you believe the decision was incorrect

━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 7️⃣
Wait for the review process to complete and monitor your email for updates.

━━━━━━━━━━━━━━━ 
✅ Use accurate account information and valid documents during the review process.
 ━━━━━━━━━━━━━━━

FIR BHI GHANTA SAMAJH NAA AAYE TOH 
SIRF ITNA SUNLE 
OR KUCH NAHI EK UNPATCH DOCUMENTS LAGA LE 
UNPACTCH DOCUMENT USE KAREGA TOH KOI DIKKAT NAHI AAYEGI
"""

HELLO_MESSAGE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━
NONAPPEAL BOT REASON METHOD -1
━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1
sbse pehele suspended account ko saare devices se log out krdo

━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2
ab Instagram ki app info m jake clear chache and clear data krdo.

━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3
account ka pass reset kro reset link se.

━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4
5 se 6 devices m account ko log in krlo

━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 5 
ab vpn laga k 1 device se appeal krdo.

━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 6
saare devices se account ko log out krdo

━━━━━━━━━━━━━━━━━━━━━━━━━━
If appeal stuck m jati haii to 10-12 hours m account lock ho jayega due to multiple log in ab us account ko easily log in krlo 🥰👆
"""

HELLO_MESSAGE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━
NONAPPEAL BOT REASON METHOD -2
━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1
Fresh device main use karo jisme ip ban na ho

━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2
Face verification do
Number use karo jisme instagram na bana ho
Fresh email use karo

━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3
Unpatch documents use karo

━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4
Aur kya lega bas hogaya account unban
Use unpatch documents you will get your result in 5 minutes
"""

HELLO_MESSAGE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━
DISABLED ACCOUNT BOT REASON/INTEGRITY CASE TEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━
Hello Instagram Support,
I am writing to respectfully request a manual review of my Instagram account, which was disabled under the category of "Integrity / Bypass." I believe this enforcement may have been applied in error.
To the best of my knowledge, I have not engaged in any activity intended to bypass Instagram's policies, security systems, or enforcement mechanisms. I have not knowingly participated in impersonation, fraud, spam operations, unauthorized automation, or any other behavior designed to violate Instagram's Community Standards or Terms of Use.
If unusual activity was detected on my account, it may have resulted from a login anomaly, security issue, compromised session, or an automated enforcement error rather than any intentional misconduct on my part.
I previously submitted an appeal, but the decision appears to have been upheld without a detailed manual investigation. Therefore, I am respectfully requesting that my case be reviewed by a human specialist who can examine the full context of my account activity.
I am fully willing to cooperate with any additional verification requirements and provide any information necessary to confirm my identity and account ownership.
I respectfully request:
* A complete manual review of my account
* Reassessment of the disablement decision
* Restoration of my account if the enforcement was applied incorrectly
Account Information:
Username: @username
Full Name: [Your Name]
Linked Email: [Your Email]
Thank you for your time and consideration. I appreciate any assistance you can provide and look forward to your response.
Sincerely,
[Your Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

HELLO_MESSAGE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━
DISABLED ACCOUNT SCAM/FRAUD CASE TEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━
Hello Instagram Support,
I am writing to respectfully request a manual review of my Instagram account, which was disabled under the category of "Scam / Fraud." I believe this enforcement may have been applied in error.
I have never intentionally engaged in fraudulent activity, impersonation, phishing, deception, financial scams, or any behavior intended to mislead other users. I take Instagram's policies seriously and have always tried to use the platform in accordance with its Community Standards and Terms of Use.
If suspicious activity was detected on my account, it may have been the result of a false positive, unauthorized access, reporting abuse, a security issue, or an automated enforcement error rather than any intentional misconduct on my part.
I previously submitted an appeal; however, it appears that the decision may have been made without a thorough manual investigation. Therefore, I respectfully request that my case be reviewed by a human specialist who can evaluate the complete context of my account activity.
I am fully willing to verify my identity and cooperate with any additional security or verification procedures required to confirm my ownership of the account.
I respectfully request:
* A complete manual review of my account
* Reassessment of the disablement decision
* Restoration of my account if the enforcement was applied incorrectly
Account Information:
Username: @username
Full Name: [Your Name]
Linked Email: [Your Email]
Thank you for your time and consideration. I sincerely appreciate any assistance you can provide and look forward to your response.
Kind regards,
[Your Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

# ── JOIN CHECK ────────────────────────────────────────────────────────────────

async def is_user_joined(bot, user_id: int) -> bool:
    for channel_id in [CH1_ID, CH2_ID, CH3_ID, CH4_ID, CH5_ID, CH6_ID]:
        if not channel_id:
            continue
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True

def join_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Channel 1", url=CH1_LINK or "https://t.me/ruchika_ownss"),
            InlineKeyboardButton("📢 Channel 2", url=CH2_LINK or "https://t.me/backupvnsh"),
            InlineKeyboardButton("📢 Channel 3", url=CH3_LINK or "https://t.me/ruchu_owns"),       
            InlineKeyboardButton("📢 Channel 4", url=CH4_LINK or "https://t.me/ruchii_owns"),
            InlineKeyboardButton("📢 Channel 5", url=CH5_LINK or "https://t.me/v4nshera"),
            InlineKeyboardButton("📢 Channel 6", url=CH6_LINK or "https://t.me/leeeunjuu"),
            
            
        ],
        [InlineKeyboardButton("♻️ Try Again", callback_data="verify_join")],
    ])

# ── AUTO DELETE ───────────────────────────────────────────────────────────────

async def schedule_delete(bot, chat_id, message_id, delay=AUTO_DELETE_SECONDS):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

# ── MESSAGE SEND + AUTO DELETE ────────────────────────────────────────────────

async def send_hello_message(bot, chat_id):
    sent = await bot.send_message(
        chat_id=chat_id,
        text=HELLO_MESSAGE,
        protect_content=True
    )
    asyncio.create_task(schedule_delete(bot, chat_id, sent.message_id))

# ── START ─────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user   = update.effective_user
    joined = await is_user_joined(context.bot, user.id)

    if not joined:
        await update.message.reply_text(
            f"Hey {user.first_name} 👋\n\n"
            "Please Join All My Update Channels To Use Me! 🔒",
            reply_markup=join_markup()
        )
        return

    await send_hello_message(context.bot, update.effective_chat.id)

# ── VERIFY JOIN CALLBACK ──────────────────────────────────────────────────────

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    user   = query.from_user
    joined = await is_user_joined(context.bot, user.id)

    if joined:
        await query.answer(
            "☬ ᴀᴜᴛʜᴇɴᴛɪᴄᴀᴛɪᴏɴ ᴄᴏᴍᴘʟᴇᴛᴇ ☬\n🔓 ᴀᴄᴄᴇss ɢʀᴀɴᴛᴇᴅ",
            show_alert=True
        )
        try:
            await query.message.delete()
        except Exception:
            pass

        granted = await context.bot.send_message(
            query.message.chat.id,
            "┏━━━「 ᴀᴄᴄᴇss ɢʀᴀɴᴛᴇᴅ 🎉 」━━━┓\n"
            "┃\n"
            "┃ ʙᴏᴛ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴʟᴏᴄᴋᴇᴅ!\n"
            "┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━┛"
        )
        asyncio.create_task(
            schedule_delete(context.bot, granted.chat.id, granted.message_id)
        )

        await send_hello_message(context.bot, query.message.chat.id)

    else:
        await query.answer(
            "❌ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ғᴀɪʟᴇᴅ • ᴊᴏɪɴ ʙᴏᴛʜ ᴄʜᴀɴɴᴇʟs ғɪʀsᴛ",
            show_alert=True
        )

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_join_callback, pattern="^verify_join$"))

    print("✅ Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
