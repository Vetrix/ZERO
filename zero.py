import os
from urllib.parse import quote
import requests
from flask import Flask, request, abort

from linebot import (
	LineBotApi, WebhookHandler
)
from linebot.exceptions import (
	InvalidSignatureError
)
from linebot.models import (
	MessageEvent, TextMessage, TextSendMessage, SourceGroup, SourceRoom
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
	a,b = text.split(" ")

	def wolfram(query):
		wolfram_appid = ('83L4JP-TWUV8VV7J7')

		url = 'https://api.wolframalpha.com/v2/result?i={}&appid={}'
		return requests.get(url.format(quote(query), wolfram_appid))
	
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
	else:
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(text))
			
	if text[1:].lower().strip().startswith('wolfram'):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(wolfram(b)))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)