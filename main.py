from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler
from pymongo import MongoClient
from utils import *
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
class Database:
    def __init__(self):
        self.users = {}
        self.client = MongoClient('mongodb://hoangks5:hoangks5@103.75.182.201:27017/')
        self.db = self.client['iqglobal']
        self.collection = self.db['users']
        self.collection_key = self.db['keys']
    def check_user(self, user_id):
        user = self.collection.find_one({'user_id': user_id})
        if user:
            return user
        return False
    def check_ref(self, list_user_id):
        # kiểm tra xem list_user_id có bao nhiêu user_id đã có 1 key
        count = self.collection.count_documents({
            'user_id': {'$in': list_user_id},
            'keys': {'$exists': True, '$ne': []}
        })
        return count
    def create_key(self):
        pass
database = Database()


price_key = 50

command_help = """
📜 *Hướng dẫn sử dụng Bot*:
/start - 🌟 Bắt đầu sử dụng bot và khám phá các tính năng
/my - 👤 Xem thông tin tài khoản cá nhân của bạn
/ref - 👫 Xem danh sách người bạn đã giới thiệu
/deposit - 💸 Nạp tiền vào ví nhanh chóng và an toàn
/buy - 🛒 Mua key để kích hoạt các công cụ cao cấp
/key - 🔑 Kiểm tra danh sách và tình trạng các key bạn sở hữu
/tool - 🛠 Tải về công cụ hỗ trợ giao dịch của chúng tôi
"""



async def start(update: Update, context: CallbackContext) -> None:
    status = database.check_user(update.message.from_user.id)
    if not status:
        key = create_new_account()
        info = {
            'user_id': update.message.from_user.id,
            'address': key['address'],
            'private_key': key['private_key'],
            'ref': [],
            'balance_used': 0,
            'keys': []
        }
        id_ref = ' '.join(context.args)
        if id_ref.isdigit():
            id_ref = int(id_ref)
            database.collection.update_one({'user_id': update.message.from_user.id}, {'$push': {'ref': id_ref}})
        else:
            id_ref = None
        database.collection.insert_one(info)
        
    welcome_message = f"""
🎉 *Chào mừng {update.message.from_user.first_name} đến với bot AIPredict!* 🎉

💼 Tôi hỗ trợ giao dịch tự động trên sàn giao dịch IQGlobal Prediction dựa trên phân tích kĩ thuật bằng công nghệ AI tiên tiến bậc nhất thế giới!

{command_help}
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(command_help, parse_mode='Markdown')

async def my(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    status = database.check_user(user_id)
    key = status['keys']
    bonus = min(database.check_ref(status['ref']), 20)
    balance_deposit = get_balance_deposit(status['address']) - status['balance_used'] + bonus
    if key == []:
        account_info = f"""
💼 *Thông tin tài khoản của bạn:*
💰 Số dư: {balance_deposit} USDT"""
    else:
        account_info = f"""
    💼 *Thông tin tài khoản của bạn:*
💰 Số dư: {balance_deposit} USDT
🔗 Link giới thiệu: `t.me/IQGlobalTool_bot?start={update.message.from_user.id}`
    """
    await update.message.reply_text(account_info, parse_mode='Markdown')

async def ref(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    status = database.check_user(user_id)
    # kiểm tra người này đã có key chưa
    key = status['keys']
    if key == []:
        await update.message.reply_text("⚠️ Bạn chưa mua key nào cả\nHãy mua key để sử dụng hoạt động này")
        return
    ref_count = database.check_ref(status['ref'])
    referral_info = f"👥 Bạn đã giới thiệu được {ref_count} người"
    await update.message.reply_text(referral_info)

async def key(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    status = database.check_user(user_id)
    keys = status['keys']
    key_list = "🔑 *Danh sách key:*\n"
    for key in keys:
        if key['status'] == 'active':
            time_remaining = datetime.strptime(key['expired_time'], '%Y-%m-%d %H:%M:%S') - datetime.now()
            key_list += f"Key: `{key['key']}`\n⏳ Hạn sử dụng: {time_remaining}\n"
    await update.message.reply_text(key_list, parse_mode='Markdown')

async def buy(update: Update, context: CallbackContext) -> None:
    purchase_message = f"💵 *Giá của key là {price_key} USDT/30 ngày*\n\nBạn có muốn mua key không?"
    keyboard = [
        [InlineKeyboardButton("✅ Có", callback_data='confirm_buy')],
        [InlineKeyboardButton("❌ Không", callback_data='cancel_buy')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(purchase_message, reply_markup=reply_markup, parse_mode='Markdown')

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    status = database.check_user(user_id)
    bonus = min(database.check_ref(status['ref']), 20)
    balance_deposit = get_balance_deposit(status['address']) - status['balance_used'] + bonus
    keyboard_ok = [
        [InlineKeyboardButton("OK", callback_data='ok')]
    ]
    reply_markup_ok = InlineKeyboardMarkup(keyboard_ok)
    
    if query.data == 'confirm_buy':
        if balance_deposit < price_key:
            await query.edit_message_text("⚠️ Số dư không đủ để mua key", reply_markup=reply_markup_ok)
            return
        database.collection.update_one({'user_id': user_id}, {'$set': {'balance_used': status['balance_used'] + price_key}})
        new_key = gen_key()
        data_key = {
            'key': new_key,
            'expired_time': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'active'
        }
        database.collection.update_one({'user_id': user_id}, {'$push': {'keys': data_key}})
        data_key_user = {
            'key': new_key,
            'user_id': user_id,
            'log': []
        }
        database.collection_key.insert_one(data_key_user)
        await query.edit_message_text(f"🎉 Bạn đã mua key thành công!\n\n🔑 Key: `{new_key}`\n⏳ Hạn sử dụng: 30 ngày", reply_markup=reply_markup_ok, parse_mode='Markdown')
    elif query.data == 'cancel_buy':
        await query.edit_message_text("🚫 Bạn đã hủy mua key", reply_markup=reply_markup_ok )

async def tool(update: Update, context: CallbackContext) -> None:
    await update.message.reply_document(document=open('./iqglobal_v1.2.zip', 'rb'), filename='iqglobal_v1.2.zip')

async def deposit(update: Update, context: CallbackContext) -> None:
    status = database.check_user(update.message.from_user.id)
    address = status['address']
    generate_qr(address)
    deposit_message = f"""
🏦 *BEP20: {address}*

Hãy chuyển USDT vào địa chỉ trên để nạp tiền vào ví của bạn.
"""
    await update.message.reply_photo(photo=open(f"./qr_code/{address}.png", 'rb'), caption=deposit_message, parse_mode='Markdown')

    
# Hàm chính để chạy bot
def main() -> None:
    # Token của bạn từ BotFather
    token = '7488070683:AAFV5Lf-YZJRHMN0Dp6D07Qb3K0dD9Clj-8'

    # Tạo application và pass token
    app = ApplicationBuilder().token(token).build()

    # Đăng ký các lệnh
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("my", my))
    app.add_handler(CommandHandler("ref", ref))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("tool", tool))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("key",key))
    # Bắt đầu bot
    app.run_polling()

if __name__ == '__main__':
    main()
    
