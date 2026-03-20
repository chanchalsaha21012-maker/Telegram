# -*- coding: utf-8 -*-
import os
import time
import asyncio
import shutil
import sys
from datetime import datetime
import pyzipper
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# আপনার বট টোকেন এবং অ্যাডমিন আইডি (অবশ্যই টোকেন পরিবর্তন করবেন)
BOT_TOKEN = "8608550946:AAFFW49FlCz5aU9ZjXuUTUQzSELzHOjLu6U" 
ADMIN_ID = "7151641035"

# স্টার্ট কমান্ড
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔓 <b>প্রো Zip ক্র্যাকার বটে স্বাগতম!</b>\n\n"
        "আমি সাধারণ এবং AES-256 এনক্রিপ্টেড পাসওয়ার্ড প্রোটেক্টেড zip ফাইল ক্র্যাক করতে পারি।\n\n"
        "<b>কিভাবে ব্যবহার করবেন:</b>\n"
        "1️⃣ পাসওয়ার্ড প্রোটেক্টেড .zip ফাইল আপলোড করুন\n"
        "2️⃣ পাসওয়ার্ড লিস্ট (.txt ফাইল) আপলোড করুন\n"
        "3️⃣ আমি স্বয়ংক্রিয়ভাবে পাসওয়ার্ড চেক করব\n\n"
        "📁 পাসওয়ার্ড লিস্ট ফরম্যাট: প্রতি লাইনে একটি পাসওয়ার্ড",
        parse_mode=ParseMode.HTML
    )

# হেল্প কমান্ড
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 <b>ব্যবহার বিধি:</b>\n\n"
        "/start - বট চালু করুন\n"
        "/help - সাহায্য দেখুন\n"
        "/status - বর্তমান অবস্থা দেখুন\n"
        "/cancel - চলমান কাজ বাতিল করুন\n\n"
        "<b>অ্যাডমিন কমান্ড:</b>\n"
        "/admin - অ্যাডমিন প্যানেল চালু/বন্ধ করুন",
        parse_mode=ParseMode.HTML
    )

# স্ট্যাটাস কমান্ড
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    processing = context.user_data.get('processing', False)
    admin_mode = context.bot_data.get('admin_mode', False)
    
    status = "📊 <b>আপনার বর্তমান অবস্থা:</b>\n\n"
    status += f"🔄 প্রসেসিং: {'চলছে ⏳' if processing else 'কিছু নেই 💤'}\n"
    status += f"👤 ইউজার আইডি: <code>{user_id}</code>\n"
    
    if user_id == ADMIN_ID:
        status += f"👑 অ্যাডমিন: হ্যাঁ\n"
        status += f"⚙️ অ্যাডমিন মোড: {'চালু ✅' if admin_mode else 'বন্ধ ❌'}"
    
    if processing:
        status += f"\n\n📁 জিপ ফাইল: {context.user_data.get('zip_name', 'অজানা')}"
        status += f"\n🔑 মোট পাসওয়ার্ড: {context.user_data.get('password_count', 0)} টি"
    
    await update.message.reply_text(status, parse_mode=ParseMode.HTML)

# ক্যান্সেল কমান্ড
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('processing'):
        context.user_data['cancel_requested'] = True
        await update.message.reply_text("⏳ আপনার চলমান কাজ বাতিল করা হচ্ছে... একটু অপেক্ষা করুন।")
    else:
        await update.message.reply_text("❌ আপনার কোনো কাজ বর্তমানে চলছে না।")

