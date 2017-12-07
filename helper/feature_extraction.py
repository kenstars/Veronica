import json
import sys

class FeatureWorker(object):
    def __init__(self):
        pass
    
    def getFeatures(self, query):
        self.getDateTime(query)
    
    
    
if __name__ == '__main__':
    fw = FeatureWorker()
    