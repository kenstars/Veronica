from bs4 import BeautifulSoup
import requests
import json
import re
from many_stop_words import get_stop_words
from fuzzywuzzy.fuzz import token_set_ratio

def getWikiResult(passed_url):
    result_value = "0"
    main_content = "mw-parser-output"
    URL = passed_url
    res = requests.get(URL)
    # print res.text
    soup = BeautifulSoup(res.text, 'html.parser')
    valz = soup.find('div', class_ = main_content)
    if valz:
        p_title = valz.find("p")
        results = valz.find("ul")
        result_value = p_title.text +"\n"+ results.text
    return result_value

def getWikiSearch(query):
    stop_words = get_stop_words()
    payload = dict(search = query,
    go = "Go")
    URL = "https://en.wikipedia.org/wiki/Special:Search?"
    res = requests.get(URL,params = payload)
    # print dir(res)
    print res.url , URL not in res.url
    if URL not in res.url:
        href_result = ""
        highest_gram_match_result = [{"href":href_result, "title":query, "exact_match_found":"1"}]
        results_with_exact_match = False
    else:
        soup = BeautifulSoup(res.text, 'html.parser')
        search_class = "mw-search-results"
        valz = soup.find('ul', class_ = search_class)
        all_li = valz.find_all("li")
        result = []
        for each in all_li:
            tmp_string = each.find("div")
            print tmp_string
            match_regex = r'class="searchmatch"'
            if re.search(match_regex, str(tmp_string)):
                anchor_find = tmp_string.find("a")
                print anchor_find
                words_string = tmp_string.find("mw-search-result-data")
                if anchor_find:
                    title = anchor_find["title"].lower()
                    grams = len(title.split())
                    if title in query:
                        result.append(dict(
                            gram_found = grams,
                            title = title,
                            href = anchor_find["href"],
                            exact_match_found = "1"
                        ))
                    else:
                        grams = title.split()
                        non_stop_words =  [gram for gram in grams if gram not in stop_words]
                        all_matches = [words for words in non_stop_words if words.lower() in query.lower()]
                        if all_matches:
                            result.append(dict(
                                gram_found = float(len(all_matches))/len(non_stop_words),
                                title = title,
                                href = anchor_find["href"],
                                exact_match_found = "0",
                                all_match_found = "1"
                            ))
        print result
        results_with_exact_match = filter(lambda x:x["exact_match_found"] == "1", result)
        if results_with_exact_match:
            max_gram_result = max(results_with_exact_match, key = lambda x:x["gram_found"])
            highest_gram_match_result = filter(lambda x:x["gram_found"] == max_gram_result["gram_found"], results_with_exact_match)
        elif result:
            max_gram_result = max(result, key = lambda x:x["gram_found"])
            highest_gram_match_result = filter(lambda x:x["gram_found"] == max_gram_result["gram_found"],result)
        else:
            print soup
            highest_gram_match_result = []
    return highest_gram_match_result, bool(results_with_exact_match)

def getDataFromWikiLink(link):
    pass

def removeUnnecessary(title):
    name_suffix = ["jr", "sr", "sir", "dame", "queen", "duchess", "mr", "mrs", "dr"]
    title = re.sub(r"[^A-za-z0-9 ]","",title)
    output_ngrams = title.split()
    return_list = []
    for each in output_ngrams :
        if each not in name_suffix:
            return_list.append(each)
    if not return_list:
        return_list = str(title)
    else:
        return_list =  str(" ".join(return_list))
    return return_list.strip()


if __name__ == '__main__':
    query = "Tell me about Baidu corporation".lower()
    lresult, exact_match_bool = getWikiSearch(query)
    if exact_match_bool:
        if len(lresult) == 1:
            print lresult
        else:
            print "Do you want to know about ",
            for each in lresult:
                print each
    else:
        print "We don't seem to have exactly what you want, Does this help :"
        for each in lresult:
            title = each["title"]
            title = removeUnnecessary(title)
            print title.split()
            print query.split()
            resultant = token_set_ratio(title.split(), query.split())
            print resultant
            if resultant == 100:
                print each
                break
            else:
                print each
