from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import requests

TOKEN = "7971420481:AAF9AhsQTFx_jW0sey5sSV4iJSHfcBrdYEY"

# API Endpoints
REQ_OTP_URL = "https://nomorxlku.my.id/api/req_otp.php"
VER_OTP_URL = "https://nomorxlku.my.id/api/ver_otp.php"
CHECK_QUOTA_URL = "https://nomorxlku.my.id/api/check_quota.php"
CHECK_VERIF_URL = "https://nomorxlku.my.id/api/check_ver_otp.php"

# Kode Seller
SELLER_CODE = "6cdeb687424a7d7a641d0494dfb2ec23"

# State untuk ConversationHandler
MSISDN, OTP, CHECK_MSISDN = range(3)

# Data penyimpanan sementara per user
user_data = {}

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

# ✅ **Fitur Login Nomor XL**
async def login_xl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Masukkan nomor XL kamu (08xxx / 628xxx):")
    return MSISDN

# ✅ **Perbaikan Fitur Request OTP**
async def request_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msisdn = update.message.text.strip()

    # **Validasi Nomor HP**
    if not msisdn.startswith("08") and not msisdn.startswith("628"):
        await update.message.reply_text("❌ Nomor tidak valid! Gunakan format 08xxxx atau 628xxxx.")
        return ConversationHandler.END

    # Simpan nomor ke dalam `user_data`
    user_data[update.message.chat_id] = {"msisdn": msisdn}
    payload = {"msisdn": msisdn, "seller_code": SELLER_CODE}

    try:
        response = requests.post(REQ_OTP_URL, data=payload, timeout=10)
        response_json = response.json()

        if response_json.get("status"):
            user_data[update.message.chat_id]["auth_id"] = response_json["data"]["auth_id"]

            keyboard = [[InlineKeyboardButton("✅ Masukkan OTP", callback_data="masukkan_otp")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(f"📨 OTP telah dikirim ke nomor {msisdn}.", reply_markup=reply_markup)
            return OTP
        else:
            await update.message.reply_text(f"❌ Gagal mengirim OTP: {response_json.get('message')}")
            return ConversationHandler.END

    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan saat menghubungi server: {str(e)}")
        return ConversationHandler.END

# ✅ **Input OTP setelah klik tombol**
async def input_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    await query.message.reply_text("🔑 Silakan masukkan kode OTP yang kamu terima:")
    return OTP

# ✅ **Verifikasi OTP**
async def verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    otp_code = update.message.text.strip()
    user_info = user_data.get(chat_id, {})

    if not user_info:
        await update.message.reply_text("⚠️ Kamu belum login. Gunakan 📲 Login Nomor XL untuk masuk terlebih dahulu.")
        return ConversationHandler.END

    payload = {"msisdn": user_info["msisdn"], "auth_id": user_info["auth_id"], "otp": otp_code}

    try:
        response = requests.post(VER_OTP_URL, data=payload, timeout=10).json()
        if response.get("status"):
            user_data[chat_id]["access_token"] = response["data"]["access_token"]
            await update.message.reply_text("✅ Login berhasil! Sekarang kamu bisa cek kuota.")
        else:
            await update.message.reply_text(f"❌ Verifikasi OTP gagal: {response.get('message')}")

        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan: {str(e)}")
        return ConversationHandler.END

# ✅ **Cek Kuota**
async def check_quota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    access_token = user_data.get(chat_id, {}).get("access_token")

    if not access_token:
        await update.message.reply_text("⚠️ Kamu belum login. Gunakan 📲 Login Nomor XL untuk masuk terlebih dahulu.")
        return

    payload = {"access_token": access_token}

    try:
        response = requests.post(CHECK_QUOTA_URL, data=payload, timeout=10).json()
        if response.get("status"):
            text = "📊 *Informasi Kuota:*\n\n"
            for quota in response["data"]["quotas"]:
                text += f"📌 *{quota['name']}*\n"
                text += f"🕒 Expired: {quota['expired_at']}\n"
                for benefit in quota["benefits"]:
                    text += f"🔹 {benefit['name']}: {benefit['quota']} (Sisa: {benefit['remaining_quota']})\n"
                text += "\n"

            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Gagal cek kuota: {response.get('message')}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan: {str(e)}")

# ✅ **Logout**
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data.pop(update.message.chat_id, None)
    await update.message.reply_text("🚪 Kamu telah logout. Silakan /start untuk login kembali.")

# ✅ **Bantuan Admin**
async def bantuan_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 Untuk bantuan admin, hubungi: [Admin](https://t.me/admin_bot)", parse_mode="Markdown")

# ✅ **Fitur Cek Status Verifikasi**
async def request_verifikasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Masukkan nomor XL yang ingin dicek (08xxx / 628xxx):")
    return CHECK_MSISDN

async def check_verifikasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msisdn = update.message.text.strip()

    # Validasi nomor XL
    if not msisdn.startswith("08") and not msisdn.startswith("628"):
        await update.message.reply_text("❌ Nomor tidak valid! Gunakan format 08xxxx atau 628xxxx.")
        return CHECK_MSISDN  # Minta input ulang

    payload = {"username": SELLER_CODE, "msisdn": msisdn}

    try:
        response = requests.post(CHECK_VERIF_URL, data=payload, timeout=10).json()

        if response.get("status"):
            message = response.get("message", "✅ Nomor ini pernah terverifikasi.")
        else:
            message = response.get("message", "❌ Nomor ini belum pernah login atau terverifikasi.")

        await update.message.reply_text(f"ℹ️ *Status Verifikasi untuk {msisdn}:*\n{message}", parse_mode="Markdown")
        return ConversationHandler.END  # Selesai

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏳ Server sedang sibuk. Coba lagi nanti.")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan: {str(e)}")
        return ConversationHandler.END

# ✅ **Main Function**
def main():
    app = Application.builder().token(TOKEN).build()

    # Handler untuk login & OTP
    login_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📲 Login Nomor XL$"), login_xl)],
        states={
            MSISDN: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_otp)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_otp)]
        },
        fallbacks=[]
    )

    # Handler untuk cek status verifikasi
    verif_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^ℹ️ Cek Status Verifikasi$"), request_verifikasi)],
        states={
            CHECK_MSISDN: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_verifikasi)]
        },
        fallbacks=[]
    )

    # Handler untuk semua fitur
    app.add_handler(CommandHandler("start", start))
    app.add_handler(login_conv_handler)
    app.add_handler(verif_conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^📊 Cek Kuota$"), check_quota))
    app.add_handler(MessageHandler(filters.Regex("^🚪 Logout$"), logout))
    app.add_handler(MessageHandler(filters.Regex("^🆘 Bantuan Admin$"), bantuan_admin))
    app.add_handler(CallbackQueryHandler(input_otp, pattern="masukkan_otp"))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()