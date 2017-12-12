import requests
import json
import re
from bs4 import BeautifulSoup
from many_stop_words import get_stop_words

HOW_TO_SEARCH_RESULT_CLASS = "result_data"
def getHowToInfo(query):
    stop_words = get_stop_words()
    payload = dict(
        search = query.lower()
    )
    URL = "https://www.wikihow.com/wikiHowTo"
    res = requests.get(URL, params = payload)
    print res.text
    print res.url
    soup = BeautifulSoup(res.text,"html.parser")
    
    list_result = soup.find_all("div", class_ = HOW_TO_SEARCH_RESULT_CLASS)
    final_result = []
    max_gram_matched = 0
    for each in list_result[:5]:
        views = each.find("li", class_ = "sr_view")
        views = views.get_text()
        views = int(re.sub(r"[^0-9]","",views))
        anchor = each.find("a", class_ = "result_link")
        link = anchor["href"]
        text = anchor.get_text().lower()
        grams = text.split()
        grams = [ each for each in grams if each not in stop_words ]
        grams_match = [ each for each in grams if each in query.lower()]
        cur_grams = float(len(grams_match))/len(grams)
        print text, cur_grams
        if cur_grams > max_gram_matched:
            max_gram_matched = cur_grams
        final_result.append(dict(views = views,
                                 link = link,
                                 title = text,
                                 grams_match = cur_grams))
    final_result = filter(lambda x:x["grams_match"] == max_gram_matched, final_result)
    return final_result

if __name__ == '__main__':
    query = "how to make butter chicken"
    final_result = getHowToInfo(query)
    print final_result
    exact_match = filter(lambda x:query in x["title"], final_result)
    if exact_match:
        result = exact_match
    else:
        result = max(final_result, key = lambda x:x["views"])
    print result