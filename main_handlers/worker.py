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
import urllib
from time import time
from base64 import b64decode
from helper.feature_extraction import *
import xmltodict

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
        print "in getAnswer"
        ts = str(int(time()*1000))
        PRIMARYCODEX = "aHR0cHM6Ly93d3cud29sZnJhbWFscGhhLmNvbS9pbnB1d"
        CODEX1 = PRIMARYCODEX + "C9hcGkvdjEvY29kZQ=="
        CODEX2 = PRIMARYCODEX + "C9qc29uLmpzcA=="
        CODEX3 = PRIMARYCODEX + "C8/"
        CODEX4 = "d3d3LndvbGZyYW1hbHBoYS5jb20="
        HOSTCODEX = b64decode(CODEX4)
        CODEX_REQUEST = b64decode(CODEX1)
        CODEX_REQUEST2 = b64decode(CODEX2)
        CODEX_REFER =  b64decode(CODEX3)
        payload = dict(ts = ts)
        result = requests.get(CODEX_REQUEST,params = payload)
        json_out = json.loads(result.text)
        code = json_out["code"]
        print "#"*10
        print code
        print "#"*10
        payload=dict(ts=ts,
            async=True,
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
        refer_dict = dict(i = query)
        payload_refer = urllib.urlencode(refer_dict)
        refer_url = CODEX_REFER + payload_refer
        headers = {
                    "Host": HOSTCODEX,
                    "Referer":refer_url
                   }
        result = requests.get(CODEX_REQUEST2, params = payload, headers = headers)
        print result.text
        json_output = json.loads(result.text)
        pods = json_output["queryresult"].get("pods")
        try:
            result = pods[1]
            result_info = result["subpods"][0]["plaintext"]
        except Exception:
            print "result not found"
            result_info =  "Sorry I couldnt find an answer to your question"
        else:
            return result_info
        if json_output["queryresult"]["id"]:
            send,xml_output = self.recal_function(json_output, headers)
            json_output = xmltodict.parse(xml_output)
            print "*"*10
            stringified_output = json.dumps(json_output)
            print "*"*10
            if stringified_output:
                result_info = self.makeAnswer(stringified_output, query )
            else:
                 print "No answer found"
                 result_info = "0"
        return result_info
        # json_output = self.recal_function(json_output, headers)
        #raw_input("************")
        #send,json_output = self.recal_next(json_output,headers,send)

    def makeAnswer(self, stringified_output, query):
        input_value = json.loads(stringified_output)
        pods = input_value["pod"]
        input_interpretation = filter(lambda x:x["@title"].lower() == "input interpretation", pods)
        input_text =  input_interpretation["plain_text"]
        if input_text in query:
            for each in pods:
                if each["@title"].lower() == "notable_facts":
                    result["1_notable_facts"] = each
                elif each["@title"].lower() == "image":
                    result["2_image"] = each["@async"]
                elif each["@title"].lower() == "basic information":
                     tmp = re.sub("\(.+?\)","",each["plain_text"])
                     result["0_basic_info"] = dict([each.split("|") for each in tmp.split("\n")])
            input_text = result
        return input_text

    def recal_next(self,json_output ,headers,send):
        recal_id = send["recal_id"]
        recal_s = send["recal_s"]
        # url_start = "https://www4d.wolframalpha"
        url_start = send["url_start"]
        payload_jump = dict(action="recalc",
        duplicatepodaction="read",
        format	="image,plaintext,imagemap,minput,moutput",
        id=recal_id,
        output = {0	:"JSON",
        1:"JSON"},
        podinfoasync=True,
        redisFailed	=True,
        s=recal_s,
        sbsetails=True,
        scantimeout=10,
        statemethod="deploybutton",
        storesubpodexprs=True)
        # print payload_jump, url_start
        url_jump = url_start+".com/input/json.jsp"
        result_jump = requests.get(url_jump, params = payload_jump, headers = headers)
        xml_output = result_jump.text
        return send,result_jump.text

    def recal_function(self, json_output, headers):
        recal_id = 0
        recal_s = 0
        send = {}
        url_start = "https://www4d.wolframalpha"
        try:
            recal = json_output["queryresult"].get("recalculate")
            try:
                recal_id = recal.split("id=")[1].split("&")[0]
                recal_s = recal.split("&s=")[1].split("&")[0]
                url_start = recal.split(".com")[0]
                print "recal_id",recal_id
                print "recal_s",recal_s
            except:
                print "Error in id"
        except:
            print "No recal"

        payload_jump = {"action":"recalc",
            "duplicatepodaction":"write",
            "format":"image,plaintext,imagemap,minput,moutput",
            "id":recal_id,
            "output":{
            "0":"JSON",
            "1":"JSON"
            },
            "podinfoasync":True,
            "redisFailed":True,
            "s":recal_s,
            "sbsetails":True,
            "scantimeout":0.5,
            "statemethod":"deploybutton",
            "storesubpodexprs":	True}


    #     payload = {
    #     "action": "recalc",
    #     "duplicatepodaction" : "read",
    #     "format" : "image,plaintext,imagemap,minput,moutput",
    #     "id" : "",
    #     "output" : "JSON",
    #     "podinfoasync" : true,
    #     "redisFailed" : true,
    #     "s" :"",
    #     "sbsetails" : true,
    #     "scantimeout" : 0.5,
    #     "statemethod" : "deploybutton",
    #     "storesubpodexprs" :true
    # }
        url_jump = url_start+".com/input/json.jsp"
        result_jump = requests.get(url_jump, params = payload_jump, headers = headers)
        print result_jump.text
        send["recal_s"] = recal_s
        send["recal_id"] = recal_id
        send["url_start"] = url_start
        return send,result_jump.text

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
            removed_specials_query = re.sub(r"[^A-Za-z0-9 +-/*]"," ",json_chat_input)
            pre_processed_query = re.sub(r"\s+"," ",removed_specials_query)
            pre_processed_query = self.remove_redundant(pre_processed_query)
            redis_data = self.getRedisData(redis_id)
            print "=-=-"*10,"REDIS AT START", "=-=-"*10
            print redis_data
            print "=-=-"*15, "=-=-"*15
            query_type = self.findQueryType(pre_processed_query)
            question_asked = redis_data["last_query_information"].get("asked_question")
            context_exists = False
            if question_asked:
                result, redis_data = callFeatureExtractor(question_asked, pre_processed_query, redis_data, self.getAnswer)
                print "result in question_asked>>>>>", result
            else:
                context_exists = self.doesContextExist(pre_processed_query)
                print "context_exists : ", context_exists
                if not context_exists:
                    print "Query Type : ", query_type
                    if query_type == "interrogative":
                        personal_bool = findIfPersonal(pre_processed_query)
                        print "personal_bool>>", personal_bool
                        if personal_bool:
                            answer, redis_data = solr_search(pre_processed_query, redis_data, search_type = "questions")
                            if answer:
                                result = answer
                            else:
                                answer, redis_data = solr_search(pre_processed_query, redis_data)
                                print "Soln Solr :", answer
                        else:
                            answer = self.getAnswer(pre_processed_query)
                            print "Soln : ", answer
                        if answer:
                            result = answer
                    elif query_type == "assertive":
                        question_provided = redis_data.get("question_provided")
                        if question_provided:
                            solr_query = dict(questions = question_provided,
                                              memory = pre_processed_query)
                            insertSolrchatData(solr_query)
                            result = "Thank you. I will remember that."
                            redis_data["question_provided"] = ""
                            redis_data["last_query_information"] = {}
                        else:
                            redis_data["last_query_information"]["asked_question"] = "should_i_learn"
                            redis_data["last_query_information"]["query_to_learn"] = pre_processed_query
                            result = "Should I learn this information"
                else:
                    result = "Sorry, I am not yet trained to handle context questions"
            # saving into redis
            to_save_in_history = dict(original_query = json_chat_input,
                                pre_processed_query = pre_processed_query,
                                query_type = query_type,
                                context_exists = context_exists,
                                response = result)
            redis_data["history"].append(to_save_in_history)
            self.redis_obj.setex(redis_id, self.ttl, json.dumps(redis_data))
            print "=-=-"*10,"REDIS AT END", "=-=-"*10
            print redis_data
            print "=-=-"*15, "=-=-"*15
        except Exception as e:
            print "Exception occurred",e
            print traceback.format_exc()
        return json.dumps(dict(response=result, question_keywords=""))
if __name__ == '__main__':
    #try:
    #    print "waiting for call...."
    #    ChatHandler().gm_worker.work()
    #except Exception as e:
    #    print traceback.format_exc()
    #    print "\nError in main !! ",e,"\n"
    tmp = ChatHandler()
    print tmp.getAnswer("who invented the bicycle")
