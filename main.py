import json
import os

nowdir = os.getcwd()

with open(nowdir + '/environment/setting.json' , 'r') as f:
    envData = json.load(f)

if __name__=="__main__":
    if envData['used_db'] == True:
        import environment.gptChatBotUsedDB as usedDB
    elif envData['used_db'] == False:
        import environment.gptChatBotnotUsedDB as notDB