import sys
import json
import hashlib
import datetime
import os
import threading
import io
import ssl
import urllib3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import requests
from tqdm import tqdm
import websocket
import base64
import hmac
import secrets
import time

urllib3.disable_warnings()


# 以下配置变量统一由 config.json 提供，不再硬编码默认值
api_url = ""
use_https = True
protocol = ""
ws_protocol = ""
SECRET_KEY = ""

login_url = ""
info_url = ""
user_url = ""
bulletin_url = ""
upload_url = ""
avatar_url = ""


def generate_signature(data: dict, secret_key: str = None) -> str:
    """生成请求签名（密钥来自 config.json）"""
    secret_key = secret_key or SECRET_KEY
    filtered_data = {k: v for k, v in data.items() if v is not None}
    sorted_data = sorted(filtered_data.items())
    sign_str = '&'.join([f'{k}={v}' for k, v in sorted_data])
    
    print(f"[DEBUG] 签名字符串: {sign_str}")
    
    signature = hmac.new(
        secret_key.encode('utf-8'),
        sign_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"[DEBUG] 签名结果: {signature}")
    return signature

def generate_nonce(length: int = 16) -> str:
    """生成随机 nonce"""
    return secrets.token_hex(length)


def load_config():
    """加载配置文件（所有配置项均来自 config.json）"""
    global api_url, use_https, protocol, ws_protocol, SECRET_KEY
    global login_url, info_url, user_url, bulletin_url, upload_url, avatar_url
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        api_url = str(config.get("api_url", "")).strip()
        if not api_url:
            return False, "config.json 缺少 api_url"
        use_https = bool(config.get("use_https", True))
        SECRET_KEY = str(config.get("SECRET_KEY", ""))
        if not SECRET_KEY:
            return False, "config.json 缺少 SECRET_KEY"
        protocol = "https" if use_https else "http"
        ws_protocol = "wss" if use_https else "ws"
        
        login_url = f"{protocol}://{api_url}/api_v3/login/"
        info_url = f"{protocol}://{api_url}/api_v3/function_info_api_v3/"
        user_url = f"{protocol}://{api_url}/api_v3/function_user_api_v3/"
        bulletin_url = f"{protocol}://{api_url}/api_v3/bulletinboard_api_v3/"
        upload_url = f"{protocol}://{api_url}/api_v3/upload_logfile_api_v3/"
        avatar_url = f"{protocol}://{api_url}/api_v3/GetAvatar_api_v3/"
        
        return True, ""
    except Exception as e:
        return False, str(e)


class LoginThread(QThread):
    finished = pyqtSignal(dict, str)

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        try:
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            

            sign_data = {
                'Account': self.username,
                'password': self.password,
                'timestamp': timestamp,
                'nonce': nonce,
            }
            signature = generate_signature(sign_data)
            

            resp = requests.post(
                login_url,
                data={
                    'Account': self.username,
                    'password': self.password,
                    'timestamp': timestamp,
                    'nonce': nonce,
                    'signature': signature,
                },
                timeout=5,
                verify=False
            )
            
            if resp.status_code == 200:
                self.finished.emit(resp.json(), "")
            else:
                error_msg = resp.text
                try:
                    error_data = resp.json()
                    error_msg = error_data.get('error', resp.text)
                except:
                    pass
                self.finished.emit({}, f"登录失败: {resp.status_code} - {error_msg}")
        except Exception as e:
            self.finished.emit({}, f"请求错误: {e}")


class InfoThread(QThread):
    finished = pyqtSignal(object, str)

    def run(self):
        try:
            resp = requests.post(info_url, data={}, timeout=5, verify=False)
            if resp.status_code == 200:
                self.finished.emit(resp.json(), "")
            else:
                self.finished.emit({}, f"获取失败: {resp.status_code}")
        except Exception as e:
            self.finished.emit({}, f"请求错误: {e}")


