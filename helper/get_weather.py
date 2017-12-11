# -*- coding: utf-8 -*-
import gearman
import urllib
import requests
from bs4 import BeautifulSoup
import json
# from socketIO_client import SocketIO
#
print "connecting to server"

class WeatherData():
    def __init__(self):
        self.config = json.load(open("./config.json", "r"))
        self.gm_worker = gearman.GearmanWorker([ str(self.config["gearmanip"]) +":"+ str(self.config["gearmanport"])])
        self.gm_worker.register_task('send_location_details', self.get_weather)

    def get_weather(self, gearman_worker, gearman_job):
        print "inside get weather", json.loads(gearman_job.data)
        data = json.loads(gearman_job.data)
        data_to_send = {}

        try:
            url_data =  urllib.urlopen('http://openweathermap.org/data/2.5/weather?q='+data["city"]+'&appid=b6907d289e10d714a6e88b30761fae22')
            weather_content = BeautifulSoup(url_data,"html.parser")
            print ">>>>>>>>>>>>>",weather_content
            weather_json = json.loads(str(weather_content))
            data_to_send = {'loc':weather_json["name"],'temp':weather_json["main"]["temp"], 'humidity':weather_json["main"]["humidity"]}
            print "data to send >>>",data_to_send
            # gm_client.submit_job('fetch_weather_details', json.dumps({'loc':weather_json["name"],'temp':weather_json["main"]["temp"], 'humidity':weather_json["main"]["humidity"], "socket_id":socket_id}))
        except Exception as e:
            print "error>>>>",e

        return json.dumps(data_to_send)


if __name__=="__main__":
    obj = WeatherData()
    obj.gm_worker.work()
