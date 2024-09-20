'''Analysis:
token time = 20s
code refresh = 30s
status changing = 10s
login forbidden time = 20s

status 1: connection refused
status 2:(enter:expire session 
         leave:expire session)
         message:Internal Server Error
status 3: message:Bad Gateway

token died:message:invalid or expired jwt
repeated logins:message:Forbidden

if token expired , must login again
'''

from datetime import datetime
import requests,json,time,threading
import config


token = ""
status = "fine"
success=0
wait=30
username = "dailin"
password = ""


def get_password(username):
    user_name = {'username': username}
    print("getting user data...")
    res= json.loads(requests.post(url=config.signup_url, data=user_name).text)
    if "password" in res:
        print("get user password:"+res["password"])
        return res["password"]
    elif "message" in res:
        err = res["message"]
        raise requests.exceptions.ConnectionError(err)  # return "message" is due to servers' status not good(status 1 or 3)

def login(username,password):
    global token
    user_data = {
        'username': username,
        'password': password
    }
    print("try login...")
    res = json.loads(requests.post(url=config.login_url, data=user_data).text)
    if "token" in res:
        token= res["token"]
        print("login:"+token[:10])
    elif "message" in res:
        err = res["message"]
        if "Connection refused" in str(err):
            err = "Connection refused"
        raise requests.exceptions.ConnectionError(err)


def token_update():
    global token, status
    headers={"Authorization": "Bearer "+token }
    res=json.loads(requests.get(url=config.heartbeat_url, headers=headers).text)
    if "token" in res:
        token=res["token"]
        status = "fine"
    elif "message" in res:
        status =res["message"]
        raise requests.exceptions.ConnectionError(status)


def get_and_post_code(token):
    headers={"Authorization": "Bearer "+token }
    res=json.loads(requests.get(config.info_url,headers=headers).text)
    code = res["code"]
    print("get code:"+code)
    headers={"Authorization": "Bearer "+token }
    data={"code":code}
    res=json.loads(requests.post(config.validate_url,headers=headers,data=data).text)
    print(res) #try and exception is below, because this function is running in a safe environment,so I didn't do exceptional error handling

def heart_beat():
    global wait,status,token
    while True:
        try:
            token_update()
            wait+=config.beat_delay
            time.sleep(config.beat_delay)
            print("status update:" + str(status))
        except requests.exceptions.ConnectionError as err:
            if (str(err) == "invalid or expired jwt" or
                    str(err) == "missing or malformed jwt" or
                    str(err) == "Internal Server Error"):
                print("login to get new token...")
                login(username,password)
                status = "fine"
                print("status update:" + str(status))
            else:
                if "Connection refused" in str(err):
                    err = "Connection refused"
                print("status update:" + str(err))
                wait += config.beat_delay
                time.sleep(config.beat_delay)
        except Exception as err:
            log_and_print(config.log_file, "heartbeat occur unexpected error:" + str(err))
            status = "?"

def log_and_print(file_name:str ,content):
    current_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S ')
    with open(file_name, 'a') as logfile:
        logfile.write(current_time + str(content) + '\n')
    print(content)



for i in range(config.max_retries):
    try:
        password=get_password(username)
        login(username,password)
        break
    except requests.exceptions.ConnectionError as err:
        if "Connection refused" in str(err):
            err="Connection refused"
        print("can't login due to network error:"+str(err))
        print("try again...")
        time.sleep(config.beat_delay)
        continue
    except Exception as e:
        log_and_print(config.log_file,"login occur unexpected error:" + str(e))

beat=threading.Thread(target=heart_beat,daemon=True) #daemon used to stop this thread when main thread stop
beat.start()
#开始心跳，来检查服务器状态

while success < config.post_target:
    if wait>config.code_fresh and status== "fine": #条件允许，则提交code
        try:
            get_and_post_code(token)
            success+=1
            print(f"it is the {success} success!!!!!!!")
            wait=0
        except Exception as e:
            if "Connection refused" not in str(e):
                log_and_print(config.log_file,"post occur unexpected error:" + str(e))
                status= "?"