class UserOpThread(QThread):
    finished = pyqtSignal(str, str)

    def __init__(self, uid, opid, session_token):
        super().__init__()
        self.uid = uid
        self.opid = opid
        self.session_token = session_token

    def run(self):
        try:
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            
            sign_data = {
                'uuids': self.uid,
                'opid': self.opid,
                'session_token': self.session_token,
                'timestamp': timestamp,
                'nonce': nonce,
            }
            signature = generate_signature(sign_data)
            

            resp = requests.post(
                user_url,
                data={
                    'uuids': self.uid,
                    'opid': self.opid,
                    'session_token': self.session_token,
                    'timestamp': timestamp,
                    'nonce': nonce,
                    'signature': signature,
                },
                verify=False
            )
            
            if resp.status_code == 200:
                self.finished.emit(json.dumps(resp.json(), ensure_ascii=False, indent=2), "")
            else:
                error_msg = resp.text
                try:
                    error_data = resp.json()
                    error_msg = error_data.get('error', resp.text)
                except:
                    pass
                self.finished.emit("", f"操作失败: {resp.status_code} - {error_msg}")
        except Exception as e:
            self.finished.emit("", f"请求错误: {e}")


class BulletinThread(QThread):
    finished = pyqtSignal(str, str)

    def __init__(self, bid=""):
        super().__init__()
        self.bid = bid

    def run(self):
        try:
            if self.bid:
                resp = requests.post(bulletin_url, data={'id': self.bid}, timeout=5, verify=False)
            else:
                resp = requests.post(bulletin_url, timeout=5, verify=False)

            if resp.status_code == 200:
                data = resp.json()
                self.finished.emit(data.get('text', '无内容'), "")
            else:
                self.finished.emit("", f"获取失败: {resp.status_code}")
        except Exception as e:
            self.finished.emit("", f"请求错误: {e}")


class UploadThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str, str)

    def __init__(self, filepath, account, uuid):
        super().__init__()
        self.filepath = filepath
        self.account = account
        self.uuid = uuid

    def run(self):
        try:
            size = os.path.getsize(self.filepath)
            buf = io.BytesIO()
            with open(self.filepath, "rb") as f:
                uploaded = 0
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    buf.write(chunk)
                    uploaded += len(chunk)
                    self.progress.emit(uploaded, size)
            buf.seek(0)

            files = {
                "file": (os.path.basename(self.filepath), buf, "application/octet-stream")
            }
            r = requests.post(
                upload_url,
                data={"Account": self.account, "uuid": self.uuid},
                files=files,
                timeout=None,
                verify=False
            )

            if r.text and r.headers.get('Content-Type', '').startswith('application/json'):
                self.finished.emit(json.dumps(r.json(), ensure_ascii=False, indent=2), "")
            else:
                self.finished.emit("", f"上传响应异常: {r.status_code}")
        except Exception as e:
            self.finished.emit("", f"上传错误: {e}")



