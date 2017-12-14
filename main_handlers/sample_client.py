import gearman
import json

with open('config.json','r') as filename:
    config = json.load(filename)
gm_client = gearman.GearmanClient([ str(config["gearmanip"]) +":"+ str(config["gearmanport"]) ])
input_value = raw_input("Enter your input ")
input_dictionary = dict(
    input_text = input_value,
    redis_id = "admin"
)
print input_dictionary
res = gm_client.submit_job(str(config["chat_worker"]), json.dumps(input_dictionary))
output_result = res.result
print output_result
