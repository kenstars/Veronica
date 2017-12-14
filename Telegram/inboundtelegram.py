from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler,CallbackQueryHandler,InlineQueryHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineQueryResultArticle,InputTextMessageContent,InlineKeyboardMarkup
import gearman
import json
import re
import requests
from uuid import uuid4
config = json.load(open('config.json','r'))
AUTH_TOKEN = str(config['Telegram']['key'])

class first_bot:
    def __init__(self):
        self.TELEGRAM_URL = 'https://api.telegram.org/bot'+str(config['Telegram']['key'])+'/'
        print self.TELEGRAM_URL
        self.updater = Updater(token = AUTH_TOKEN )
        self.dispatcher = self.updater.dispatcher
        self.gm_client = gearman.GearmanClient(  [  config['gearmanip']+':'+str(config['gearmanport']) ] )
        logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level = logging.INFO )
        self.prevQuery = ''
    
    def run(self, bot_value, update_value):
        global bot
        global update
        bot = bot_value
        update = update_value
        received_InlineQuery = False
        if isinstance(update.message,dict):
            update = update.to_dict()
            print "update>>>>>", update
            ChatMsg = update['message']['text']
            custInfo = {'FirstName':update['from']['first_name'],"LastName":update['from']['last_name']}
            queryobj = {"customer_info":custInfo,"input_text":ChatMsg,"v":"20150910","confidence":0.5,"redis_id":str(update['from']['id']),"lang":'en',"channel":"telegram"}
            received_InlineQuery = True
        else:
            ChatMsg = update.message.text
            custInfo = {'FirstName':update.message['chat']['first_name'],"LastName":update.message['chat']['last_name']}
            queryobj = {"customer_info":custInfo,"input_text":ChatMsg,"v":"20150910","confidence":0.5,"uId":str(update.message.chat_id),"lang":'en',"channel":"telegram", "redis_id":"admin"}
        print queryobj
        completed_task = self.gm_client.submit_job(str(config["gearmanworker_veronica"]),json.dumps(queryobj))
        result = json.loads(completed_task.result)
        print "^-^"*30
        print result
        if completed_task.state == 'COMPLETE':
            answer_text = result['response']
            print result
            # answer_text = html2text.html2text(answer_text)
            answer_text = answer_text.replace('<br>','\n')
            answer_text = answer_text.replace('<p>','\t')
            answer_text = answer_text.replace('<div>','\t')
            answer_text = re.sub('\<.?\w+.?\>',' ',answer_text)
            searchedvalue = re.search('(?:http)(?:.*)(?:target)',answer_text)
            link =' '
            if searchedvalue:
                print searchedvalue.group()
                if 'http' in searchedvalue.group():
                    link = searchedvalue.group()
                    answer_text = answer_text.replace('Read More!','')
                    link = link.replace('target',' ')
                    link = link.replace('http:\//','http://')
            answer_text = re.sub('(?:\<)(?:.*)(?:\>)',link,answer_text)
            if not result['question_keywords']:
                if not received_InlineQuery:
                    CHAT_ID= update.message.chat_id
                    r = requests.post(self.TELEGRAM_URL + "sendMessage", data=dict(chat_id=CHAT_ID,text=answer_text.strip()))
                else:
                    print "CHECKPOINT !!! HERE I AM !!!"
                    print update['id']
                    if len(answer_text) >61:
                        title = answer_text[:60]+'...'
                    else:
                        title = answer_text
                    if len(answer_text) > 4000:
                        answer_text = answer_text[:4000]
                    results = [{'type': 'article', 
                                'title': title, 
                                'id': update['id']+'/0', 
                                'message_text': str(answer_text)}]

                    my_data = {
                                'inline_query_id': update['id'],
                                'results': json.dumps(results),
                            }
                    r = requests.post(self.TELEGRAM_URL + "answerInlineQuery", params=my_data)
            else:
                buttonlist = result['question_keywords']
                inlinekeyboard = []
                final_keyboard = []
                for each in buttonlist:
                    inlinekeyboard.append({'text':each,'callback_data':each})
                    if len(inlinekeyboard)>1:
                        final_keyboard.append(inlinekeyboard)
                        inlinekeyboard = []
                buttonvalues = json.dumps({'inline_keyboard':final_keyboard})
                print "\n\n\n"
                print answer_text
                print buttonvalues
                if not received_InlineQuery:
                    CHAT_ID= update.message.chat_id
                    r = requests.post(self.TELEGRAM_URL + "sendMessage", data=dict(chat_id=CHAT_ID,text=answer_text,reply_markup=buttonvalues))
                else:
                    print update['id']
                    answer_text = "This request requires advanced features currently not supported in inline queries within Telegram. Please visit us at @veronica_light_bot for Answers to your queries"
                    if len(answer_text) >61:
                        title = answer_text[:60]+'...'
                    else:
                        title = answer_text
                    results = [{'type': 'article', 
                                'title': title, 
                                'id': update['id']+'/0', 
                                'message_text':answer_text}]

                    my_data = {
                                'inline_query_id': update['id'],
                                'results': json.dumps(results),
                            }
                    r = requests.post(self.TELEGRAM_URL + "answerInlineQuery", params=my_data)
            print vars(r)

    def buttonMethod(self,bot_value,update_value):
        callBackquery = update_value.callback_query
        query = callBackquery.data
        messageID = callBackquery.message.message_id
        #The commented code , will remove the buttons after User clicks.
        # r = requests.post(self.TELEGRAM_URL + "editMessageReplyMarkup", data=dict(chat_id=callBackquery.message.chat.id,message_id=messageID,reply_markup=''))
        # print r
        new_update_value = callBackquery
        new_update_value.message.text = query
        self.run(bot_value,new_update_value)
    
    def inlineQuery(self,bot_value,update_value):
        query = update_value.inline_query.query
        CHAT_ID = bot_value.id
        print update_value.inline_query
        new_update_value = update_value.inline_query
        new_update_value.message = {}
        new_update_value.message['text'] = query.replace('$$','')
        new_update_value.message['chat_id'] = CHAT_ID
        if query.endswith('$$') and query!=self.prevQuery:
            self.prevQuery = query
            self.run(bot_value,new_update_value)

if __name__ == '__main__':
        telebot = first_bot()
        echo_handler = MessageHandler([Filters.text], telebot.run)
        telebot.dispatcher.add_handler(CallbackQueryHandler(telebot.buttonMethod))
        inline_caps_handler = InlineQueryHandler(telebot.inlineQuery)
        telebot.dispatcher.add_handler(inline_caps_handler)
        telebot.dispatcher.add_handler(echo_handler)
        telebot.updater.start_polling(poll_interval = 1.0)
        telebot.updater.idle()
