import json
import os

def generate_intent_engine(engine):
    INTENT_ROOT_PATH = "data/intents/"
    all_files = os.listdir(INTENT_ROOT_PATH)
    for file_path in all_files:
        with open(file_path) as file_obj:
            json_data = json.load(file_obj)
        tmp = ""
        for each_key in json_data:
            for each_mandatory_dictionary in json_data[each_key]:
                keyWordName = each_mandatory_dictionary["IntentObjectName"]
                keywordList = each_mandatory_dictionary.get("IntentObjectKeywordList")
                keywordType = each_mandatory_dictionary["IntentObjectKeywordType"]
                if keywordType == "list":
                    for each_keyword in keywordList:
                        engine.register_entity(each_keyword, keyWordName)
                elif keywordType == "regex":
                    engine.register_regex_entity(keyWordName)
                if not tmp:
                    tmp = IntentBuilder(json_data["intent_name"])
                if each_key == "mandatory":
                    tmp = tmp.require(keyWordName)
                else:
                    tmp = tmp.optionally(keyWordName)
        engine.register_intent_parser(tmp)
    return engine