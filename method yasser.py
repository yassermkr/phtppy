import telebot
import requests
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)

# Configure the bot
bot = telebot.TeleBot("7211896389:AAHPDavrq5bD2Fepz30N0QBABMVWrsUrRvk")

# Dictionary to store user data
user_data_dict = {}

# Function to check balance
def check_balance(access_token):
    url = "https://ibiza.ooredoo.dz/api/v1/mobile-bff/users/balance"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': "okhttp/4.9.3",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'language': "AR",
        'request-id': "995fd8a7-853c-481d-b9c6-0a24295df76a",
        'flavour-type': "gms"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        accounts = response_json.get('accounts', [])

        for account in accounts:
            if account.get('label') == 'رصيد التكفل المهدى':
                return account.get('value', None)

    return None

# Function to check if 24 hours have passed since the last interaction
def can_use_service(user_id):
    if user_id not in user_data_dict:
        return True
    last_used = user_data_dict[user_id].get('last_used')
    if last_used is None:
        return True
    if datetime.now() - last_used > timedelta(hours=24):
        return True
    return False

# Update the timestamp of the last interaction
def update_last_used(user_id):
    user_data_dict[user_id]['last_used'] = datetime.now()

# Handle start command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if can_use_service(user_id):
        bot.reply_to(message, 'مرحبًا! أدخل رقم الهاتف:')
        bot.reply_to(message, '📲')
    else:
        bot.reply_to(message, 'يمكنك استخدام البوت مرة واحدة كل 24 ساعة. حاول مرة أخرى لاحقًا.')

# Handle messages
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_message(message):
    user_id = message.from_user.id
    user_input = message.text

    if user_id in user_data_dict and user_data_dict[user_id].get('awaiting_otp', False):
        # User is awaiting OTP, process OTP input
        otp = user_input
        num = user_data_dict[user_id]['num']

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'ibiza.ooredoo.dz',
            'Connection': 'Keep-Alive',
            'User-Agent': 'okhttp',
        }
        data = {
            'client_id': 'ibiza-app',
            'otp': otp,
            'grant_type': 'password',
            'mobile-number': num,
            'language': 'AR',
        }
        response = requests.post('https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token', headers=headers, data=data)

        if response.status_code == 200:
            access_token = response.json().get('access_token')
            if access_token:
                bot.reply_to(message, 'تم التحقق بنجاح. يتم الآن التحقق من الإنترنت..🚀🔰')
                user_data_dict[user_id]['access_token'] = access_token
                user_data_dict[user_id]['awaiting_otp'] = False

                # Example of sending multiple internet requests
                url = 'https://ibiza.ooredoo.dz/api/v1/mobile-bff/users/mgm/info/apply'
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'language': 'AR',
                    'request-id': 'ef69f4c6-2ead-4b93-95df-106ef37feefd',
                    'flavour-type': 'gms',
                    'Content-Type': 'application/json'
                }
                payload = {"mgmValue": "ABC"}

                count = 0  # Counter for number of "Internet sent" messages

                while count < 6:
                    response = requests.post(url, headers=headers, json=payload)
                    count += 1

                # Inform user about internet sent
                bot.send_message(message.chat.id, 'تم إرسال الإنترنت بنجاح!✅🚀🎉')

                # After all requests, check balance
                balance = check_balance(access_token)
                if balance is not None:
                    bot.send_message(message.chat.id, f"حجم الأنترنت: 🎉 {balance}")
                else:
                    bot.send_message(message.chat.id, "فشل في استرداد الرصيد.🛜❌")

                # Update the last used timestamp
                update_last_used(user_id)

        else:
            bot.reply_to(message, 'فشل في التحقق من الرمز❌💬.')

    else:
        # User is providing phone number
        if can_use_service(user_id):
            num = user_input
            user_data_dict[user_id] = {'num': num}
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'ibiza.ooredoo.dz',
                'Connection': 'Keep-Alive',
                'User-Agent': 'okhttp/4.9.3',
            }
            data = {
                'client_id': 'ibiza-app',
                'grant_type': 'password',
                'mobile-number': num,
                'language': 'AR',
            }
            response = requests.post('https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token', headers=headers, data=data)

            if 'ROOGY' in response.text:
                bot.reply_to(message, 'تم إرسال رمز 💬. أدخل الرمز:')
                bot.reply_to(message, '💬')
                user_data_dict[user_id]['awaiting_otp'] = True
            else:
                bot.reply_to(message, 'فشل في إرسال رمز❌💬.')
        else:
            bot.reply_to(message, 'يمكنك استخدام البوت مرة واحدة كل 24 ساعة. حاول مرة أخرى لاحقًا.')

# Start polling
bot.polling(none_stop=True, interval=0, timeout=20)