import errno, os, sys, tempfile, requests, json, wikipedia, pafy, tweepy
from gtts import gTTS
from imdb import IMDb
from argparse import ArgumentParser
from urllib.parse import quote
from kbbi import KBBI
from urbandictionary_top import udtop
from googletrans import Translator
from flask import Flask, request, abort
from bs4 import BeautifulSoup as bs

from linebot import (
	LineBotApi, WebhookHandler
)
from linebot.exceptions import (
	InvalidSignatureError, LineBotApiError
)
from linebot.models import *

translator = Translator()
wiki_settings = {}
save_file = {}

app = Flask(__name__)

line_bot_api = LineBotApi('CQcg1+DqDmLr8bouXAsuoSm5vuwB2DzDXpWc/KGUlxzhq9MSWbk9gRFbanmFTbv9wwW8psPOrrg+mHtOkp1l+CTlqVeoUWwWfo54lNh16CcqH7wmQQHT+KnkNataGXez6nNY8YlahgO7piAAKqfjLgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c116ac1004040f97a62aa9c3503d52d9')

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
	
# function for create tmp dir for download content
def make_static_tmp_dir():
	try:
		os.makedirs(static_tmp_path)
	except OSError as exc:
		if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
			pass
		else:
			raise

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
	except LineBotApiError as e:
		print("Got exception from LINE Messaging API: %s\n" % e.message)
		for m in e.error.details:
			print("  %s: %s" % (m.property, m.message))
		print("\n")
	except InvalidSignatureError:
		abort(400)

	return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):

	text=event.message.text
	
	if isinstance(event.source, SourceGroup):
		subject = line_bot_api.get_group_member_profile(event.source.group_id,
														event.source.user_id)
		set_id = event.source.group_id
	elif isinstance(event.source, SourceRoom):
		subject = line_bot_api.get_room_member_profile(event.source.room_id,
                                                   event.source.user_id)
		set_id = event.source.room_id
	else:
		subject = line_bot_api.get_profile(event.source.user_id)
		set_id = event.source.user_id

	### should get new api key
	"""	
	def shorten(url):
		api_key = 'AIzaSyB2JuzKCAquSRSeO9eiY6iNE9RMoZXbrjo'
		req_url = 'https://www.googleapis.com/urlshortener/v1/url?key=' + api_key
		payload = {'longUrl': url}
		headers = {'content-type': 'application/json'}
		r = requests.post(req_url, data=json.dumps(payload), headers=headers)
		resp = json.loads(r.text)
		return resp['id']		
	"""


	def prof():
		result = ("Display name: " + subject.display_name + "\n"
				  "User_ID: " + subject.user_id)
		if subject.picture_url :
			result += "\nProfile picture: " + subject.picture_url
		try:
			profile = line_bot_api.get_profile(event.source.user_id)
			if profile.status_message:
				result += "\n" + "Status message: " + profile.status_message
		except LineBotApiError:
			pass
		
		return(result)
	
	def split(text):
		return text.split(' ', 1)[-1]	


	def ytdl(url):
		video = pafy.new(url)
		best = video.getbest(preftype="mp4")
		bestaudio = video.getbestaudio(preftype="m4a")
		return ("Title: " + video.title +"\n"
				"Views: " + str(video.viewcount) + "\n"
				"Likes: " + str(video.likes) + "\n"
				"Dislikes: " + str(video.dislikes) + "\n"
				"Duration: " + video.duration + "\n"
				"Videodl: "+ best.url + "\n"
				"Audiodl: " + bestaudio.url)
	
	def force_safe(text):
		return text.replace('http','https',1)
	
	def fdetect(url) :
		http_url = 'https://api-us.faceplusplus.com/facepp/v3/detect'
		key = "lM4feUDrJJYyKm8s4WvmxgWlVpZE0iNw"
		secret = "Y5L_l2a87UAtKeFzL-FD8K3C5OwtAbfA"
		attributes="age,gender,ethnicity,beauty"
		
		#add emotion later in atributes
		
		resp = requests.post(http_url,
			data = { 
					'api_key': key,
					'api_secret': secret,
					'image_url': url,
					'return_attributes': attributes}
		)

		r = resp.json()
	
		if (len(r) == 3 ) :
			return ("Face not detected")
			
		dict1 = r['faces']
		if ((len(dict1) > 1) or (len(dict1) < 1)):
			return ("Please send picture with one face only")
		else:
			dict2 = dict1[0]['attributes']['gender']['value']
			dict3 = dict1[0]['attributes']['age']['value']
			dict4 = dict1[0]['attributes']['beauty']
			
			if (dict2 == 'Male') :
				dict4 = dict4['male_score']
			else:
				dict4 = dict4['female_score']
			
			dict5 = dict1[0]['attributes']['ethnicity']['value']
			
			#dict6 = dict1[0]['attributes']['emotion'] add emotion later
			
			return("Gender		: " + str(dict2) + "\n" +
					"Age				: " + str(dict3) + "\n" +
					"Beauty		: " + str(round(dict4, 2)) + "\n" +
					"Ethnicity	: " + str(dict5))
	
	def pt(city) :
		url = "https://time.siswadi.com/pray/?address={}"
		r = requests.get(url.format(city))

		data = r.json()
		dict1 = data['data']
		dict2 = data['location']
		dict3 = data['time']
		
		return (str(dict2['address']) + " prayer time " + str(dict3['date']) + "\n"
				"Fajr				: " + str(dict1['Fajr']) + "\n"
				"Sunrise	: " + str(dict1['Sunrise']) + "\n"
				"Dhuhr		: " + str(dict1['Dhuhr']) + "\n"
				"Asr				: " + str(dict1['Asr']) + "\n"
				"Maghrib	: " + str(dict1['Maghrib']) + "\n"
				"Isha				: " + str(dict1['Isha']))
	
	def twt(query):
		query = query.split('/', 5)[-1]
		query = query.split('/')[0]
		
		access_token = ('1084471906248445952-3aN04mwGh4Y3VKUXFVV1YIfiC6WPVB')
		access_token_secret = ('XsRaIf04Te3AldW5mRFz1kgaT1ZyyXWNaDOlK1GKivDUE')
		consumer_key = ('u1CBf3TrAu1BDp7qsAH2GbSwl')
		consumer_secret = ('P2vMIp4vSuM7Q1PdscyjAE8eMcoROCIBY5mZ4H5WHQXPxWbcwy')
		
		auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
		auth.set_access_token(access_token, access_token_secret)

		api = tweepy.API(auth)
		data1 = api.get_status(query).user.name
		data2 = api.get_status(query).text
		
		return (data1 + ' on Twitter:\n' + data2)
	
	def ig(username) :
		url = "https://www.instagram.com/{}"
		r = requests.get(url.format(username))
		if r.status_code == 404:
			return ("Unavailable")
		html = r.text
		jsondata = html.split("window._sharedData = ")[1].split(";</script>")[0]
		data = json.loads(jsondata)
		
		try:
			dict1 = data['entry_data']['ProfilePage'][0]['graphql']['user']

			return ("User : @"+ dict1['username'] + "\n" + "Name : " + dict1['full_name'] + "\n" + 
					"Following : " + str(dict1['edge_follow']['count']) + "\n" +
					"Followers : " + str(dict1['edge_followed_by']['count']) + "\n" +
					"Bio : " + dict1['biography'])
					
		except KeyError:
			try:
				data = html.split("""og:description" content=\"""")[1].split("""" />""")[0]
				data = bs(data, "html.parser").text
				return (data)
			except IndexError:
				return ("Unavailable")
		
	def igs(username) :
		url = "https://www.instagram.com/{}"
		r = requests.get(url.format(username))
		html = r.text
		jsondata = html.split("window._sharedData = ")[1].split(";</script>")[0]
			
		try:
			data = json.loads(jsondata)
			dict1 = data['entry_data']['ProfilePage'][0]['graphql']['user']

			return (dict1['profile_pic_url_hd'])
		except KeyError:
			try:
				data = html.split("""og:image" content=\"""")[1].split("""" />""")[0]
				return (data)
			except IndexError:
				return ("Unavailable")
		
	def picg(uri) :
		url = split(uri)
		r = requests.get(url)
		if r.status_code == 404:
			return ("Unavailable")
		
		html = r.text
		
		try:
			jsondata = html.split("""<script type="application/ld+json">""")[1].split("</script>")[0]
			
			data = json.loads(jsondata)
			try:
				dict1 = data['caption']
			except KeyError:
				dict1 = "no caption post."
			try:
				data4 = "@" + data['contentLocation']['name']
			except KeyError:
				data4 = "no location included."	

		except IndexError:
			jsondata = html.split("""<script type="text/javascript">window._sharedData =""")[1].split(";</script>")[0]

			data = json.loads(jsondata)
			try:
				dict1 = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_media_to_caption']['edges'][0]['node']['text']
			except KeyError:
				dict1 = "no caption post."
			try:
				data4 = "@" + data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['location']['name']
			except (TypeError, KeyError):
				data4 = "no location included."	
				
		count = len(str(dict1))
		if (count > 1900):
			dict1 = dict1[:1900]
			if not dict1.endswith(' '):
				dict1 = dict1[:dict1.rfind(' ')+1]
			dict1 = str(dict1) + "。。。 Caption trimmed."
		
		data2 = html.split("""og:title" content=\"""")[1].split(":")[0]
		
		data2 = bs(data2, "html.parser").text
		data3 = bs(dict1, "html.parser").text
		data4 = bs(data4, "html.parser").text
		
		return(data2 + " : \n" + data3 + "\n" + data4)
		
	def picgs(query) :
		number = 0
		
		if query[0:].lower().strip().startswith('p'):
			number = query.split(' ', 1)[0]
			number = number.split('p', 1)[-1]
			query = query.split(' ', 1)[1]
		
		number = int(number)
		if number != 0 :
			number = number -1
		
		url = query
		r = requests.get(url)
		html = r.text
		jsondata = html.split("""<script type="text/javascript">window._sharedData =""")[1].split(";</script>")[0]
		data = json.loads(jsondata)

		dict1 = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
		try:
			dict1= dict1['edge_sidecar_to_children']['edges'][number]['node']['display_url']
		except KeyError:
			dict1= dict1['display_url']
			
		return (dict1)
	
	def vigs(query) :
		number = 0
		
		if query[0:].lower().strip().startswith('p'):
			number = query.split(' ', 1)[0]
			number = number.split('p', 1)[-1]
			query = query.split(' ', 1)[1]
		
		number = int(number)
		if number != 0 :
			number = number -1
		
		url = query
		r = requests.get(url)
		html = r.text
		jsondata = html.split("""<script type="text/javascript">window._sharedData =""")[1].split(";</script>")[0]
		data = json.loads(jsondata)

		dict1 = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
		try:
			dict1= dict1['edge_sidecar_to_children']['edges'][number]['node']['video_url']
		except KeyError:
			dict1= dict1['video_url']
			
		return (dict1)	
	
	def tts(word):
		la ='en'
		ext = 'mp3'
		
		if word[0:].lower().strip().startswith('la='):
			la = word.split(', ', 1)[0]
			la = la.split('la=', 1)[-1]
			word = word.split(', ', 1)[1]
			
		speech = gTTS(text=word, lang=la)
		with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='mp3-', delete=False) as tf:
			speech.write_to_fp(tf)
		tempfile_path = tf.name
		
		dist_path = tempfile_path + '.' + ext
		dist_name = os.path.basename(dist_path)
		os.rename(tempfile_path, dist_path)
		
		url = request.host_url + os.path.join('static', 'tmp', dist_name)
		return force_safe(url)

	def mreview(movie) :	
		ia = IMDb()
		movies = ia.search_movie(movie)
		
		ID = movies[0].movieID
		data = ia.get_movie(ID)
		
		#data.infoset2keys (get all info)
		
		cast = ''
		i = 0
		while (i != 4) :
			cast = cast + "\n" + str(data['cast'][i]) + " as " +  str(data['cast'][i].notes)
			i += 1
		
		duration = str(data['runtimes']).split("'")[1]
		
		year = str(data['year'])
		
		plot = str(data['plot'][0].split("::")[0])
		
		rate = str(data['rating'])
		
		return ("Title						: " + str(movies[0]) + "\n"
				"Rating				: " + rate + "\n"
				"Duration			: " + duration + " minutes\n"
				"Year						: " + year + "\n"
				"Main Casts 	: " + cast + "\n"
				"Plot : \n" + str(plot))
				
	def imdbpic(movie) :
		ia = IMDb()
		movies = ia.search_movie(movie)
		
		ID = movies[0].movieID
		data = ia.get_movie(ID)
		
		return (str(data['cover url']))
	
	def ox(keyword):
		oxdict_appid = ('c4390cc1')
		oxdict_key = ('ebb4414c6c7e422dd7df459b48bd1529')
		
		word = quote(keyword)
		url = ('https://od-api.oxforddictionaries.com:443/api/v2/entries/en/{}'.format(word))
		req = requests.get(url, headers={'app_id': oxdict_appid, 'app_key': oxdict_key})
		if "No entry available" in req.text:
			return 'No entry available for "{}".'.format(word)

		req = req.json()
		result = ''
		i = 0
		for each_result in req['results']:
			for each_lexEntry in each_result['lexicalEntries']:
				for each_entry in each_lexEntry['entries']:
					for each_sense in each_entry['senses']:
						if 'crossReferenceMarkers' in each_sense:
							search = 'crossReferenceMarkers'
						else:
							search = 'definitions'
						for each_def in each_sense[search]:
							i += 1
							result += '\n{}. {}'.format(i, each_def)

		if i == 1:
			result = 'Definition of {}:\n'.format(keyword) + result[4:]
		else:
			result = 'Definitions of {}:'.format(keyword) + result
		return result

	
	def wolfram(query):
		wolfram_appid = ('83L4JP-TWUV8VV7J7')

		url = 'https://api.wolframalpha.com/v2/result?i={}&appid={}'
		return requests.get(url.format(quote(query), wolfram_appid)).text
		
	def wolframs(query):
		wolfram_appid = ('83L4JP-TWUV8VV7J7')

		url = 'https://api.wolframalpha.com/v2/simple?i={}&appid={}'
		return url.format(quote(query), wolfram_appid)
	
	def ytskip(query):
		time = '0s'
		url = 'https://youtube.com/watch?v={}&t={}'
		
		if query[0:].lower().strip().startswith('t='):
			time = query.split(', ', 1)[0]
			time = time.split('t=', 1)[-1]
			query = query.split(', ', 1)[1]
			
		query = query.split('/', 3)[-1]
		if query[0:].lower().strip().startswith('watch'):
			query = query.split('v=', 1)[1]
			query = query.split('/')[0]
		
		result = url.format(quote(query), time)
		if ((len(result)) < 44) or ((len(result)) > 54):
			result = "Wrong format"
		
		return(result)
	
	def trans(word):
		sc = 'en'
		to = 'id'
		
		if word[0:].lower().strip().startswith('sc='):
			sc = word.split(', ', 1)[0]
			sc = sc.split('sc=', 1)[-1]
			word = word.split(', ', 1)[1]
	
		if word[0:].lower().strip().startswith('to='):
			to = word.split(', ', 1)[0]
			to = to.split('to=', 1)[-1]
			word = word.split(', ', 1)[1]
			
		if word[0:].lower().strip().startswith('sc='):
			sc = word.split(', ', 1)[0]
			sc = sc.split('sc=', 1)[-1]
			word = word.split(', ', 1)[1]
			
		return translator.translate(word, src=sc, dest=to).text
		
	def wiki_get(keyword, set_id, trim=True):
    
		try:
			wikipedia.set_lang(wiki_settings[set_id])
		except KeyError:
			wikipedia.set_lang('en')

		try:
			result = wikipedia.summary(keyword)

		except wikipedia.exceptions.DisambiguationError:
			articles = wikipedia.search(keyword)
			result = "{} disambiguation:".format(keyword)
			for item in articles:
				result += "\n{}".format(item)
		except wikipedia.exceptions.PageError:
			result = "{} not found!".format(keyword)

		else:
			if trim:
				result = result[:2000]
				if not result.endswith('.'):
					result = result[:result.rfind('.')+1]
		return result
		
	def wiki_lang(lang, set_id):
    
		langs_dict = wikipedia.languages()
		if lang in langs_dict.keys():
			wiki_settings[set_id] = lang
			return ("Language has been changed to {} successfully."
					.format(langs_dict[lang]))

		return ("{} not available!\n"
				"See meta.wikimedia.org/wiki/List_of_Wikipedias for "
				"a list of available languages, and use the prefix "
				"in the Wiki column to set the language."
				.format(lang))	
	
	def find_kbbi(keyword, ex=True):

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
	
	def urban(keyword, ex=True):
		
		try:
			entry = udtop(keyword)
		except (TypeError, AttributeError, udtop.TermNotFound) :
			result = "{} definition not found in urbandictionary.".format(keyword)
		else:
			result = "{} definition:\n".format(keyword)
			if ex:
				result += str(entry)
			else:
				result += entry.definition
		return result
	
	if text == '/help':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("I will be here for you"))
				
	
	elif text == '/leave':
		if isinstance(event.source, SourceGroup):
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('I am leaving the group...'))
			line_bot_api.leave_group(event.source.group_id)
		
		elif isinstance(event.source, SourceRoom):
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('I am leaving the room...'))
			line_bot_api.leave_room(event.source.room_id)
			
		else:
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(">_< can't do..."))
	
	elif text == '/about':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Hello, my name is Itsumi \n"
								"Nice to meet you... \n"
								"Creator: https://github.com/Vetrix"))
	
	elif text == '/cmd':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Without parameters: \n"
								"/about, /help, /profile, /leave,\n"
								"/confirm, /buttons, /on, /off,\n"
								"/image_carousel, /lang\n"
								"/flex\n"
								
								"\n"
								"With parameters:\n"
								"/echo, /kbbi, /twt, /wolfram,\n"
								"/wolframs, /yt, /ytskip,\n"
								"/trans, /wiki, /wikilang, /urban,\n"
								"/ox, /tts, /stalkig, /photoig,\n"
								"/videoig, /imdb, /pt, /fdetect"))
	
	elif text == '/lang':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Language for translation see here \n"
								"https://github.com/Vetrix/ZERO/blob/master/Lang.txt"))
	
	elif text == '/profile':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(prof()))
				
	elif text == '/on':
		save_file[set_id] = True
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Save file on"))
				
	elif text == '/off':
		save_file[set_id] = False
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Save file off"))
	
	if text == '/echo':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Copy the message you send\n"
								"command /echo {word}\n"
								"sample : /echo echo"))
	
	elif text == '/kbbi':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get meaning of a word from https://kbbi.kemdikbud.go.id/ \n"
								"command /kbbi {word}\n"
								"sample : /kbbi gim"))
	
	elif text == '/urban':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get meaning of a word from https://www.urbandictionary.com/ \n"
								"command /urban {word}\n"
								"sample : /urban 1437"))
	
	elif text == '/ox':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get meaning of a word from https://www.oxforddictionaries.com/ \n"
								"command /ox {word}\n"
								"sample : /ox chatbot"))
								
	elif text == '/imdb':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get movie review from https://www.imdb.com/ \n"
								"command /imdb {movie}\n"
								"sample : /imdb the godfather"))
								
	elif text == '/fdetect':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get face detection of photo url \n"
								"command /fdetect {url}\n"
								"sample : /fdetect https://upload.wikimedia.org/wikipedia/commons/b/be/Pygoscelis_papua.jpg"))
	
	elif text == '/wolfram':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("use https://www.wolframalpha.com/ features, and give the result "
								"in simple text \n"
								"command /wolfram {input}\n"
								"sample : /wolfram 1+1"))
				
	elif text == '/wolframs':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("use https://www.wolframalpha.com/ features, and give the result "
								"in image \n"
								"command /wolframs {input}\n"
								"sample : /wolframs 1+1"))
	
	elif text == '/yt':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get title, views, likes, etc. from youtube video url\n"
								"command /yt {url}\n"
								"sample : /yt https://youtu.be/PHgc8Q6qTjc"))
								
	elif text == '/ytskip':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("skip youtube video to certain timestamp\n"
								"command /ytskip t={time}, {url}\n"
								"sample : /ytskip t=1m0s, https://youtu.be/PHgc8Q6qTjc"))
	
	elif text == '/stalkig':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get simple description of instagram account and profile picture\n"
								"command /stalkig {username}\n"
								"sample : /stalkig instagram"))
				
	elif text == '/photoig':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get photo and description of instagram post\n"
								"command /photoig p{page no.} {link}\n"
								"sample : /photoig p2 https://www.instagram.com/p/BwvIsCpgTr1/"))
				
	elif text == '/videoig':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get video and description of instagram post\n"
								"command /videoig p{page no.} {link}\n"
								"sample : /videoig p2 https://www.instagram.com/p/BuwNBs_nLte/"))
	
	elif text == '/twt':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get twitter status (tweet) from url\n"
								"command /twt {url}\n"
								"sample : /twt https://twitter.com/elonmusk/status/1119414361984884737"))
	
	elif text == '/trans':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get translation from https://translate.google.com/ \n"
								"language code can be seen in /lang command \n"
								"command /trans sc={language code}, to={language code}, {text}\n"
								"sample : /trans sc=en, to=id, ubiquitous"))
				
	elif text == '/tts':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get audio file about how a word pronounced in a language \n"
								"language code can be seen in /lang command \n"
								"command /tts la={language code}, {text}\n"
								"sample : /tts la=en, uh she up"))
	
	elif text == '/wiki':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get https://www.wikipedia.org/ description of something \n"
								"command /wiki {text}\n"
								"sample : /wiki penguin"))
				
	elif text == '/wikilang':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("change the language of wikipedia description \n"
								"language code can be seen in /lang command \n"
								"command /wikilang {language code}\n"
								"sample : /wikilang id"))
								
	elif text == '/pt':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("get prayer time of your city \n"
								"command /pt {city}\n"
								"sample : /pt los angeles"))
	
	elif text == '/confirm':
		confirm_template = ConfirmTemplate(text='Do it?', actions=[
			MessageTemplateAction(label='Yes', text='Yes!'),
			MessageTemplateAction(label='No', text='No!'),
			])
		template_message = TemplateSendMessage(
			alt_text='Confirm alt text', template=confirm_template)
		line_bot_api.reply_message(event.reply_token, template_message)
	
	elif text == '/buttons':
		buttons_template = ButtonsTemplate(
			title='My buttons sample', text='Hello, my buttons', actions=[
				URITemplateAction(
					label='Go to line.me', uri='https://line.me'),
				PostbackTemplateAction(label='ping', data='ping'),
				PostbackTemplateAction(
					label='ping with text', data='ping',
					text='ping'),
				MessageTemplateAction(label='Translate Rice', text='米')
			])
		template_message = TemplateSendMessage(
			alt_text='Buttons alt text', template=buttons_template)
		line_bot_api.reply_message(event.reply_token, template_message)

	elif text == '/flex':
		bubble = BubbleContainer(
			direction='ltr',
			hero=ImageComponent(
				url='https://globalassets.starbucks.com/assets/71d2dc1df70c41ca91e8aae0b3fd3e36.jpg',
				size='full',
				aspect_ratio='4:3',
				aspect_mode='cover',
				action=URIAction(uri='https://github.com/vetrix/zero', label='label')
			),
			body=BoxComponent(
				layout='vertical',
				contents=[
					# title
					TextComponent(text='Coffee Shop', weight='bold', size='xl'),
					# review
					BoxComponent(
						layout='baseline',
						margin='md',
						contents=[
							IconComponent(size='sm', url='https://cdn2.iconfinder.com/data/icons/default-1/100/.svg-4-512.png'),
							IconComponent(size='sm', url='https://cdn2.iconfinder.com/data/icons/default-1/100/.svg-4-512.png'),
							IconComponent(size='sm', url='https://cdn2.iconfinder.com/data/icons/default-1/100/.svg-4-512.png'),
							IconComponent(size='sm', url='https://cdn2.iconfinder.com/data/icons/default-1/100/.svg-4-512.png'),
							IconComponent(size='sm', url='https://cdn2.iconfinder.com/data/icons/default-1/100/.svg-4-512.png'),
							TextComponent(text='5.0', size='sm', color='#FFFF00', margin='md',
										  flex=0)
						]
					),
					# info
					BoxComponent(
						layout='vertical',
						margin='lg',
						spacing='sm',
						contents=[
							BoxComponent(
								layout='baseline',
								spacing='sm',
								contents=[
									TextComponent(
										text='Place',
										color='#aaaaaa',
										size='sm',
										flex=1
									),
									TextComponent(
										text='Shinjuku, Tokyo',
										wrap=True,
										color='#666666',
										size='sm',
										flex=5
									)
								],
							),
							BoxComponent(
								layout='baseline',
								spacing='sm',
								contents=[
									TextComponent(
										text='Time',
										color='#aaaaaa',
										size='sm',
										flex=1
									),
									TextComponent(
										text="10:00 - 23:00",
										wrap=True,
										color='#666666',
										size='sm',
										flex=5,
									),
								],
							),
						],
					)
				],
			),
			footer=BoxComponent(
				layout='vertical',
				spacing='sm',
				contents=[
					# callAction, separator, websiteAction
					SpacerComponent(size='sm'),
					# callAction
					ButtonComponent(
						style='link',
						height='sm',
						action=URIAction(label='Americano', uri='tel:000000'),
					),
					# separator
					SeparatorComponent(),
					# websiteAction
					ButtonComponent(
						style='link',
						height='sm',
						action=URIAction(label='WEBSITE', uri="https://github.com/vetrix/zero")
					)
				]
			),
		)
		message = FlexSendMessage(alt_text="hello", contents=bubble)
		line_bot_api.reply_message(
			event.reply_token,
			message
		)
		
	elif text == '/image_carousel':
		image_carousel_template = ImageCarouselTemplate(columns=[
			ImageCarouselColumn(image_url='https://via.placeholder.com/1024x1024',
								action=DatetimePickerTemplateAction(label='datetime',
																	data='datetime_postback',
																	mode='datetime')),
			ImageCarouselColumn(image_url='https://via.placeholder.com/1024x1024',
								action=DatetimePickerTemplateAction(label='date',
																	data='date_postback',
																	mode='date'))
		])
		template_message = TemplateSendMessage(
			alt_text='ImageCarousel alt text', template=image_carousel_template)
		line_bot_api.reply_message(event.reply_token, template_message)
		
	elif text == '/imagemap':
		pass
		
	elif text[0:].lower().strip().startswith('/videoig '):
		line_bot_api.reply_message(
			event.reply_token, [
			TextSendMessage(picg(split(text))),
			TextSendMessage(vigs(split(text))),
			VideoSendMessage(original_content_url= vigs(split(text)),
							preview_image_url= picgs(split(text)))
			])
	
	elif text[0:].lower().strip().startswith('/photoig '):
		line_bot_api.reply_message(
			event.reply_token, [
			TextSendMessage(picg(split(text))),
			TextSendMessage(picgs(split(text))),
			ImageSendMessage(original_content_url= picgs(split(text)),
							preview_image_url= picgs(split(text)))
			])
	
	elif text[0:].lower().strip().startswith('/stalkig '):
		line_bot_api.reply_message(
			event.reply_token, [
			TextSendMessage(ig(split(text))),
			TextSendMessage(igs(split(text))),
			ImageSendMessage(original_content_url= igs(split(text)),
							preview_image_url= igs(split(text)))
			])
	
	elif text[0:].lower().strip().startswith('/twt '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(twt(split(text))))
	
	elif text[0:].lower().strip().startswith('/imdb '):
		line_bot_api.reply_message(
			event.reply_token, [
			TextSendMessage(mreview(split(text))),
			ImageSendMessage(original_content_url= imdbpic(split(text)),
							preview_image_url= imdbpic(split(text)))
			])
	
	elif text[0:].lower().strip().startswith('/yt '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(ytdl(split(text))))
			
	elif text[0:].lower().strip().startswith('/ytskip '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(ytskip(split(text))))
	
	elif text[0:].lower().strip().startswith('/wolfram '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(wolfram(split(text))))
			
	elif text[0:].lower().strip().startswith('/wolframs '):
		line_bot_api.reply_message(
			event.reply_token,
			ImageSendMessage(original_content_url= wolframs(split(text)),
								preview_image_url= wolframs(split(text))))

	elif text[0:].lower().strip().startswith('/kbbi '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(find_kbbi(split(text))))
			
	elif text[0:].lower().strip().startswith('/urban '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(urban(split(text))))
			
	elif text[0:].lower().strip().startswith('/ox '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(ox(split(text))))
			
	elif text[0:].lower().strip().startswith('/echo ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(split(text)))
			
	elif text[0:].lower().strip().startswith('/pt ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(pt(split(text))))
			
	elif text[0:].lower().strip().startswith('/fdetect ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(fdetect(split(text))))
			
	elif text[0:].lower().strip().startswith('/trans ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(trans(split(text))))
	
	elif text[0:].lower().strip().startswith('/wiki ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(wiki_get(split(text), set_id=set_id)))
			
	elif text[0:].lower().strip().startswith('/wikilang ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(wiki_lang(split(text), set_id=set_id)))
			
	elif text[0:].lower().strip().startswith('/test ') :
		line_bot_api.reply_message(
				event.reply_token,
				AudioSendMessage(original_content_url=(split(text)), duration=60000))
				
	elif text[0:].lower().strip().startswith('/tts ') :
		line_bot_api.reply_message(
				event.reply_token, [
				TextSendMessage(tts(split(text))),
				AudioSendMessage(original_content_url=tts(split(text)), duration=60000)
				])
			
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
	line_bot_api.reply_message(
		event.reply_token,
		LocationSendMessage(
			title=event.message.title, address=event.message.address,
			latitude=event.message.latitude, longitude=event.message.longitude
		)
	)

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
	line_bot_api.reply_message(
		event.reply_token,
		StickerSendMessage(
			package_id=event.message.package_id,
			sticker_id=event.message.sticker_id)
	)
	
# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
	if isinstance(event.source, SourceGroup):
		subject = line_bot_api.get_group_member_profile(event.source.group_id,
														event.source.user_id)
		set_id = event.source.group_id
	elif isinstance(event.source, SourceRoom):
		subject = line_bot_api.get_room_member_profile(event.source.room_id,
                                                   event.source.user_id)
		set_id = event.source.room_id
	else:
		subject = line_bot_api.get_profile(event.source.user_id)
		set_id = event.source.user_id
		
	try :
		if save_file[set_id] :
			if isinstance(event.message, ImageMessage):
				ext = 'jpg'
			elif isinstance(event.message, VideoMessage):
				ext = 'mp4'
			elif isinstance(event.message, AudioMessage):
				ext = 'm4a'
			else:
				return

			message_content = line_bot_api.get_message_content(event.message.id)
			with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
				for chunk in message_content.iter_content():
					tf.write(chunk)
				tempfile_path = tf.name

			dist_path = tempfile_path + '.' + ext
			dist_name = os.path.basename(dist_path)
			os.rename(tempfile_path, dist_path)

			line_bot_api.reply_message(
				event.reply_token, [
					TextSendMessage(text='Save content.'),
					TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
				])
	except KeyError:
		save_file[set_id] = False
	
@handler.add(MessageEvent, message=FileMessage)
def handle_file_message(event):
	if isinstance(event.source, SourceGroup):
		subject = line_bot_api.get_group_member_profile(event.source.group_id,
														event.source.user_id)
		set_id = event.source.group_id
	elif isinstance(event.source, SourceRoom):
		subject = line_bot_api.get_room_member_profile(event.source.room_id,
                                                   event.source.user_id)
		set_id = event.source.room_id
	else:
		subject = line_bot_api.get_profile(event.source.user_id)
		set_id = event.source.user_id
	
	try :
		if save_file[set_id] :
			message_content = line_bot_api.get_message_content(event.message.id)
			with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='file-', delete=False) as tf:
				for chunk in message_content.iter_content():
					tf.write(chunk)
				tempfile_path = tf.name
			
			dist_path = tempfile_path + '-' + event.message.file_name
			dist_name = os.path.basename(dist_path)
			os.rename(tempfile_path, dist_path)
			
			line_bot_api.reply_message(
				event.reply_token, [
					TextSendMessage(text='Save file.'),
					TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
				])
	except KeyError:
		save_file[set_id] = False
		
@handler.add(FollowEvent)
def handle_follow(event):
	line_bot_api.reply_message(
		event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow():
	app.logger.info("Got Unfollow event")


@handler.add(JoinEvent)
def handle_join(event):
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text='Hi, my name is Itsumi. Hope we can make some fun in this ' + event.source.type))
		
@handler.add(LeaveEvent)
def handle_leave():
	app.logger.info("Bye")


@handler.add(PostbackEvent)
def handle_postback(event):
	if event.postback.data == 'ping':
		line_bot_api.reply_message(
			event.reply_token, TextSendMessage(text='pong'))
	elif event.postback.data == 'datetime_postback':
		line_bot_api.reply_message(
			event.reply_token, TextSendMessage(text=event.postback.params['datetime']))
	elif event.postback.data == 'date_postback':
		line_bot_api.reply_message(
			event.reply_token, TextSendMessage(text=event.postback.params['date']))


@handler.add(BeaconEvent)
def handle_beacon(event):
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(
			text='Got beacon event. hwid={}, device_message(hex string)={}'.format(
				event.beacon.hwid, event.beacon.dm)))
	
if __name__ == "__main__":
	port = int(os.environ.get('PORT', 5000))
	make_static_tmp_dir()
	app.run(host='0.0.0.0', port=port)
