import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from google import genai
from google.genai import types
import time 
import asyncio
import os
from dotenv import load_dotenv
# ===== CONFIG =====
TOKEN = os.getenv("TELEGRAM_TOKEN")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

load_dotenv()
# ===== DATABASE =====  
conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    phone TEXT PRIMARY KEY,
    name TEXT,
    address TEXT,
    product TEXT,
    status TEXT
)
""")
conn.commit()

# ===== STATE =====
user_state = {}
chat_count = {}

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌸 Tư vấn nước hoa", callback_data="consult")],
        [InlineKeyboardButton("🛒 Chốt đơn", callback_data="order")],
        [InlineKeyboardButton("🔍 Tra cứu đơn", callback_data="lookup")],
        [InlineKeyboardButton("✏️ Sửa đơn", callback_data="edit")]
    ]

    await update.message.reply_text(
        "Xin chào! Tôi là Tài ho chướng 😎 chuyên tư vấn nước hoa xịn sò!\nBạn cần gì nào?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== AI CONSULT =====
async def consult_ai(update, context):
    user_id = update.message.chat_id
    chat_count[user_id] = chat_count.get(user_id, 0) + 1
    user_input = update.message.text
    
    final_prompt = f"""
    HÀNH ĐỘNG NHƯ MỘT CHUYÊN GIA NƯỚC HOA TÊN 'TÀI HO CHƯỚNG'.
    
    DANH SÁCH SẢN PHẨM:
    1. Dior Sauvage: Nam tính, mạnh mẽ.
    2. Chanel No.5: Sang trọng, quý phái.
    3. Gucci Bloom: Ngọt ngào, nhẹ nhàng.
    4. Versace Eros: Quyến rũ, bùng nổ.
    5. YSL Libre: Thanh lịch, hiện đại.

    YÊU CẦU TỪ KHÁCH: "{user_input}"

    QUY TẮC BẮT BUỘC:
    - Viết ít nhất 3 câu hoàn chỉnh.
    - Tổng độ dài tối thiểu 80 chữ.
    - Không được trả lời ngắn.
    - Không được kết thúc đột ngột.
    """

    try:
        await asyncio.sleep(1)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=final_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=2000,
                temperature=0.7,
            )
        )

        if response.candidates and len(response.candidates) > 0:
            reply = response.candidates[0].content.parts[0].text
            keyboard = [[InlineKeyboardButton("🛒 Chốt đơn ngay", callback_data="order")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reply = "Tài bí ý tưởng rồi 😅 bạn hỏi lại kiểu khác nha!"

    except Exception as e:
        print(f"Lỗi AI: {e}")
        if "429" in str(e):
            reply = "Tài đang quá tải 🤯 đợi chút rồi hỏi lại nha!"
        else:
            reply = "Lỗi hệ thống rồi 😭 thử lại giúp Tài!"

    await update.message.reply_text(reply, reply_markup=reply_markup if 'reply_markup' in locals() else None)

# ===== BUTTON HANDLER =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.message.chat_id
    data = query.data

    if data == "consult":
        user_state[user_id] = "consult"
        await query.message.reply_text("Bạn thích mùi hương như nào?")

    elif data == "order":
        keyboard = [
            [InlineKeyboardButton("Dior Sauvage: Nam tính, mạnh mẽ.", callback_data="p_Dior")],
            [InlineKeyboardButton("Chanel No.5: Sang trọng, quý phái.", callback_data="p_Chanel")],
            [InlineKeyboardButton("Gucci Bloom: Ngọt ngào, nhẹ nhàng.", callback_data="p_Gucci")],
            [InlineKeyboardButton("Versace Eros: Quyến rũ, bùng nổ.", callback_data="p_Versace")],
            [InlineKeyboardButton("YSL Libre: Thanh lịch, hiện đại.", callback_data="p_YSL")]
        ]
        await query.message.reply_text("Chọn sản phẩm:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("p_"):
        context.user_data["product"] = data.split("_")[1]
        user_state[user_id] = "name"
        await query.message.reply_text("Nhập họ tên:")

    elif data == "lookup":
        user_state[user_id] = "lookup"
        await query.message.reply_text("Nhập số điện thoại:")

    elif data == "edit":
        user_state[user_id] = "edit_lookup"
        await query.message.reply_text("Nhập số điện thoại:")

    elif data == "confirm":
        d = context.user_data
        cursor.execute("REPLACE INTO orders VALUES (?,?,?,?,?)",
                       (d["phone"], d["name"], d["address"], d["product"], "Đang chờ xác nhận"))
        conn.commit()
        await query.message.reply_text("✅ Đã cập nhật đơn!")

    elif data == "retry":
        user_state[user_id] = "name"
        await query.message.reply_text("Nhập lại họ tên:")

# ===== MESSAGE FLOW =====
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Nhận tin nhắn từ user: {update.message.text}")
    user_id = update.message.chat_id
    state = user_state.get(user_id)

    if state == "consult":
        await consult_ai(update, context)

    elif state == "name":
        context.user_data["name"] = update.message.text
        user_state[user_id] = "phone"
        await update.message.reply_text("Nhập số điện thoại:")

    elif state == "phone":
        context.user_data["phone"] = update.message.text
        user_state[user_id] = "address"
        await update.message.reply_text("Nhập địa chỉ:")

    elif state == "address":
        context.user_data["address"] = update.message.text

        d = context.user_data
        cursor.execute("REPLACE INTO orders VALUES (?,?,?,?,?)",
                       (d["phone"], d["name"], d["address"], d["product"], "Đang chờ xác nhận"))
        conn.commit()

        await update.message.reply_text("🎉 Đặt hàng thành công!")

    elif state == "lookup":
        phone = update.message.text
        cursor.execute("SELECT * FROM orders WHERE phone=?", (phone,))
        row = cursor.fetchone()

        if row:
            await update.message.reply_text(
                f"Họ tên: {row[1]}\nSĐT: {row[0]}\nSản phẩm: {row[3]}\nTrạng thái: {row[4]}"
            )
        else:
            await update.message.reply_text("Không tìm thấy đơn!")

    elif state == "edit_lookup":
        phone = update.message.text
        cursor.execute("SELECT * FROM orders WHERE phone=?", (phone,))
        row = cursor.fetchone()

        if row:
            context.user_data["phone"] = phone
            user_state[user_id] = "name"
            await update.message.reply_text("Nhập lại họ tên:")
        else:
            await update.message.reply_text("Không tìm thấy đơn!")

    elif state == "address_confirm":
        context.user_data["address"] = update.message.text
        d = context.user_data

        keyboard = [
            [InlineKeyboardButton("✅ Chính xác", callback_data="confirm")],
            [InlineKeyboardButton("❌ Nhập lại", callback_data="retry")]
        ]

        await update.message.reply_text(
            f"Xác nhận:\n{d['name']}\n{d['phone']}\n{d['address']}\n{d['product']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ===== RUN =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

app.run_polling()