class AvatarThread(QThread):
    finished = pyqtSignal(QPixmap, str)

    def __init__(self, uuid):
        super().__init__()
        self.uuid = uuid

    def run(self):
        try:
            resp = requests.post(avatar_url, data={'uuid': self.uuid}, timeout=10, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                base64_str = data.get('avatar_base64', '')
                if base64_str:
                    if ',' in base64_str:
                        base64_str = base64_str.split(',', 1)[1]
                    
                    image_data = base64.b64decode(base64_str)
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    
                    if not pixmap.isNull():
                        self.finished.emit(pixmap, "")
                    else:
                        self.finished.emit(QPixmap(), "图片解码失败")
                else:
                    self.finished.emit(QPixmap(), data.get('error', '获取头像失败'))
            else:
                self.finished.emit(QPixmap(), f"请求失败: {resp.status_code}")
        except Exception as e:
            self.finished.emit(QPixmap(), f"请求错误: {e}")



class WSThread(QThread):
    status_changed = pyqtSignal(str)

    def __init__(self, uuid):
        super().__init__()
        self.uuid = uuid
        self.ws_app = None
        self.running = True

    def run(self):
        ws_url = f"{ws_protocol}://{api_url}/ws/user/{self.uuid}/"

        def on_open(ws):
            self.status_changed.emit("✅ WebSocket 已连接")

        def on_close(ws, code, msg):
            self.status_changed.emit("❌ WebSocket 已断开")

        def on_error(ws, err):
            self.status_changed.emit(f"⚠️ WebSocket 错误: {err}")

        self.ws_app = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=lambda ws, msg: None,
            on_close=on_close,
            on_error=on_error,
        )
        self.ws_app.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False})

    def stop(self):
        if self.ws_app:
            self.ws_app.close()
        self.running = False



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user = {}
        self.account = None
        self.ws_thread = None
        self.avatar_pixmap = None
        self.session_token = None
        self.init_ui()
        self.update_status()

    def init_ui(self):
        self.setWindowTitle("AT API 测试工具")
        self.setMinimumSize(700, 550)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)


        title = QLabel("AT API 测试工具")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px; color: #2c3e50;")
        layout.addWidget(title)


        top_layout = QHBoxLayout()
        
        avatar_group = QGroupBox("头像")
        avatar_layout = QVBoxLayout(avatar_group)
        
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(120, 120)
        self.avatar_label.setStyleSheet("border: 2px solid #ccc; border-radius: 60px; background-color: #f0f0f0;")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setText("未登录")
        avatar_layout.addWidget(self.avatar_label, alignment=Qt.AlignCenter)
        
        self.btn_avatar = QPushButton("获取头像")
        self.btn_avatar.clicked.connect(self.get_avatar)
        self.btn_avatar.setEnabled(False)
        avatar_layout.addWidget(self.btn_avatar)
        
        top_layout.addWidget(avatar_group)

        status_group = QGroupBox("状态信息")
        status_layout = QGridLayout(status_group)

        self.account_label = QLabel("账号: 未登录")
        self.uuid_label = QLabel("UUID: 未登录")
        self.info_label = QLabel("功能信息: 未获取")
        self.ws_label = QLabel("连接状态: 未连接")
        self.token_label = QLabel("会话令牌: 未获取")

        status_layout.addWidget(self.account_label, 0, 0)
        status_layout.addWidget(self.uuid_label, 1, 0)
        status_layout.addWidget(self.info_label, 2, 0)
        status_layout.addWidget(self.ws_label, 3, 0)
        status_layout.addWidget(self.token_label, 4, 0)

        top_layout.addWidget(status_group)
        top_layout.setStretchFactor(avatar_group, 1)
        top_layout.setStretchFactor(status_group, 2)

        layout.addLayout(top_layout)


        btn_group = QGroupBox("操作")
        btn_layout = QGridLayout(btn_group)

        self.btn_login = QPushButton("1. 用户登录")
        self.btn_info = QPushButton("2. 获取功能信息")
        self.btn_user = QPushButton("3. 操作用户")
        self.btn_bulletin = QPushButton("4. 请求公告")
        self.btn_upload = QPushButton("5. 上传文件")
        self.btn_logout = QPushButton("6. 退出登录")

        self.btn_login.clicked.connect(self.show_login_dialog)
        self.btn_info.clicked.connect(self.get_info)
        self.btn_user.clicked.connect(self.show_user_op_dialog)
        self.btn_bulletin.clicked.connect(self.show_bulletin_dialog)
        self.btn_upload.clicked.connect(self.show_upload_dialog)
        self.btn_logout.clicked.connect(self.logout)

        btn_layout.addWidget(self.btn_login, 0, 0)
        btn_layout.addWidget(self.btn_info, 0, 1)
        btn_layout.addWidget(self.btn_user, 1, 0)
        btn_layout.addWidget(self.btn_bulletin, 1, 1)
        btn_layout.addWidget(self.btn_upload, 2, 0)
        btn_layout.addWidget(self.btn_logout, 2, 1)

        layout.addWidget(btn_group)


        log_group = QGroupBox("输出日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)

        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_btn)

        layout.addWidget(log_group)

        self.log("程序启动完成，请登录")

    def log(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")

    def update_status(self):
        account_display = self.account or self.user.get('Account') or self.user.get('account') or '未登录'
        self.account_label.setText(f"账号: {account_display}")
        self.uuid_label.setText(f"UUID: {self.user.get('uuid') or '未登录'}")
        info_str = "未获取"
        if self.user.get('uuid'):
            info_str = "已登录"
        self.info_label.setText(f"功能信息: {info_str}")
        
        token_display = self.session_token[:16] + '...' if self.session_token else '未获取'
        self.token_label.setText(f"会话令牌: {token_display}")

        is_logged_in = bool(self.user.get('uuid'))
        self.btn_info.setEnabled(is_logged_in)
        self.btn_user.setEnabled(is_logged_in and bool(self.session_token))
        self.btn_upload.setEnabled(is_logged_in)
        self.btn_logout.setEnabled(is_logged_in)
        self.btn_avatar.setEnabled(is_logged_in)

    def set_ws_status(self, status):
        self.ws_label.setText(f"连接状态: {status}")


    def get_avatar(self):
        if not self.user.get('uuid'):
            QMessageBox.warning(self, "提示", "请先登录")
            return


        if hasattr(self, '_last_avatar_time'):
            now = time.time()
            if now - self._last_avatar_time < 5:
                remaining = 5 - (now - self._last_avatar_time)
                self.log(f"⚠️ 获取头像太频繁，请等待 {remaining:.1f} 秒")
                QMessageBox.warning(self, "提示", f"请等待 {remaining:.1f} 秒后再试")
                return
        
        self._last_avatar_time = time.time()
        self.log("正在获取头像...")
        self.btn_avatar.setEnabled(False)
        self.avatar_label.setText("加载中...")

        self.avatar_thread = AvatarThread(self.user['uuid'])
        self.avatar_thread.finished.connect(self.on_avatar_done)
        self.avatar_thread.start()

    def on_avatar_done(self, pixmap, error):
        self.btn_avatar.setEnabled(True)
        
        if error:
            if '操作过于频繁' in error:
                self.log(f"获取头像失败: {error}")
                self.avatar_label.setText("⏳")
                QMessageBox.warning(self, "提示", error)
                return
            
            self.log(f"获取头像失败: {error}")
            self.avatar_label.setText("❌")
            QMessageBox.warning(self, "获取头像失败", error)
            return

        if pixmap.isNull():
            self.log("获取头像失败: 图片为空")
            self.avatar_label.setText("无头像")
            return

        scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        rounded = self.make_rounded_pixmap(scaled_pixmap)
        self.avatar_label.setPixmap(rounded)
        self.avatar_label.setText("")
        self.avatar_pixmap = pixmap
        self.log("头像获取成功")

    def make_rounded_pixmap(self, pixmap):
        size = min(pixmap.width(), pixmap.height())
        rounded = QPixmap(size, size)
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        painter.drawPixmap(0, 0, size, size, pixmap)
        painter.end()
        
        return rounded


    def show_login_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("用户登录")
        dialog.setFixedWidth(350)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("账号:"))
        username_edit = QLineEdit()
        layout.addWidget(username_edit)

        layout.addWidget(QLabel("密码:"))
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btn_box)

        def do_login():
            username = username_edit.text().strip()
            password = password_edit.text().strip()
            if not username or not password:
                QMessageBox.warning(dialog, "提示", "账号或密码不能为空")
                return

            self.log(f"正在登录: {username}")
            self.btn_login.setEnabled(False)
            
            self.login_username = username

            self.login_thread = LoginThread(username, password)
            self.login_thread.finished.connect(lambda data, err: self.on_login_done(data, err, dialog))
            self.login_thread.start()

        btn_box.accepted.connect(do_login)
        btn_box.rejected.connect(dialog.reject)
        dialog.exec_()

    def on_login_done(self, data, error, dialog):
        self.btn_login.setEnabled(True)
        if error:
            self.log(f"登录失败: {error}")
            QMessageBox.warning(self, "登录失败", error)
            return

        self.log(f"登录返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        self.user = data
        self.account = data.get('Account') or data.get('account') or getattr(self, 'login_username', '')
        

        self.session_token = data.get('session_token', None)
        
        self.log(f"登录成功: {self.account} (UUID: {self.user.get('uuid')})")
        if self.session_token:
            self.log(f"会话令牌: {self.session_token[:16]}...")
        
        dialog.accept()

        if self.user.get('uuid'):
            self.start_ws(self.user['uuid'])

            QTimer.singleShot(1000, self.get_avatar)

        self.update_status()
        
        msg = f"登录成功！\n账号: {self.account}"
        if self.session_token:
            msg += f"\n会话令牌: {self.session_token[:16]}..."
        QMessageBox.information(self, "成功", msg)


    def start_ws(self, uuid):
        if self.ws_thread:
            self.ws_thread.stop()
            self.ws_thread.wait()

        self.ws_thread = WSThread(uuid)
        self.ws_thread.status_changed.connect(self.set_ws_status)
        self.ws_thread.start()
        self.log("WebSocket 线程已启动")

    def stop_ws(self):
        if self.ws_thread:
            self.ws_thread.stop()
            self.ws_thread.wait()
            self.ws_thread = None
            self.set_ws_status("未连接")
            self.log("WebSocket 已关闭")


    def get_info(self):
        self.log("正在获取功能信息...")
        self.btn_info.setEnabled(False)

        self.info_thread = InfoThread()
        self.info_thread.finished.connect(self.on_info_done)
        self.info_thread.start()

    def on_info_done(self, data, error):
        self.btn_info.setEnabled(True)
        if error:
            self.log(f"获取功能信息失败: {error}")
            QMessageBox.warning(self, "失败", error)
            return

        data_type = "列表" if isinstance(data, list) else "对象"
        self.log(f"功能信息获取成功 ({data_type}, {len(data)} 项)")
        self.info_label.setText(f"功能信息: 已获取 ({len(data)} 项)")
        self.show_result_dialog("功能信息", json.dumps(data, ensure_ascii=False, indent=2))


    def show_user_op_dialog(self):
        if not self.session_token:
            QMessageBox.warning(self, "提示", "请先登录获取会话令牌")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("操作用户")
        dialog.setFixedWidth(350)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("用户 UUID:"))
        uid_edit = QLineEdit()
        uid_edit.setText(self.user.get('uuid', ''))
        layout.addWidget(uid_edit)

        layout.addWidget(QLabel("操作类型 ID:"))
        opid_edit = QLineEdit()
        layout.addWidget(opid_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btn_box)

        def do_user_op():
            uid = uid_edit.text().strip()
            opid = opid_edit.text().strip()
            if not uid or not opid:
                QMessageBox.warning(dialog, "提示", "UUID 和操作ID不能为空")
                return

            self.log(f"正在操作用户: {uid} (OPID: {opid})")
            dialog.accept()

            self.user_op_thread = UserOpThread(uid, opid, self.session_token)
            self.user_op_thread.finished.connect(self.on_user_op_done)
            self.user_op_thread.start()

        btn_box.accepted.connect(do_user_op)
        btn_box.rejected.connect(dialog.reject)
        dialog.exec_()

    def on_user_op_done(self, result, error):
        if error:
            self.log(f"操作用户失败: {error}")
            QMessageBox.warning(self, "失败", error)
            return

        self.log("操作用户成功")
        self.show_result_dialog("操作用户结果", result)

    def show_bulletin_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("请求公告")
        dialog.setFixedWidth(350)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("公告 ID (留空获取最新):"))
        bid_edit = QLineEdit()
        layout.addWidget(bid_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btn_box)

        def do_bulletin():
            bid = bid_edit.text().strip()
            self.log(f"正在获取公告: {bid or '最新'}")
            dialog.accept()

            self.bulletin_thread = BulletinThread(bid)
            self.bulletin_thread.finished.connect(self.on_bulletin_done)
            self.bulletin_thread.start()

        btn_box.accepted.connect(do_bulletin)
        btn_box.rejected.connect(dialog.reject)
        dialog.exec_()

    def on_bulletin_done(self, text, error):
        if error:
            self.log(f"获取公告失败: {error}")
            QMessageBox.warning(self, "失败", error)
            return

        self.log("公告获取成功")
        self.show_result_dialog("公告内容", text)


    def show_upload_dialog(self):
        if not self.user.get('uuid'):
            QMessageBox.warning(self, "提示", "请先登录")
            return

        filepath, _ = QFileDialog.getOpenFileName(self, "选择要上传的文件")
        if not filepath:
            return

        self.log(f"开始上传文件: {os.path.basename(filepath)}")

        progress_dialog = QProgressDialog("正在上传...", "取消", 0, 100, self)
        progress_dialog.setWindowTitle("上传进度")
        progress_dialog.setModal(True)
        progress_dialog.show()

        self.upload_thread = UploadThread(filepath, self.account, self.user['uuid'])
        self.upload_thread.progress.connect(lambda cur, total: progress_dialog.setValue(int(cur / total * 100)))
        self.upload_thread.finished.connect(lambda result, err: self.on_upload_done(result, err, progress_dialog))
        self.upload_thread.start()

    def on_upload_done(self, result, error, progress_dialog):
        progress_dialog.close()
        if error:
            self.log(f"上传失败: {error}")
            QMessageBox.warning(self, "上传失败", error)
            return

        self.log("上传成功")
        self.show_result_dialog("上传结果", result)


    def logout(self):
        self.stop_ws()
        self.user = {}
        self.account = None
        self.session_token = None
        self.avatar_pixmap = None
        self.avatar_label.setText("未登录")
        self.avatar_label.setPixmap(QPixmap())
        self.log("已退出登录")
        self.update_status()
        QMessageBox.information(self, "提示", "已退出登录")


    def show_result_dialog(self, title, content):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(text_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec_()



if __name__ == "__main__":

    app = QApplication(sys.argv)

    success, msg = load_config()
    if not success:
        QMessageBox.critical(None, "错误", f"未找到 config.json 或读取失败：{msg}")
        sys.exit(1)
    

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())