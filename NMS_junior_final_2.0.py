'''Analysis:
token time = 20s
code refresh = 30s
status changing = 10s
login forbbiden time = 20s

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
status = 0
success=0
wait=30
username= "dailin"
password = ""


def get_password(user_name):
    user_name = {'username': user_name}
    res = requests.post(url=config.signup_url, data=user_name)
    return json.loads(res.text)["password"]

def login(username,password):
    global token
    user_data = {
        'username': username,
        'password': password
    }
    res = json.loads(requests.post(url=config.login_url, data=user_data).text)
    if "message" in res:
        err = res["message"]
        if err =="Forbidden":
            print("repeated login? wait")
            time.sleep(10) #避免重复登陆
        else:
            print(err)
            raise ConnectionError("3")
    elif "token" in res:
        token= res["token"]
        print("login:"+token[:10])
    else:
        log_and_print(config.log_file,"login:"+str(res))

def token_update():
    global token, status
    headers={
        "Authorization": "Bearer "+token 
    }
    try:
        res=json.loads(requests.get(url=config.heartbeat_url, headers=headers).text)
        if "message" in res:
            err=res["message"]
            if err == "Internal Server Error":
                status = 2

            elif err == "Bad Gateway":
                status = 3
            
            elif err == "invalid or expired jwt" or "missing or malformed jwt":
                status = 4 
            
            else:
                print("beat:"+err)
            #status 2,3
        else:
            token=res["token"]
            status = 0

    except Exception as e:
        if "Connection refused" in str(e):
            status = 1
        else:
            log_and_print(config.log_file,"update:"+str(e))


def get_code(token):
    headers={
        "Authorization": "Bearer "+token 
    }
    res=json.loads(requests.get(config.info_url,headers=headers).text)
    code=res["code"]
    print("get code:"+code)
    return code

def post_code(token,code):
    headers={
        "Authorization": "Bearer "+token 
    }
    data={
        "code":code
    }
    res=json.loads(requests.post(config.validate_url,headers=headers,data=data).text)
    print(res)

def heart_beat():
    global wait,status,token
    while True:
        token_update()
        print("status:"+str(status))
        if status == 4 or status == 2:  #可以更好的抓住status 2作为提交机会
            print("login to get new token...")
            login(username,password)
            status = 0
            print("status update:" + str(status))
        wait+=config.beat_delay
        time.sleep(config.beat_delay)

def log_and_print(file_name:str ,content):
    current_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S ')
    with open(file_name, 'a') as logfile:
        logfile.write(current_time + str(content) + '\n')
    print(content)

for i in range(20):
    try:
        password=get_password(user_name=username)
        login(username,password)
        break
    except Exception as e:
        print("try again...")
        time.sleep(config.beat_delay)
        #确保在网络异常时获得用户信息

beat=threading.Thread(target=heart_beat,daemon=True) #daemon used to stop this thread when main thread stop
beat.start()
#开始心跳，来检查服务器状态

while success < 15:
    if wait>30 and status==0:#条件允许，则提交code
        code=get_code(token)
        post_code(code=code,token=token)
        success+=1
        print(f"it is the {success} success!!!!!!!")
        wait=0

