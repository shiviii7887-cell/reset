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

AUTO_DELETE_SECONDS = 5 * 60  # 5 minutes

# ── VERIFY KE BAD DIKHNE WALA MESSAGE ────────────────────────────────────────

HELLO_MESSAGE = """
1. AAPKO APNI INSTAGRAM OR FACEBOOK KA CLEAR DATA OR CLEAR CACHE KAR LENA HE

2. SAME GMAIL SE FACEBOOK OR INSAGRAM ACCOUN BANAO

3. JO UNC ME GMAIL HE VO GMAIL FACEBOOK ME ADD KARO

4. IG ME CHECK KARO APNE AAP AAGA HOGA AGAR NAI AATA TO PHIR SE METHOD KARO 

5. AB FORGOT PASS KARO RESET LINK AAYEGA 

6. GERMANY KA VPN USE KARO TABHI WORK KAREGA.
"""

# ── JOIN CHECK ────────────────────────────────────────────────────────────────

async def is_user_joined(bot, user_id: int) -> bool:
    for channel_id in [CH1_ID, CH2_ID, CH3_ID, CH4_ID]:
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
            InlineKeyboardButton("📢 Join Channel 1", url=CH1_LINK or "https://t.me/ruchika_ownss"),
            InlineKeyboardButton("📢 Join Channel 2", url=CH2_LINK or "https://t.me/backupvnsh"),
            InlineKeyboardButton("📢 Join Channel 3", url=CH3_LINK or "https://t.me/ruchikaa_owns"),
            InlineKeyboardButton("📢 Join Channel 4", url=CH4_LINK or "https://t.me/ruchii_owns"),
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
        parse_mode="Markdown",
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
            "┃ 🔓 *ʙᴏᴛ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴʟᴏᴄᴋᴇᴅ!*\n"
            "┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━┛",
            parse_mode="Markdown"
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
