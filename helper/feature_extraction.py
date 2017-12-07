import json
import sys
import re
import pysolr
import traceback
import gearman

with open('config.json','r') as filename:
    config = json.load(filename)
spacy_client = gearman.GearmanClient([ str(config["gearmanip"]) +":"+ str(config["gearmanport"]) ])

def callFeatureExtractor(method_name, query, redis_data, getanswer):
    try:
        response = "I did not find the answer we were looking for. REPEATQUESTION"
        with open("data/methods.json") as method_file:
            method_json = json.load(method_file)
        functions_list = method_json.get(method_name)
        if functions_list:
            for each in functions_list:
                print "Method going to be called", each
                response, redis_data = globals()[each](query, redis_data, getanswer)
    except Exception as e:
        print "Exception Occurred", e
        print traceback.format_exc()
    return response, redis_data

def learnInformation(*args):
    query = args[0]
    redis_data = args[1]
    query_to_learn = redis_data["last_query_information"]["query_to_learn"]
    solr_query = dict(memory = query_to_learn)
    val1 = re.search("(yes|yeah|sure|ya|ye|alrite|alright|ok|okz|okay|okey|okei|yup|yupz|yo|please|affirmative|fine)(s*)(\s|$)", query, re.I)
    val2 = re.search("(no|nope|nay|naa|na|nah|naaa)(s*)(\s|$)", query, re.I)
    if val1:
        response = "Thank you. I will remember that."
        insertSolrchatData(solr_query)
        redis_data["last_query_information"] = {}
    elif val2:
        response = "Alright, I'll forget it"
        redis_data["last_query_information"] = {}
    else:
        response = "Please let me know if I should remember that or not."
    return response, redis_data

def findIfPersonal(*args):
    print "in findIfPersonal"
    query = args[0]
    possessive_words = ["me", "my", "mine", "i"]
    possessive_regex = r"\b" + "\b|\b".join(possessive_words) + r"\b"
    result = re.findall(possessive_regex, query)
    print result
    return bool(result)

def lookUpOnline(*args):
    print "in lookUpOnline", args[1]
    query = args[0]
    redis_data = args[1]
    getAnswer = args[2]
    val1 = re.search("(yes|yeah|sure|ya|ye|alrite|alright|ok|okz|okay|okey|okei|yup|yupz|yo|please|affirmative|fine)(s*)(\s|$)", query, re.I)
    val2 = re.search("(no|nope|nay|naa|na|nah|naaa)(s*)(\s|$)", query, re.I)
    if val1:
        response = getAnswer(redis_data["last_query_information"]["query_to_learn"])
        redis_data["last_query_information"] = {}
    elif val2:
        response = "Please tell me the answer so that I can learn"
        redis_data["question_provided"] = redis_data["last_query_information"]["query_to_learn"]
        redis_data["last_query_information"] = {}
    else:
        response = "Please let me know if I should I search online or not"
    return response, redis_data

def insertSolrchatData(solr_json):
    print "\n ===================== inside insertSolrchatData =================== \n"
    try:
        solr_data = solr_json
        query_data = {}
        for key in solr_data.keys():
            if isinstance(solr_data[key], str):
                query_data[key.encode('ascii', 'ignore')] = solr_data[key].encode('ascii', 'ignore')
            else:
                query_data[key.encode('ascii', 'ignore')] = solr_data[key]
        solr_url = pysolr.Solr('http://localhost:8983/solr/veronica', timeout = 10000000)
        print "query_data", query_data
        solr_url.add([query_data])
        print "\nData Inserted in Solr!!!\n","=="*25
    except Exception as e:
        print "\nError in solr insertion : ", str(e)

def CompareSentences(input_value1, input_value2):
    result1 = spacy_client.submit_job(str(config["spacy"]),json.dumps(dict(query = input_value1, query_type = "question")))
    outcome1 = json.loads(result1.result)
    print input_value1
    print outcome1
    result2 = spacy_client.submit_job(str(config["spacy"]),json.dumps(dict(query = input_value2, query_type = "answer")))
    outcome2 = json.loads(result2.result)
    print input_value2
    print outcome2
    matched_results = len(list(set(outcome1).intersection(outcome2)))
    result_value = set(outcome2) - set(outcome1)
    return matched_results == 2, list(result_value)
    
def solr_search(query, redis_data, search_type = "memory"):
    print "\n\n\n ==============in solr_search========== \n\n\n\n"
    new_query = re.sub(r"[^a-zA-Z0-9]","", query)
    ans_dict = {}
    search_results = []
    solr_query = search_type+": " + query
    try :
        response = ""
        solr_url = pysolr.Solr('http://localhost:8983/solr/veronica', timeout = 20)
        search_results = solr_url.search(solr_query)
        result_variables = []
        if search_results:
            for result in search_results:
                result_query = re.sub(r"[^a-zA-Z0-9 ]","",result['memory'])
                print query,"####", result_query
                boolean_outcome, outcomes = CompareSentences(query, result_query)
                if boolean_outcome:
                    result_variables.extend(outcomes)
            if result_variables:
                result_variables = list(set(result_variables))
                print "result_variables", result_variables
                response = "It is "
                if len(result_variables) == 1:
                    response += " ".join(result_variables)
                else:
                    response += ", ".join(result_variables[:-1]) +" and " + result_variables[-1]
        if not response:
            response = "I do not know the answer to this. Would you like me to look up online."
            redis_data["last_query_information"]["asked_question"] = "look_up_online"
            redis_data["last_query_information"]["query_to_learn"] = query
    except Exception as e:
        print "\nERROR in solr_search !!!! \n", e
        print traceback.format_exc()
    return response, redis_data