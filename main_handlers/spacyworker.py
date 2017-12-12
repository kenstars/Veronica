import gearman
import json
import spacy
import traceback


class SpacemanSpiff():
    def __init__(self):
        with open('config.json','r') as filename:
            self.config = json.load(filename)
        self.gm_worker = gearman.GearmanWorker([ str(self.config["gearmanip"]) +":"+ str(self.config["gearmanport"]) ])
        self.gm_client = gearman.GearmanClient([ str(self.config["gearmanip"]) +":"+ str(self.config["gearmanport"]) ])
        self.gm_worker.register_task(str(self.config["spacy"]), self.findSubObject)
        self.nlp = spacy.load('en_md')
        print "Spacy initialising complete"

    def findSubObject(self, gm_job, gm_object):
        try:
            json_data = json.loads(gm_object.data)
            query = json_data["query"]
            query_type = json_data["query_type"]
            print query, type(query)
            parsed_text = self.nlp(query)
            #get token dependencies
            subject, direct_object = [],[]
            ROOT_VALUE = []
            do_not_add = False
            for text in parsed_text:
                print "*"*10
                print text
                print text.dep_
                print text.orth_
                print "*"*10
                #subject would be
                if "ROOT" in text.dep_:
                    ROOT_VALUE.append(text.orth_)
                elif any(map(lambda x:x in text.dep_, ["amod", "acomp","compound","attr","subj","obj"])) and not do_not_add:
                    if  not ROOT_VALUE:
                        print "Subject Value to be appended", text.orth_
                        subject.append(text.orth_)
                    else:
                        print "Object Value to be appended", text.orth_
                        direct_object.append(text.orth_)
                elif ROOT_VALUE and query_type != "question":
                    print "do not add has been reached"
                    do_not_add = True
                    
            subject = " ".join(subject)
            direct_object = " ".join(direct_object)
            ROOT_VALUE = " ".join(ROOT_VALUE)
            print(direct_object)
        except Exception as e:
            print "Exception Occurred", e
            print traceback.format_exc()
        return json.dumps([subject, ROOT_VALUE, direct_object])
    
if __name__ == '__main__':
    try:
        print "waiting for call...."
        SpacemanSpiff().gm_worker.work()
    except Exception as e:
        print traceback.format_exc()
        print "\nError in main !! ",e,"\n"