# অ্যাডমিন কমান্ড
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ আপনার এই কমান্ড ব্যবহারের অনুমতি নেই!")
        return
    
    current_mode = context.bot_data.get('admin_mode', False)
    context.bot_data['admin_mode'] = not current_mode
    
    status = "✅ চালু" if context.bot_data['admin_mode'] else "❌ বন্ধ"
    
    keyboard = None
    if context.bot_data['admin_mode']:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📁 ফাইল আপলোড নির্দেশিকা", callback_data="upload_info")
        ]])
    
    await update.message.reply_text(
        f"🔧 <b>অ্যাডমিন মোড:</b> {status}\n\n"
        f"{'এখন আপনি .py ফাইল আপলোড করে বট আপডেট করতে পারবেন।' if context.bot_data['admin_mode'] else 'অ্যাডমিন মোড বন্ধ আছে।'}",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# কলব্যাক হ্যান্ডলার
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "upload_info":
        await query.message.reply_text(
            "📤 <b>ফাইল আপলোড নির্দেশিকা:</b>\n\n"
            "1. আপনার আপডেট করা .py ফাইল তৈরি করুন\n"
            "2. ফাইলটি এখানে আপলোড করুন\n"
            "3. বট স্বয়ংক্রিয়ভাবে আপডেট হবে\n\n"
            "⚠️ আপডেট ফাইলের নাম bot.py হতে হবে।",
            parse_mode=ParseMode.HTML
        )

# ফাইল হ্যান্ডলার
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    file_name = update.message.document.file_name
    file_size = update.message.document.file_size / (1024 * 1024)  # MB
    
    if file_size > 100:
        await update.message.reply_text(f"❌ ফাইল খুব বড়! সর্বোচ্চ 100MB অনুমোদিত। আপনার ফাইল: {file_size:.2f}MB")
        return
    
    if user_id == ADMIN_ID and context.bot_data.get('admin_mode', False):
        if file_name.endswith('.py'):
            await update_bot(update, context)
        else:
            await update.message.reply_text("❌ অ্যাডমিন মোড চালু আছে, শুধুমাত্র .py ফাইল আপলোড করুন অথবা অ্যাডমিন মোড বন্ধ করুন!")
        return
    
    if context.user_data.get('processing'):
        await update.message.reply_text("⚠️ আপনার আগের একটি কাজ চলছে। দয়া করে শেষ হওয়া পর্যন্ত অপেক্ষা করুন অথবা /cancel দিন।")
        return
    
    if file_name.endswith('.zip'):
        context.user_data['zip'] = update.message.document.file_id
        context.user_data['zip_name'] = file_name
        await update.message.reply_text(
            f"✅ Zip ফাইল সংরক্ষণ করা হয়েছে\n"
            f"📁 ফাইল: {file_name}\n"
            f"📊 সাইজ: {file_size:.2f}MB\n"
            f"🔑 এখন আপনার password.txt ফাইল আপলোড করুন"
        )
    
    elif file_name.endswith('.txt'):
        context.user_data['password'] = update.message.document.file_id
        
        try:
            status_msg = await update.message.reply_text("📥 পাসওয়ার্ড ফাইল পড়া হচ্ছে...")
            temp_file = await context.bot.get_file(context.user_data['password'])
            temp_path = f"temp_count_{user_id}.txt"
            await temp_file.download_to_drive(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
                context.user_data['password_count'] = len(passwords)
            
            os.remove(temp_path)
            await status_msg.edit_text(
                f"✅ পাসওয়ার্ড ফাইল প্রস্তুত!\n"
                f"📁 ফাইল: {file_name}\n"
                f"🔑 মোট পাসওয়ার্ড: {context.user_data['password_count']} টি"
            )
        except Exception as e:
            await update.message.reply_text("❌ পাসওয়ার্ড ফাইল রিড করতে সমস্যা হয়েছে।")
            return
        
        if 'zip' in context.user_data:
            context.user_data['processing'] = True
            context.user_data['cancel_requested'] = False
            asyncio.create_task(process_zip(update, context, passwords))
        else:
            await update.message.reply_text("দয়া করে আগে .zip ফাইল আপলোড করুন, তারপর .txt ফাইল দিন।")
    
    else:
        await update.message.reply_text("❌ শুধুমাত্র .zip এবং .txt ফাইল আপলোড করুন!")

# Zip প্রসেসিং ফাংশন
async def process_zip(update: Update, context: ContextTypes.DEFAULT_TYPE, passwords: list):
    user_id = str(update.effective_user.id)
    zip_path = f"temp_zip_{user_id}.zip"
    
    try:
        status_msg = await update.message.reply_text("📥 Zip ফাইল ডাউনলোড হচ্ছে...")
        
        zip_file_obj = await context.bot.get_file(context.user_data['zip'])
        await zip_file_obj.download_to_drive(zip_path)
        
        await status_msg.edit_text("🔍 ক্র্যাকিং শুরু হচ্ছে (এটি আপনার ফাইলের সাইজ এবং পাসওয়ার্ডের সংখ্যার উপর নির্ভর করবে)...")
        
        total = len(passwords)
        start_time = time.time()
        last_edit_time = start_time
        
        found_password = None
        checked = 0
        
        with pyzipper.AESZipFile(zip_path) as zf:
            if not zf.namelist():
                await update.message.reply_text("❌ Zip ফাইলটি সম্পূর্ণ খালি!")
                return
                
            first_file = zf.namelist()[0]
            
            for i, password in enumerate(passwords, 1):
                if context.user_data.get('cancel_requested'):
                    break
                    
                try:
                    zf.read(first_file, pwd=password.encode('utf-8'))
                    found_password = password
                    checked = i
                    break
                except RuntimeError as e:
                    pass
                except Exception:
                    pass
                
                checked = i
                
                if i % 100 == 0:
                    await asyncio.sleep(0.001)
                
                current_time = time.time()
                if current_time - last_edit_time > 3.0:
                    elapsed_time = current_time - start_time
                    speed = i / elapsed_time if elapsed_time > 0 else 0
                    try:
                        await status_msg.edit_text(
                            f"🔍 ক্র্যাকিং চলছে...\n\n"
                            f"📊 প্রগ্রেস: {i}/{total}\n"
                            f"⚡ স্পিড: {speed:.0f} পাসওয়ার্ড/সেকেন্ড"
                        )
                        last_edit_time = current_time
                    except:
                        pass
        
        elapsed_time = time.time() - start_time
        
        if context.user_data.get('cancel_requested'):
            await update.message.reply_text("❌ কাজ আপনার নির্দেশে বাতিল করা হয়েছে।")
        elif found_password:
            await update.message.reply_text(
                f"✅ <b>সফলভাবে পাসওয়ার্ড পাওয়া গেছে!</b> 🎉\n\n"
                f"🔑 <b>পাসওয়ার্ড:</b> <code>{found_password}</code>\n"
                f"📊 <b>চেষ্টা করা হয়েছে:</b> {checked}/{total}\n"
                f"⚡ <b>গড় স্পিড:</b> {checked/elapsed_time:.0f} p/s\n"
                f"⏱️ <b>সময় লেগেছে:</b> {elapsed_time:.1f} সেকেন্ড",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                f"❌ <b>পাসওয়ার্ড লিস্টে সঠিক পাসওয়ার্ড পাওয়া যায়নি!</b>\n\n"
                f"📊 <b>মোট চেষ্টা:</b> {total}\n"
                f"⚡ <b>গড় স্পিড:</b> {total/elapsed_time:.0f} p/s\n"
                f"⏱️ <b>সময় লেগেছে:</b> {elapsed_time:.1f} সেকেন্ড\n"
                f"💡 অন্য কোনো পাসওয়ার্ড লিস্ট দিয়ে আবার চেষ্টা করুন।",
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ ক্র্যাকিং এর সময় ত্রুটি হয়েছে: {str(e)}")
    finally:
        context.user_data['processing'] = False
        context.user_data['cancel_requested'] = False
        if 'zip' in context.user_data: del context.user_data['zip']
        if 'password' in context.user_data: del context.user_data['password']
        
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass

# বট আপডেট ফাংশন
async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        status_msg = await update.message.reply_text("⏳ বট আপডেট হচ্ছে...")
        
        new_file = await context.bot.get_file(update.message.document.file_id)
        new_file_path = "update_bot.py"
        await new_file.download_to_drive(new_file_path)
        
        current_file = "bot.py"
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        
        if os.path.exists(current_file):
            shutil.copy(current_file, backup_name)
        
        shutil.move(new_file_path, current_file)
        
        await status_msg.edit_text(
            "✅ <b>বট আপডেট সফল হয়েছে!</b>\n\n"
            f"📁 ব্যাকআপ: {backup_name}\n"
            "🔄 বট পুনরায় চালু হচ্ছে...",
            parse_mode=ParseMode.HTML
        )
        
        os.execl(sys.executable, sys.executable, current_file)
        
    except Exception as e:
        await update.message.reply_text(f"❌ আপডেট করতে সমস্যা: {str(e)}")

# এরর হ্যান্ডলার
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error caused by update {update}: {context.error}")

# মেইন ফাংশন
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.add_error_handler(error_handler)
    
    print("🤖 প্রো জিপ ক্র্যাকার বট চালু হচ্ছে...")
    print("✅ বট সফলভাবে চালু হয়েছে!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()