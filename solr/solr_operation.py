import pysolr
import json
import re
import sys
import os
import urllib2

class SolrOperation(object):
    def __init__(self):
       self.ip = "localhost"
       self.port = "8983"

    def addCoreInSolr(self, core_name, configSet):
        print "Adding New Core : ", core_name
        app_core_url = "http://" + self.ip + ":" + self.port + "/solr/admin/cores?action=CREATE&name=" + core_name + "&configSet=" + configSet
        try :
            urllib2.urlopen(app_core_url)
            urllib2.urlopen("http://localhost:" + self.port + "/solr/admin/cores?action=RELOAD&core="+ core_name)
            print("Core created : ", core_name)
        except Exception as e:
            print "Workapps :: ERROR in SOLR add Core for appid = " + str(core_name) + " ERROR :: " + str(e)
            return False

        return True


    def createDataInSolr(self, core_name, data):
        print "core name in create ::" , core_name
        try:
            self.solr_data = pysolr.Solr('http://' + self.ip + ':' + self.port + '/solr/' + core_name, timeout = 100)
            self.solr_data.add(data)
            print "Data sync successfully"
        except Exception as e:
            print "ERROR in SOLR addData for Data = " + str(data) + " MESSAGE :: " + str(e)

        return {"result":"Data sync successfully"}

    def deleteDataInSolr(self, core_name, filed_name , uniqueTerm):
        try:
            # self.solr_data = pysolr.Solr('http://localhost:8983/solr/' + core_name, timeout = 10)
            self.solr_data = pysolr.Solr('http://' + self.ip + ':' + self.port + '/solr/' + core_name, timeout = 10)
            self.solr_data.delete(q = filed_name + ": " + str(uniqueTerm))
            print "data deleted successfully"
        except Exception as e:
            print "ERROR in SOLR delete operation for ID = ", traceback.format_exc()

        return {"result":"Data deleted successfully"}

    def serachInSolr(self, core_name, query):
        solr_url = pysolr.Solr('http://' + self.ip + ':' + self.port + '/solr/' + core_name)
        solr_result = solr_url.search(query)
        return solr_result
        
            
if __name__ == '__main__':
    obj = SolrOperation()
    # obj.addCoreInSolr(sys.argv[1],sys.argv[1])
    data = [{"personName":"Mandar","companyName":"A","linkedinUrl":"asd"},
        {"personName":"Aamir","companyName":"B","linkedinUrl":"as"},
        {"personName":"Zensoft","companyName":"C","linkedinUrl":"asd"}]
    # obj.createDataInSolr(sys.argv[1], data)
    obj.deleteDataInSolr(sys.argv[1], "*" , "*")
    # solr_result = obj.serachInSolr(sys.argv[1],"Mandar")
    # for res in solr_result:
    #         print res