from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram import Update, ParseMode
from telegram.ext import (Updater,
						  PicklePersistence,
						  CommandHandler,
						  CallbackQueryHandler,
						  CallbackContext,
						  ConversationHandler)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ReplyKeyboardMarkup
import requests
import hashlib
import sqlite3
import re
from bs4 import BeautifulSoup

bot_token = '5415345086:AAFsaAWlJcgMd0Wii1Z8UgzpgSrfSZM1ZWw'
admin = 37087739

#############################################

EXPECT_STATUS, EXPECT_USERNAME, EXPECT_PASSWORD, EXPECT_SUBMIT, EXPECT_BACK, EXPECT_BUTTON_CLICK  = range(6)

def start(update: Update, context: CallbackContext):
	chat_id = update.effective_chat.id
	text = ('به ربات پرتال دانشجویی خوش آمدید 🌹')
	update.message.reply_text(text, reply_markup=main_keyboard)


def set_info_handler(update: Update, context: CallbackContext):
	username = context.user_data.get('username', 'تنظیم نشده است')
	password = context.user_data.get('password', 'تنظیم نشده است')
	text = (f'نام کاربری: {username}\n'
			f'رمز عبور: {password}\n\n'
			'لطفا یک گزینه را انتخاب نمایید')
	button = [  [InlineKeyboardButton('رمز عبور', callback_data='pass'),
				 InlineKeyboardButton('نام کاربری', callback_data='user')],
				[InlineKeyboardButton('ورود و دریافت نمرات', callback_data='login_portal')],
				[InlineKeyboardButton('بازگشت', callback_data='cancel')],
			]
	inline_keyboard = InlineKeyboardMarkup(button)
	update.message.reply_text(text, reply_markup=inline_keyboard)
	return EXPECT_BUTTON_CLICK

def button_click_handler(update: Update, context: CallbackContext):
	chat_id = update.effective_chat.id
	query = update.callback_query
	query.answer()
	query.delete_message()
	if query.data == 'login_portal':
		web_url = 'https://pooya.um.ac.ir/gateway/PuyaAuthenticate.php'
		resp = session.get(web_url, headers=headers)
		soup = BeautifulSoup(resp.content, 'html.parser')
		img_src = soup.find('img', id='secimg')['src']
		filename = 'C:/Users/Home/OneDrive/Desktop/captcha.png'
		capcha_src = 'https://pooya.um.ac.ir' + img_src[2:]
		context.user_data['captcha'] = capcha_src
		context.bot.send_photo(chat_id, photo=capcha_src)
		context.bot.send_message(chat_id, text='کد کپچا را وارد کنید', reply_markup=ForceReply())
		return EXPECT_SUBMIT
	elif query.data == 'user':
		context.bot.send_message(chat_id, text='نام کاربری خود را وارد کنید', reply_markup=ForceReply())
		return EXPECT_USERNAME
	elif query.data == 'pass':
		context.bot.send_message(chat_id, text='رمز عبور خود را وارد کنید', reply_markup=ForceReply())
		return EXPECT_PASSWORD
	elif query.data == 'cancel':
		query.answer('Opeartion canceled!')
		return ConversationHandler.END


def hash_password(text):
	password = hashlib.md5()
	password.update(text.encode('utf-8'))
	return password.hexdigest()


def login_portal(update: Update, context: CallbackContext):
	chat_id = update.effective_chat.id
	captcha = update.message.text
	USER = context.user_data['username']
	PASS = context.user_data['password']
	capcha_src = context.user_data['captcha']
	login_data = {  'UserPassword': hash_password(PASS),
					'pswdStatus': '',
					'UserID': USER,
					'DummyVar': '',
					'rand2': capcha_src[capcha_src.find('rand2=')+6:],
					'mysecpngco': captcha
				}
	req_url = 'https://pooya.um.ac.ir/gateway/UserInterim.php'
	resp = session.post(req_url, data=login_data) 
	if resp.status_code == 200:
		grade_list = session.get('https://pooya.um.ac.ir/educ/educfac/stuShowEducationalLogFromGradeList.php', headers=headers)
		soup = BeautifulSoup(grade_list.content, 'html.parser')
		data = [item.text.splitlines() for item in soup.find_all('tr', bgcolor="#E8E8FF")]
		mean = [item.text.splitlines() for item in soup.find_all('tr', bgcolor="#C4C4FF")][1][3]
		mark = '\n'.join([f'{i+1}) {row[2]}, {row[5]} ({row[8]})' for i, row in enumerate(data)])
		text = f'{mark}\nمعدل: {mean}'
		context.bot.send_message(chat_id, text)
	else:
		print('Login faild!')
	return ConversationHandler.END 


def set_password(update: Update, context: CallbackContext):
	context.user_data['password'] = update.message.text
	update.message.reply_text('رمز عبور با موفقیت ثبت شد', reply_markup=main_keyboard)
	return ConversationHandler.END


def set_username(update: Update, context: CallbackContext):
	context.user_data['username'] = update.message.text
	update.message.reply_text('نام کاربری با موفقیت ثبت شد', reply_markup=main_keyboard)
	return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
	update.message.reply_text('منوی اصلی', reply_markup=main_keyboard)
	return ConversationHandler.END

#############################################

if __name__ == '__main__':
	# Session
	session = requests.session()
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
	# Bot details
	updater = Updater(token=bot_token)
	updater.dispatcher.add_handler(CommandHandler('start', start))
	updater.dispatcher.add_handler(ConversationHandler(
		entry_points=[MessageHandler(Filters.regex('ورود به پرتال دانشجویی'), set_info_handler)],
		states={
			EXPECT_USERNAME: [MessageHandler(Filters.text, set_username)],
			EXPECT_PASSWORD: [MessageHandler(Filters.text, set_password)],
			EXPECT_SUBMIT: [MessageHandler(Filters.text, login_portal)],
			EXPECT_BUTTON_CLICK: [CallbackQueryHandler(button_click_handler)],
			EXPECT_BACK : [CallbackQueryHandler('cancel', start)]
		},
		fallbacks=[MessageHandler(Filters.regex('cancel'), cancel)],
	))
	buttons = [['ورود به پرتال دانشجویی']]
	main_buttons = [row[::-1] for row in buttons]
	main_keyboard = ReplyKeyboardMarkup(main_buttons, one_time_keyboard=True, resize_keyboard=True) 
	updater.start_polling()
	print('Bot started ..........')