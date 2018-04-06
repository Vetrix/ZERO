import errno
import os
import sys
import tempfile
from argparse import ArgumentParser
from urllib.parse import quote
from kbbi import KBBI
import requests
from flask import Flask, request, abort

from linebot import (
	LineBotApi, WebhookHandler
)
from linebot.exceptions import (
	InvalidSignatureError
)
from linebot.models import (
	MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, SourceGroup, SourceRoom,
	TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
	ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URITemplateAction,
	PostbackTemplateAction, DatetimePickerTemplateAction,
	CarouselTemplate, CarouselColumn, PostbackEvent,
	StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
	ImageMessage, VideoMessage, AudioMessage, FileMessage,
	UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent
)

app = Flask(__name__)

line_bot_api = LineBotApi('CQcg1+DqDmLr8bouXAsuoSm5vuwB2DzDXpWc/KGUlxzhq9MSWbk9gRFbanmFTbv9wwW8psPOrrg+mHtOkp1l+CTlqVeoUWwWfo54lNh16CcqH7wmQQHT+KnkNataGXez6nNY8YlahgO7piAAKqfjLgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c116ac1004040f97a62aa9c3503d52d9')


@app.route("/callback", methods=['POST'])
def callback():
	# get X-Line-Signature header value
	signature = request.headers['X-Line-Signature']

	# get request body as text
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)

	# handle webhook body
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)

	return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

	text=event.message.text
	
	def split1(text):
		return text.split('/wolfram ', 1)[-1]

	def split2(text):
		return text.split('/kbbi ', 1)[-1]
		
	def split3(text):
		return text.split('/echo ', 1)[-1]
		
	def wolfram(query):
		wolfram_appid = ('83L4JP-TWUV8VV7J7')

		url = 'https://api.wolframalpha.com/v2/result?i={}&appid={}'
		return requests.get(url.format(quote(query), wolfram_appid)).text

	def find_kbbi(keyword, ex=False):

		try:
			entry = KBBI(keyword)
		except KBBI.TidakDitemukan as e:
			result = str(e)
		else:
			result = "Definisi {}:\n".format(keyword)
			if ex:
				result += '\n'.join(entry.arti_contoh)
			else:
				result += str(entry)
		return result
		
	if text == '/help':
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage('I will be here for you'))
	
	elif text == '/leave':
		if isinstance(event.source, SourceGroup):
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('I am leaving the group...'))
			line_bot_api.leave_group(event.source.group_id)
		
		elif isinstance(event.source, SourceRoom):
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('I am leaving the group...'))
			line_bot_api.leave_room(event.source.room_id)
			
		else:
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('>_< cannot do...'))
	
	elif text == '/about':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Hello, my name is Reika \n"
								"Nice to meet you... \n"
								"source code: https://github.com/Vetrix/ZERO"))
	
	elif text == '/search image':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Try this up \n"
								"https://reverse.photos/"))
	
	elif text == '/profile':
		if isinstance(event.source, SourceGroup):
			try:
				profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
				result = ("Display name: " + profile.display_name + "\n" +
						  "Profile picture: " + profile.picture_url + "\n" +
						  "User_ID: " + profile.user_id)
			except LineBotApiError:
				pass	
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(result))
			
		
		elif isinstance(event.source, SourceRoom):
			try:
				profile = line_bot_api.get_room_member_profile(event.source.room_id, event.source.user_id)
				result = ("Display name: " + profile.display_name + "\n" +
						  "Profile picture: " + profile.picture_url + "\n" +
						  "User_ID: " + profile.user_id)
			except LineBotApiError:
				pass	
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(result))
			
				
		else:
			try:
				profile = line_bot_api.get_profile(event.source.user_id)
				result = ("Display name: " + profile.display_name + "\n" +
						  "Profile picture: " + profile.picture_url + "\n" +
						  "User_ID: " + profile.user_id)
				if profile.status_message:
					result += "\n" + "Status message: " + profile.status_message
			except LineBotApiError:
				pass
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(result))
	
	elif text=='/kbbi':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /kbbi {input}'))
	
	elif text=='/wolfram':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /wolfram {input}'))
	
	elif text == 'confirm':
		confirm_template = ConfirmTemplate(text='Do it?', actions=[
			MessageTemplateAction(label='Yes', text='Yes!'),
			MessageTemplateAction(label='No', text='No!'),
			])
		template_message = TemplateSendMessage(
			alt_text='Confirm alt text', template=confirm_template)
		line_bot_api.reply_message(event.reply_token, template_message)
	
	elif text=='test':
		line_bot_api.reply_message(
				event.reply_token,
				ImageSendMessage(original_content_url='https://www.dropbox.com/s/arbyj22nph41283/original.jpg',
                                  preview_image_url='https://www.dropbox.com/s/ipc4v29mh1hyvs9/preview.jpg?dl=0'))
	
	elif text[0:].lower().strip().startswith('/wolfram '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(wolfram(split1(text))))

	elif text[0:].lower().strip().startswith('/kbbi '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(find_kbbi(split2(text))))	
			
	elif text[0:].lower().strip().startswith('/echo ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(split3(text)))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)