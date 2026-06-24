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

AUTO_DELETE_SECONDS = 5 * 60  # 5 minutes

# ── VERIFY KE BAD DIKHNE WALA MESSAGE ────────────────────────────────────────

HELLO_MESSAGE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 STEP 1: IP Fix & Change (Mobile IP via VPN)

1️⃣ VPN install karo  
* ProtonVPN ya 1.1.1.1 VPN (safe & trusted)  
* Jo best lage wo use kar sakte ho  

2️⃣ VPN connect karo  
* Random country select karo  
* Example: Netherlands, Germany  

3️⃣ IP change confirm karo  
* Google pe search karo: What is my IP  
* New IP show ho rahi ho = IP change successful ✅  

4️⃣ Temporary break (IMPORTANT)  
* Kuch din tak jacking files / jacking mat karo  
* Pydroid 3 uninstall kar do  

5️⃣ Google Play Services reset  
* Settings > Apps > Manage Apps  
* Google Play Services  
* Clear Cache + Clear All Data  
━━━━━━━━━━━━━━━━━━━━━━━━━━
🔹 STEP 2: Instagram Reset Process

1️⃣ Instagram uninstall karo  
2️⃣ Settings > Google > Ads  
* Reset Advertising ID  
3️⃣ Phone restart karo  
4️⃣ Phone security update karo  
* Password change  
* Fingerprint / Face Lock reset  
5️⃣ Instagram dobara install karo  
6️⃣ Direct ID login mat karo ❌  
7️⃣ Pehle Instagram ka Dual / Clone app banana hoga  
━━━━━━━━━━━━━━━━━━━━━━━━━━
🔹 STEP 3: Instagram Clone App Method

1️⃣ Play Store se koi ek app install karo  
* Parallel Space  
* Dual Apps  
* Clone Maker  

2️⃣ Clone app ke andar Instagram clone karo  
3️⃣ Instagram sirf clone app ke andar hi open karo  
4️⃣ Apni Instagram ID login karo ✅  
5️⃣ 48 HOURS wait karo ⏳  
6️⃣ Dual / Clone app delete kar do  
7️⃣ Ab real Instagram app me login kar lo  
8️⃣ ✅ IP & device activity FIX ho chuki hogi  
━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ IMPORTANT NOTES
* Koi step skip mat karo  
* Jaldbazi mat karo  
* 48 hours ka wait mandatory he
* har bar alag alag nai koi 1 hi vpn use karo
* vpn ka primium leke sirf vo bhi use kar sake ho (safe hota he)
* mass report mat karo chat me abuse mat karo
* fight avoide karo 
* human ki tarah use karo normal use
"""

# ── JOIN CHECK ────────────────────────────────────────────────────────────────

async def is_user_joined(bot, user_id: int) -> bool:
    for channel_id in [CH1_ID, CH2_ID, CH3_ID, CH4_ID, CH5_ID]:
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
            InlineKeyboardButton("📢 Join Channel 5", url=CH4_LINK or "https://t.me/v4nshera"),
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
