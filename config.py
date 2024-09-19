#when your company update the servers, you can directly change the project's constant in this file. (ﾉ>ω<)ﾉ
import os

root_dir = os.path.abspath("..")
log_file = os.path.join(root_dir, "log")


signup_url = 'http://127.0.0.1:1323/signup'
login_url="http://127.0.0.1:1323/login"
heartbeat_url="http://127.0.0.1:1323/api/heartbeat"
info_url="http://127.0.0.1:1323/api/info"
validate_url="http://127.0.0.1:1323/api/validate"


secrets_key = "Hello_new_Byrs_1234123412341234"


beat_delay = 10
wait_code = 30
