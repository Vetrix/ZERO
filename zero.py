import os
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
		
	elif text == '/profile':
		try:
			profile = line_bot_api.get_profile(event.source.user_id)
			print(profile.display_name)
			print(profile.user_id)
			print(profile.picture_url)
			print(profile.status_message)
		except LineBotApiError as e:
			# error handle
			pass
			
	else:
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(text))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)