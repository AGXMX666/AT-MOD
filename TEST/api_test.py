import requests, websocket, json, hashlib, datetime, os, threading, time, urllib3
import argparse
urllib3.disable_warnings()
import ssl
import json
from tqdm import tqdm
import io

config = None
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print("[错误] 未找到 config.json 或读取失败：", e)
    input("请在当前目录下创建 config.json 配置文件，回车退出...")
    exit(1)

api_url = config.get("api_url", "127.0.0.1:8000")
use_https = config.get("use_https", True)
protocol = "https" if use_https else "http"
ws_protocol = "wss" if use_https else "ws"

login_url = f"{protocol}://{api_url}/api_v3/login/"
info_url  = f"{protocol}://{api_url}/api_v3/function_info_api_v3/"
user_url  = f"{protocol}://{api_url}/api_v3/function_user_api_v3/"

user    = {}
info    = {}
ws_info = "未连接服务器"
ws_app  = None
global Account_in
Account_in = None

def ws_thread_func(uuid):
    global ws_info, ws_app
    ws_url = f"{ws_protocol}://{api_url}/ws/user/{uuid}/"

    def on_open(ws):
        global ws_info
        ws_info = "✅ WebSocket 已连接"
        print("\n[WS] 已连接，保持监听...\n")

    def on_close(ws, code, msg):
        global ws_info
        ws_info = "❌ WebSocket 已断开"
        print("\n[WS] 连接断开\n")

    def on_error(ws, err):
        global ws_info
        ws_info = f"⚠️ WebSocket 错误: {err}"
        print("\n[WS] 错误:", err, "\n")

    ws_app = websocket.WebSocketApp(ws_url,
                                    on_open=on_open,
                                    on_message=lambda ws, msg: None,
                                    on_close=on_close,
                                    on_error=on_error,
                                    )
    ws_app.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False})

def start_ws(uuid):
    t = threading.Thread(target=ws_thread_func, args=(uuid,), daemon=True)
    t.start()

def stop_ws():
    global ws_app, ws_info
    if ws_app:
        ws_app.close()
    ws_app  = None
    ws_info = "未连接服务器"

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("AT API测试")
    print("=" * 20)
    print("1. 用户登录")
    print("2. 获取功能信息")
    print("3. 操作用户")
    print("4. 请求公告")
    print("5. 上传文件")
    print("6. 退出登录")
    print("=" * 20)
    print(f"账号: {Account_in or '未登录'}")
    print(f"uuid: {user.get('uuid') or '未登录'}")
    print(f"功能信息: {info if info else '未获取'}")
    print(f"连接状态: {ws_info}")
    choice = input("请选择操作 (1/2/3/4/5): ").strip()
    if choice == '1':
        login()
    elif choice == '2':
        get_function_info()
    elif choice == '3':
        function_user()
    elif choice == '4':
        request_bulletin_board()
    elif choice == '5':
        uploadfile(user.get('uuid'))
    elif choice == '6':
        logout()
    else:
        main()

def login():
    global user
    username = input("账号: ").strip()
    password = input("密码: ").strip()
    if not username or not password:
        input("账号或密码不能为空，回车返回..."); main(); return
    try:
        resp = requests.post(login_url, data={'Account': username, 'password': password},
                             timeout=5, verify=False)
        if resp.status_code == 200:
            user = resp.json()
            global Account_in
            Account_in =username

            start_ws(user['uuid'])
        else:
            print("登录失败:", resp.status_code, resp.text)
    except Exception as e:
        print("请求错误:", e)
    input("回车返回主菜单..."); main()

def get_function_info():
    global info
    try:
        resp = requests.post(info_url, data={}, timeout=5, verify=False)
        info = resp.json() if resp.status_code == 200 else {}
        print("功能信息:", info or resp.text)
    except Exception as e:
        print("请求错误:", e)
    input("回车返回主菜单..."); main()

def function_user():
    uid = user.get('uuid') or input("用户UUID: ").strip()
    opid = input("操作类型ID: ").strip()
    if not uid or not opid:
        input("UUID/操作ID不能为空，回车返回..."); main(); return
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M')
    key = hashlib.sha256(f'{ts}{uid}{ts}'.encode()).hexdigest()
    try:
        resp = requests.post(user_url, data={'uuids': uid, 'opid': opid, 'key': key},
                             verify=False)
        print("结果:", resp.status_code, resp.json() if resp.status_code == 200 else resp.text)
    except Exception as e:
        print("请求错误:", e)
    input("回车返回主菜单..."); main()

def request_bulletin_board():
    id = input("公告ID (留空获取最新): ").strip()
    print("")
    try:
        if not id:
            resp = requests.post(f"{protocol}://{api_url}/api_v3/bulletinboard_api_v3/", timeout=5, verify=False)
        else:
            resp = requests.post(f"{protocol}://{api_url}/api_v3/bulletinboard_api_v3/",data={'id':id} ,timeout=5, verify=False)
        
        if resp.status_code == 200:
            data = resp.json()
            print("公告内容:", data.get('text', '无内容'))
        else:
            print("获取失败:", resp.status_code, resp.text)
    except Exception as e:
        print("请求错误:", e)
    print("")
    input("回车返回主菜单..."); main()

def uploadfile(uuid):
    global Account_in
    while True:
        path = input("输入文件路径(输入back返回上一级): ").strip().strip('"\'')
        if path == "back":
            main()
        elif not os.path.isfile(path):
            print("❌ 路径无效或不是文件，请重新输入！")
            continue
        break
    size = os.path.getsize(path)
    buf = io.BytesIO()
    with open(path, "rb") as f, tqdm(total=size, unit="B", unit_scale=True, desc="upload") as bar:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            buf.write(chunk)
            bar.update(len(chunk))
    buf.seek(0)
    files = {
        "file":    (os.path.basename(path), buf, "application/octet-stream")
    }
    r = requests.post(
        f"{protocol}://{api_url}/api_v3/upload_logfile_api_v3/",
        data={
            "Account":  Account_in,
            "uuid":    uuid,
        },
        files=files,
        timeout=None,
        verify=False
    )
    if r.text and r.headers.get('Content-Type', '').startswith('application/json'):
        try:
            print('[JSON]', r.json())
        except Exception as e:
            print('[WARN] 无法解析 JSON:', e)
    else:
        print('[WARN] 服务端未返回 JSON 内容')
    input("回车返回主菜单...")
    main()

def logout():
    global user, info, Account_in
    stop_ws()
    user = {}           
    info = {}          
    Account_in = None
    print("已退出登录")
    input("回车返回主菜单..."); main()

if __name__ == "__main__":
    main()