from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os

# Ambil token dan seller code dari environment variables
TOKEN = os.getenv("TOKEN")
SELLER_CODE = os.getenv("SELLER_CODE")

if not TOKEN or not SELLER_CODE:
    raise ValueError("Token atau SELLER_CODE tidak ditemukan di environment variables!")

# API Endpoints
REQ_OTP_URL = "https://nomorxlku.my.id/api/req_otp.php"
VER_OTP_URL = "https://nomorxlku.my.id/api/ver_otp.php"
CHECK_QUOTA_URL = "https://nomorxlku.my.id/api/check_quota.php"
CHECK_VERIF_URL = "https://nomorxlku.my.id/api/check_ver_otp.php"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📲 Login Nomor XL")],
        [KeyboardButton("📊 Cek Kuota"), KeyboardButton("ℹ️ Cek Status Verifikasi")],
        [KeyboardButton("🚪 Logout"), KeyboardButton("🆘 Bantuan Admin")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🔹 *Selamat Datang!* 🔹\nSilakan pilih menu di bawah:",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

async def login_xl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Masukkan nomor XL kamu (08xxx / 628xxx):")
    return 1

async def request_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msisdn = update.message.text.strip()

    if not msisdn.startswith("08") and not msisdn.startswith("628"):
        await update.message.reply_text("❌ Nomor tidak valid! Gunakan format 08xxxx atau 628xxxx.")
        return ConversationHandler.END

    payload = {"msisdn": msisdn, "seller_code": SELLER_CODE}

    try:
        response = requests.post(REQ_OTP_URL, data=payload, timeout=10).json()

        if response.get("status"):
            await update.message.reply_text(f"📨 OTP telah dikirim ke nomor {msisdn}.")
        else:
            await update.message.reply_text(f"❌ Gagal mengirim OTP: {response.get('message')}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📲 Login Nomor XL$"), login_xl))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, request_otp))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
