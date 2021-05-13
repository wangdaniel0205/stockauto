import requests
from datetime import datetime

myToken = 'xoxb-1989182461360-1978004851105-8NyaxHeKAsD4rnb9QidCUZfT'

def bot_post(text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+myToken},
        data={"channel": "#stock","text": text}
    )
    #print(response)

def printlog(message, *args):
    """print to current cmd"""
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)
 
def dbgout(message):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S] ') + message
    bot_post(strbuf)

def write_daily_result(investment, gain):
    f = open("records.txt", "a")
    f.write(datetime.now().strftime('[%m/%d %H:%M:%S]')+"평가금액: {}, 평가손익: {}".format(investment, gain))
    f.close()
