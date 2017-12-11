from datetime import  datetime
import urllib, urllib2
from bs4 import BeautifulSoup
import json
import re
import gearman

class NewsFeedData():
    def __init__(self):
        self.config = json.load(open("./config.json", "r"))
        self.gm_worker = gearman.GearmanWorker([ str(self.config["gearmanip"]) +":"+ str(self.config["gearmanport"])])
        self.gm_worker.register_task('call_for_newsfeed', self.run)
        self.topic = ['india', 'world', 'business', 'sports', 'politics', 'entertainment', 'cricket', 'bollywood', 'tech', 'local']
        self.UserAgent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36'

    def get_url_list(self,url_list):
        try:
            url = 'https://www.repeatsoftware.com/Help/RSSFeedList.htm'
            req = urllib2.Request(url, headers={ 'User-Agent': self.UserAgent })
            list_data = urllib2.urlopen(req).read()
            list_soup = BeautifulSoup(list_data,"html.parser")
            print "receive_data"
            for each in list_soup.find_all('td'):
                if each.find('a'):
                    url_list.append(each.find('a')['href'])
        except Exception as e:
            print "error inside get_url_list",e
        return url_list

    def bbc_news_scrap(self, url):
        try:
            title_url = []
            req = urllib2.Request(url, headers={ 'User-Agent': self.UserAgent })
            bbc_links = urllib2.urlopen(req).read()
            list_soup = BeautifulSoup(bbc_links,"html.parser")
            for each in list_soup.find_all('item'):
                if each.find('title') and  each.find('guid').text:
                    title_url.append([each.find('title').text,  each.find('guid').text])
        except Exception as e:
            print "error inside bbc_news_scrap",e
        return title_url

    def cbn_news_scrap(self, url):
        try:
            title_url = []
            link_reg = r"<link\/>(.*)<isvideoarticle>"
            req = urllib2.Request(url, headers={ 'User-Agent': self.UserAgent })
            cbn_links = urllib2.urlopen(req).read()
            list_soup = BeautifulSoup(cbn_links,"html.parser")
            for each in list_soup.find_all('item'):
                if each.find('title') and  re.findall(link_reg, str(each))[0]:
                    title_url.append([each.find('title').text,  re.findall(link_reg, str(each))[0]])
        except Exception as e:
            print "error inside cbn_news_scrap", e
        return title_url

    def reuters_scrap(self, url):
        try:
            title_url = []
            link_reg = r"<link\/>(.*)<isvideoarticle>"
            req = urllib2.Request(url, headers={ 'User-Agent': self.UserAgent })
            reuters_links = urllib2.urlopen(req).read()
            list_soup = BeautifulSoup(reuters_links,"html.parser")
            for each in list_soup.find_all('item'):
                if each.find('title') and  each.find('guid').text:
                    title_url.append([each.find('title').text,  each.find('guid').text])
        except Exception as e:
            print "error inside reuters_scrap", e
        return title_url

    def run(self, gearman_worker, gearman_job):
        # import pdb; pdb.set_trace()
        print "inside run", json.loads(gearman_job.data)
        data = json.loads(gearman_job.data)
        url_list,title_url_list = [], []
        try:
            print "inside try block"
            url_list = self.get_url_list(url_list)
            for each_url in url_list:
                if 'cbn' in each_url:
                    title_url_list.extend(self.cbn_news_scrap(each_url))
                if 'reuters' in each_url:
                    title_url_list.extend(self.reuters_scrap(each_url))
        except Exception as e:
            print "error from run>>>>", e
        return json.dumps(title_url_list)

if __name__ == '__main__':
    obj = NewsFeedData()
    obj.gm_worker.work()
