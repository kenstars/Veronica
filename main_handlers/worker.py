import gearman
import redis
import re
import datetime
import time
import json
import traceback
import re
import requests
from nltk import pos_tag
import spacy
import urllib
from time import time

WH_WORDS = ["what", "where", "when", "how" , "which", "how", "why", "whose", "who"]
MODAL_WORDS = ["can", "could", "will", "would", "shall", "should", "might", "may"]
SECOND_PERSON = ["you", "thou"]

class ChatHandler():
    def __init__(self):
        with open('config.json','r') as filename:
            self.config = json.load(filename)
        self.gm_worker = gearman.GearmanWorker([ str(self.config["gearmanip"]) +":"+ str(self.config["gearmanport"]) ])
        self.gm_client = gearman.GearmanClient([ str(self.config["gearmanip"]) +":"+ str(self.config["gearmanport"]) ])
        self.gm_worker.register_task(str(self.config["chat_worker"]), self.userQuery)
        self.redis_obj = redis.StrictRedis(host = 'localhost', port = 6379, db = 1)
        self.ttl = 88000
        # self.nlp = spacy.load('en')
        print "initialising complete"
        
    def findQueryType(self, query):
        payload = dict(text = query)
        response = requests.get("http://localhost:5000/question_classifier",params = payload)
        result = response.json()
        return result["result"]
    
    
    def findSubObject(self, query):
        parsed_text = self.nlp(query)
        #get token dependencies
        subject, direct_object = [],[]
        for text in parsed_text:
            print "*"*10
            print text.dep_
            print "*"*10
            #subject would be
            if "subj" in text.dep_:
                subject.append(text.orth_)
            #object
            if "obj" in text.dep_:
                direct_object.append(text.orth_)
        print(subject)
        print(direct_object)
        return dict(subject = subject, object = direct_object)
    
    def doesContextExist(self, query):
        print query, type(query)
        tokens = query.split()
        tagged_tokens = pos_tag(tokens)
        found_pronouns = filter(lambda x:x[1] == "PRP" and x[0] not in ["i","you"], tagged_tokens)
        print found_pronouns
        return bool(found_pronouns)
    
    def getRedisData(self, redis_id):
        try:
            redis_data = json.loads(self.redis_obj.get(redis_id))
        except Exception as f:
            redis_data = json.load(open("db/redis_default.json"))
        return redis_data
    
    def getAnswer(self, query):
        ts = str(int(time()*1000))                                   
        WOLFRAMAPI = "https://www.wolframalpha.com/input/api/v1/code"          
        payload = dict(ts = ts)                                
        result = requests.get(WOLFRAMAPI,params = payload)     
        json_out = json.loads(result.text)
        code = json_out["code"]                             
        print code
        payload=dict(async=True,
            banners="raw",
            debuggingdata=False,
            format="image,plaintext,imagemap,sound,minput,moutput",
            formattimeout=8,
            input=query,
            output="JSON",
            parsetimeout=5,
            podinfosasync=True,
            proxycode=code,
            recalcscheme="parallel",
            sbsdetails=True,
            scantimeout=0.5,
            sponsorcategories=True,
            statemethod="deploybutton",
            storesubpodexprs=True)
        url = "https://www.wolframalpha.com/input/json.jsp"
        refer_dict = dict(i = query)
        payload_refer = urllib.urlencode(refer_dict)
        refer_url = "https://www.wolframalpha.com/input/?"+payload_refer
        headers = {"Host": "www.wolframalpha.com",
                   "Referer":refer_url 
                   }
        result = requests.get(url, params = payload,headers = headers)
        print result.text
        json_output = json.loads(result.text)
        pods = json_output["queryresult"].get("pods")
        try:
            result = pods[1]
            result_info = result["subpods"][0]["plaintext"]
        except Exception:
            print "result not found"
            result_info =  "Sorry I couldnt find an answer to your question"
        return result_info
        
    def remove_redundant(self, query):
        modal_regex = r"\b" + r"\b|\b".join(MODAL_WORDS) + r"\b"
        secondp_regex = r"\b" + r"\b|\b".join(SECOND_PERSON) + r"\b"
        firstp_regex = r"\b" + "me" + r"\b"
        wh_regex = r"\b" + r"\b|\b".join(WH_WORDS) + r"\b"
        reduced_query = re.sub(modal_regex, "MODAL", query)
        reduced_query = re.sub(secondp_regex, "SECPER", reduced_query)
        reduced_query = re.sub(firstp_regex, "FIRPER", reduced_query)
        reduced_query = re.sub(wh_regex, "WH", reduced_query)
        print reduced_query
        action_words = re.search(r"MODAL SECPER (.+?) FIRPER WH",reduced_query)
        action_query = ""
        if not action_words:
            action_words = re.search(r"MODAL SECPER (.+?) WH",reduced_query)
        if action_words:
            action_query = re.sub(r"MODAL SECPER .+? WH",'',reduced_query)
            information_asked = any(map(lambda x:x in action_words, ["tell","say","describe", "help"]))
            if information_asked:
                return action_query
        return query
        
    def userQuery(self, gm_job, gm_obj):
        print "in userQuery"
        try:
            result = {"result":"error"}
            current_data = {}
            gm_data = gm_obj.data
            json_input = json.loads(gm_data)
            json_chat_input = str(json_input["input_text"].lower())
            redis_id = json_input["redis_id"]
            removed_specials_query = re.sub(r"[^A-Za-z0-9]"," ",json_chat_input)
            pre_processed_query = re.sub(r"\s+"," ",removed_specials_query)
            pre_processed_query = self.remove_redundant(pre_processed_query)
            redis_data = self.getRedisData(redis_id)
            query_type = self.findQueryType(pre_processed_query)
            context_exists = self.doesContextExist(pre_processed_query)
            print "context_exists : ", context_exists
            if not context_exists:
                print "Query Type : ", query_type
                if query_type == "interrogative":
                    answer = self.getAnswer(pre_processed_query)
                    print "Soln : ", answer
                    result = answer
                elif query_type == "assertive":
                    redis_data["last_query_information"]["asked_question"] = "should_i_learn"
                    redis_data["last_query_information"]["answer_expected"] = "yes_no"
                    redis_data["last_query_information"]["query_to_learn"] = pre_processed_query
                    result = "Should I learn this information"
            else:
                result = "Sorry, I am not yet trained to handle context questions"
            # saving into redis
            to_save_in_history = dict(original_query = json_chat_input,
                                pre_processed_query = json_chat_input,
                                query_type = query_type,
                                context_exists = context_exists,
                                response = result)
            redis_data["history"].append(to_save_in_history)
            self.redis_obj.setex(redis_id, self.ttl, json.dumps(redis_data))
        except Exception as e:
            print "Exception occurred",e
            print traceback.format_exc()
        return json.dumps(result)

if __name__ == '__main__':
    try:
        print "waiting for call...."
        ChatHandler().gm_worker.work()
    except Exception as e:
        print traceback.format_exc()
        print "\nError in main !! ",e,"\n"
    # tmp = ChatHandler()
    # print tmp.getAnswer("when did bruce lee die")