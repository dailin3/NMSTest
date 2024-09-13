'''
......................................&&.........................
....................................&&&..........................
.................................&&&&............................
...............................&&&&..............................
.............................&&&&&&..............................
...........................&&&&&&....&&&..&&&&&&&&&&&&&&&........
..................&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&..............
................&...&&&&&&&&&&&&&&&&&&&&&&&&&&&&.................
.......................&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&.........
...................&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&...............
..................&&&   &&&&&&&&&&&&&&&&&&&&&&&&&&&&&............
...............&&&&&@  &&&&&&&&&&..&&&&&&&&&&&&&&&&&&&...........
..............&&&&&&&&&&&&&&&.&&....&&&&&&&&&&&&&..&&&&&.........
..........&&&&&&&&&&&&&&&&&&...&.....&&&&&&&&&&&&&...&&&&........
........&&&&&&&&&&&&&&&&&&&.........&&&&&&&&&&&&&&&....&&&.......
.......&&&&&&&&.....................&&&&&&&&&&&&&&&&.....&&......
........&&&&&.....................&&&&&&&&&&&&&&&&&&.............
..........&...................&&&&&&&&&&&&&&&&&&&&&&&............
................&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&............
..................&&&&&&&&&&&&&&&&&&&&&&&&&&&&..&&&&&............
..............&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&....&&&&&............
...........&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&......&&&&............
.........&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&.........&&&&............
.......&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&...........&&&&............
......&&&&&&&&&&&&&&&&&&&...&&&&&&...............&&&.............
.....&&&&&&&&&&&&&&&&............................&&..............
....&&&&&&&&&&&&&&&.................&&...........................
...&&&&&&&&&&&&&&&.....................&&&&......................
...&&&&&&&&&&.&&&........................&&&&&...................
..&&&&&&&&&&&..&&..........................&&&&&&&...............
..&&&&&&&&&&&&...&............&&&.....&&&&...&&&&&&&.............
..&&&&&&&&&&&&&.................&&&.....&&&&&&&&&&&&&&...........
..&&&&&&&&&&&&&&&&..............&&&&&&&&&&&&&&&&&&&&&&&&.........
..&&.&&&&&&&&&&&&&&&&&.........&&&&&&&&&&&&&&&&&&&&&&&&&&&.......
...&&..&&&&&&&&&&&&.........&&&&&&&&&&&&&&&&...&&&&&&&&&&&&......
....&..&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&...........&&&&&&&&.....
.......&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&..............&&&&&&&....
.......&&&&&.&&&&&&&&&&&&&&&&&&..&&&&&&&&...&..........&&&&&&....
........&&&.....&&&&&&&&&&&&&.....&&&&&&&&&&...........&..&&&&...
.......&&&........&&&.&&&&&&&&&.....&&&&&.................&&&&...
.......&&&...............&&&&&&&.......&&&&&&&&............&&&...
........&&...................&&&&&&.........................&&&..
.........&.....................&&&&........................&&....
...............................&&&.......................&&......
................................&&......................&&.......
.................................&&..............................
..................................&..............................
'''

'''Analysis:
token life time = 20s
code refresh = 30s
status changing = 10s
login fobbiden time = 20s

status 1: connection refused
status 2:(enter:expire session 
         leave:expire session)
         message:Internal Server Error
status 3: message:Bad Gateway

token died:message:invalid or expired jwt
repeated logins:message:Forbidden

if token expired , must relogin
'''
'''Diary:
day 3:上面是测试结果，有想法：可以做一个线程专门用来heartbeat，检测状态，加一个计时器，到时间且网络正常就直接发请求。
day 3:昨天的思路较为暴力了，疯狂发请求，直到可以提交。但是已经有了今天的雏形
day 3:我看status 2只有开头和末尾会毁掉session，其实之间是可以正常运行的，但是会产生很多登陆日志，这个就要考虑一下了
day 4:基本上做好了整体架构。成功做出第一版。
'''

import requests,json,time,threading

signup_url = 'http://127.0.0.1:1323/signup'
login_url="http://127.0.0.1:1323/login"
heartbeat_url="http://127.0.0.1:1323/api/heartbeat"
info_url="http://127.0.0.1:1323/api/info"
validate_url="http://127.0.0.1:1323/api/validate"
user_name = {'username': 'dailin'}
token=''
status=0    #status 4 就是失去session
wait=30     #等待代码刷新
success=0   #成功次数
beat_delay=5 #心跳间隔

def get_data(user_name):
    res = requests.post(url=signup_url, data=user_name)
    return json.loads(res.text)

def login(user_data):
    global token
    res = json.loads(requests.post(url=login_url, data=user_data).text)
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
        print(res)

def token_update():
    global token,status
    headers={
        "Authorization": "Bearer "+token 
    }
    try:
        res=json.loads(requests.get(url=heartbeat_url,headers=headers).text)
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
            #print("update:"+res["token"][:10])   this is a test log
            token=res["token"]
            status = 0

    except Exception as e:
        if "Connection refused" in str(e):
            status = 1 
        #status 1

    

def get_code(token):
    headers={
        "Authorization": "Bearer "+token 
    }
    res=json.loads(requests.get(info_url,headers=headers).text)
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
    res=json.loads(requests.post(validate_url,headers=headers,data=data).text)
    print(res)

def heart_beat():
    global wait,status,token
    while True:
        token_update()
        print("status:"+str(status))
        if status == 4 or status == 2:  #可以更好的抓住status 2作为提交机会
            print("relogin to get new token...")
            login(user_data)
        wait+=beat_delay
        time.sleep(beat_delay)

for i in range(100):
    try:
        user_data=get_data(user_name=user_name)
        login(user_data)
        break
    except Exception as e:
        print("try again...")
        time.sleep(10)
        #确保在网络异常时获得用户信息

beat=threading.Thread(target=heart_beat)
beat.start()
#开始心跳，来检查服务器状态

while True:
    if wait>30 and status==0:#条件允许，则提交code
        code=get_code(token)
        post_code(code=code,token=token)
        success+=1
        print(f"it is the {success} success!!!!!!!")
        wait=0