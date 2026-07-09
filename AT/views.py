from django.shortcuts import render, redirect ,get_object_or_404
from django.http import HttpResponse,JsonResponse ,HttpResponseRedirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from database import models as database
import os
import time
import  uuid
from datetime import datetime,timedelta
import hashlib
from django.utils import timezone
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from django.urls import reverse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import platform
import sys 
import django
from AT.online_state import ONLINE_USERS,ONLINE_INFO 
from PIL import Image
from .forms import *
import pytz
from utils.security import generate_signature, verify_signature, verify_timestamp, generate_nonce
import base64
from django.db.models import Q 
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
layer = get_channel_layer()


def home(request):
    if not request.session.get('Account'):
        user_list = None
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    latest_bbs = database.bbs.objects.order_by('-id').first()
    asgi_info = "Unknown"
    
    try:
        import daphne
        asgi_info = f"Daphne {daphne.__version__}"
    except ImportError:
        try:
            import uvicorn
            asgi_info = f"Uvicorn {uvicorn.__version__}"
        except ImportError:
            try:
                import hypercorn
                asgi_info = f"Hypercorn {hypercorn.__version__}"
            except ImportError:
                asgi_info = "No ASGI server detected"
    info = {
        'django_version': django.get_version(),
        'python_version': f"{platform.python_version()} ({platform.python_implementation()})",
        'os': platform.platform(),
        'asgi_info': asgi_info,
        'architecture': platform.machine(),
        'sys_version': sys.version.replace('\n', ' '),
    }
    return render(request, "home.html", context={
        "user_list": user_list,
        "latest_bbs": latest_bbs,
        "info": info,
    })


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/home')

def Download(request):
    if not request.session.get('Account'):
        user_list = None
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    try:
        latest_download = database.DownloadUrls.objects.order_by('-id').first()
    except database.DownloadUrls.DoesNotExist:
        latest_download = None

    return render(request, "download.html", context={
        "user_list": user_list,
        "latest_download": latest_download,
    })




def user(request):
    account = request.session.get('Account')
    if not account:
        return redirect('/login/')
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    

    if user_list and ONLINE_USERS.get(user_list.UniqueIdentification, None):
        info={"OnlinStatus":"在线"}
    else:
        info={"OnlinStatus":"离线"}
    query = request.GET.get('q', '').strip()

    return render(request, 'user.html', {
        'user_list': user_list,
        'info': info,
        'query': query,

    })

def usersettings(request):
    try:
        Account = request.session['Account']
    except KeyError:
        Account = None
    if not Account:
        return redirect('/login/')
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    return render(request, "usersettings.html",context={
        "user_list":user_list,
    })

def ChangeNickname(request):
    try:
        Account = request.session['Account']
    except KeyError:
        Account = None
    if not Account:
        return redirect('/login/')
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    if request.method == "POST":
        username = request.POST.get("username")
        if not username:
            usersettings = {"TxtHide":"block","Txt":"请输入新的昵称再更改！"}
            return render(request, "usersettings.html", {"usersettings": usersettings,"user_list":user_list})
        database.users.objects.filter(Account=request.session['Account']).update(nick_name=username)
        usersettings = {"TxtHide":"block","Txt":"更改完成！"}
        OperationLog(
            Account=Account,
            uuid=database.users.objects.get(Account=Account).UniqueIdentification,
            operation_type='ChangeNickname',
            description=f'用户 {Account} 重命名成功'
        )
        return render(request, "usersettings.html", {"usersettings": usersettings,"user_list":user_list})

def ClientOffline(request):
    try:
        Account = request.session['Account']
    except KeyError:
        Account = None
    if not Account:
        return redirect('/login/')

    user = database.users.objects.filter(Account=Account).first()
    if not user:
        return redirect('/login/')

    channel_name = ONLINE_USERS.pop(user.UniqueIdentification, None)
    info = ONLINE_INFO.pop(user.UniqueIdentification, None)

    if channel_name:
        async_to_sync(layer.send)(channel_name, {"type": "force_close"})
        async_to_sync(layer.group_send)(
            'online_admin',
            {
                'type': 'online_event',
                'payload': {'is_online': False, **info},
            }
        )
        usersettings = {"TxtHide": "block", "Txt": "已将客户端踢下线！"}
        return render(request, "usersettings.html", {"usersettings": usersettings, "user_list": user})
    else:
        usersettings = {"TxtHide": "block", "Txt": "用户不在线！"}
        return render(request, "usersettings.html", {"usersettings": usersettings, "user_list": user})

    

def ChangePassword(request):
    try:
        Account = request.session['Account']
    except KeyError:
        Account = None
    if not Account:
        return redirect('/login/')
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    if request.method == "POST":
        key = request.POST.get("password")
        if not key:
            usersettings = {"TxtHide":"block","Txt":"请输入新的密码再更改！"}
            return render(request, "usersettings.html", {"usersettings": usersettings,"user_list":user_list})
        database.users.objects.filter(Account=request.session['Account']).update(password=key)
        usersettings = {"TxtHide":"block","Txt":"更改完成！请重新登陆！"}
        OperationLog(
            Account=Account,
            uuid=database.users.objects.get(Account=Account).UniqueIdentification,
            operation_type='ChangePassword',
            description=f'用户 {Account} 重设密码成功'
        )
        auth.logout(request)
        return render(request, "usersettings.html", {"usersettings": usersettings,"user_list":user_list})
    
def PermanentlyLogout(request):
    try:
        Account = request.session['Account']
    except KeyError:
        Account = None
    if not Account:
        return redirect('/login/')
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    if request.method == "POST":
        fileids = database.users.objects.filter(Account=request.session['Account'])
        temp = database.users.objects.get(Account=Account)
        fileids.delete()
        usersettings = {"TxtHide":"block","Txt":"注销帐号完成！"}
        OperationLog(
            Account=Account,
            uuid=temp.UniqueIdentification,
            operation_type='PermanentlyLogout',
            description=f'用户 {Account} 永久注销成功'
        )
        auth.logout(request)
        return render(request, "usersettings.html", {"usersettings": usersettings,"user_list":user_list})
def Resetuuid(request):
    Account = request.session.get('Account')
    if not Account:
        return redirect('/login/')
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    last_reset = database.OperationLog.objects.filter(
        uuid=user_list.UniqueIdentification,
        operation_type='Resetuuid'
    ).order_by('-operation_time').first()

    if last_reset and timezone.now() < last_reset.operation_time + timedelta(hours=3):
        remaining = (last_reset.operation_time + timedelta(hours=3)) - timezone.now()
        usersettings = {
            "TxtHide": "block",
            "Txt": f"冷却中，请 {int(remaining.total_seconds())} 秒后再试"
        }
        return render(request, "usersettings.html",
                      {"usersettings": usersettings, "user_list": user_list})
    new_uuid = str(uuid.uuid4().hex)[:16]
    while database.users.objects.filter(UniqueIdentification=new_uuid).exists():
        new_uuid = str(uuid.uuid4().hex)[:16]

    user_list.UniqueIdentification = new_uuid
    user_list.save(update_fields=['UniqueIdentification'])
    OperationLog(
            Account=Account,
            uuid=new_uuid,
            operation_type='Resetuuid',
            description=f'用户 {Account} 重置 UUID 成功'
        )
    usersettings = {"TxtHide": "block", "Txt": "重置 UUID 完成！"}
    return render(request, "usersettings.html",
                  {"usersettings": usersettings, "user_list": user_list})

def ChangeSignature(request):
    try:
        Account = request.session['Account']
    except KeyError:
        Account = None
    if not Account:
        return redirect('/login/')
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None
    if request.method == "POST":
        Signature = request.POST.get("Signature")
        if not Signature:
            usersettings = {"TxtHide":"block","Txt":"请输入签名再更改！"}
            return render(request, "usersettings.html", {"usersettings": usersettings,"user_list":user_list})
        database.users.objects.filter(Account=request.session['Account']).update(signature=Signature)
        usersettings = {"TxtHide":"block","Txt":"更改完成！"}
        OperationLog(
            Account=Account,
            uuid=database.users.objects.get(Account=Account).UniqueIdentification,
            operation_type='ChangeSignature',
            description=f'用户 {Account} 更改签名完成'
        )
        return render(request, "usersettings.html", {"usersettings": usersettings,"user_list":user_list})
    


def ChangeAvatar(request):
    try:
        Account = request.session['Account']
    except KeyError:
        Account = None
    if not Account:
        return redirect('/login/')
    else:
        try:
            user_list = database.users.objects.get(Account=request.session['Account'])
        except database.users.DoesNotExist:
            user_list = None

    if request.method == "POST":
        myFile = request.FILES.get("file", None)
        if not myFile:
            usersettings = {"TxtHide": "block", "Txt": "请选择头像文件！"}
            return render(request, "usersettings.html", {"usersettings": usersettings, "user_list": user_list})

        allowed_extensions = ['jpg', 'png', 'jpeg']
        _, file_extension = os.path.splitext(myFile.name)
        ext = file_extension.lstrip('.').lower()
        if ext not in allowed_extensions:
            usersettings = {"TxtHide": "block", "Txt": "只能上传jpg,jpeg,png文件！"}
            return render(request, "usersettings.html", {"usersettings": usersettings, "user_list": user_list})

        try:
            img = Image.open(myFile)
            img.verify()
            img = Image.open(myFile)
            if img.format.lower() not in ['jpeg', 'png']:
                usersettings = {"TxtHide": "block", "Txt": "图片内容格式不正确！"}
                return render(request, "usersettings.html", {"usersettings": usersettings, "user_list": user_list})
        except Exception:
            usersettings = {"TxtHide": "block", "Txt": "文件内容不是有效图片！"}
            return render(request, "usersettings.html", {"usersettings": usersettings, "user_list": user_list})

        width, height = img.size
        if width != height:
            min_edge = min(width, height)
            left = (width - min_edge) // 2
            top = (height - min_edge) // 2
            right = left + min_edge
            bottom = top + min_edge
            img = img.crop((left, top, right, bottom))

        time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{Account}_{time_str}.{ext}"

        upload_dir = "static/avatar"
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, new_filename)
        img.save(save_path)

        database.users.objects.filter(Account=request.session['Account']).update(avatar=new_filename)


        OperationLog(
            Account=Account,
            uuid=database.users.objects.get(Account=Account).UniqueIdentification,
            operation_type='ChangeAvatar',
            description=f'用户 {Account} 更改头像完成'
        )

        usersettings = {"TxtHide": "block", "Txt": "头像上传完成"}
        return render(request, "usersettings.html", {"usersettings": usersettings, "user_list": user_list})

@csrf_exempt
def logins(request):
    Account = request.session.get('Account')
    try:
        if request.session['Account']:
            try:
                user_list = database.users.objects.get(Account=Account)
            except database.users.DoesNotExist:
                auth.logout(request)
    except KeyError:
        pass
    try:
        user_list = database.users.objects.get(Account=Account)
    except database.users.DoesNotExist or KeyError:
        user_list = None
    
    
    method = request.method
    if method == "GET":
        return render(request, "login.html",context={
        "user_list":user_list,})
    elif method == "POST":
        Account = request.POST.get("Account")
        password = request.POST.get("password")
        try:
            user = database.users.objects.get(Account=Account)
            if user.is_banned:
                login = {"Txt":"账号已被封禁!",'HomePpage':'none','SignUp':'block','REENTRY':'block'}

            if user.password == password:
                request.session['Account'] = user.Account

                login = {"Txt":"登陆成功!",'HomePpage':'block','SignUp':'none','REENTRY':'none'}
                OperationLog(
                    Account=Account,
                    uuid=user.UniqueIdentification,
                    operation_type='login',
                    description=f'用户 {Account} 网页登录成功'
                )
                database.users.objects.filter(Account=Account).update(last_login=datetime.now())
                
            else:
                login = {"Txt":"密码错误，请重新输入密码!",'HomePpage':'none','SignUp':'block','REENTRY':'block'}
                
        except database.users.DoesNotExist:
            login = {"Txt":"用户名不存在!",'HomePpage':'none','SignUp':'block','REENTRY':'block'}
    return render(request, "login.html", context={
        "user_list":user_list,
        "login": login})

@csrf_exempt
def login_api_v3(request):
    method = request.method
    if method == "GET":
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        Account = request.POST.get("Account")
        password = request.POST.get("password")
        timestamp = request.POST.get("timestamp")
        nonce = request.POST.get("nonce")
        signature = request.POST.get("signature")
        

        print(f"[DEBUG] 收到登录请求:")
        print(f"  Account: {Account}")
        print(f"  password: {password}")
        print(f"  timestamp: {timestamp}")
        print(f"  nonce: {nonce}")
        print(f"  signature: {signature}")
        
        if not all([Account, password, timestamp, nonce, signature]):
            return JsonResponse({
                'error': '缺少必要参数',
                'required': ['Account', 'password', 'timestamp', 'nonce', 'signature']
            }, status=400)
        

        try:
            timestamp_int = int(timestamp)
            current_time = int(time.time())
            print(f"[DEBUG] 当前时间: {current_time}, 请求时间: {timestamp_int}, 差值: {abs(current_time - timestamp_int)}")
            if abs(current_time - timestamp_int) > 300:
                return JsonResponse({'error': '请求已过期，请重试'}, status=401)
        except ValueError:
            return JsonResponse({'error': '时间戳格式无效'}, status=400)
        

        sign_data = {
            'Account': Account,
            'password': password,
            'timestamp': timestamp,
            'nonce': nonce,
        }
        

        server_signature = generate_signature(sign_data)
        print(f"[DEBUG] 服务端计算的签名: {server_signature}")
        print(f"[DEBUG] 客户端传来的签名: {signature}")
        print(f"[DEBUG] 签名是否匹配: {server_signature == signature}")
        
        if not verify_signature(sign_data, signature):
            return JsonResponse({'error': '签名验证失败'}, status=401)

        try:
            user = database.users.objects.get(Account=Account)
            if user.is_banned:
                return JsonResponse({'error': '账号被封禁'}, status=403)
            
            if user.password != password:
                return JsonResponse({'error': '密码错误'}, status=401)

            session_token = hashlib.sha256(
                f"{Account}{nonce}{settings.SECRET_KEY}".encode()
            ).hexdigest()
            
            OperationLog(
                Account=Account,
                uuid=user.UniqueIdentification,
                operation_type='login_api_v3',
                description=f'用户 {Account} 通过API登录成功 (加密版本)'
            )
            
            database.users.objects.filter(Account=Account).update(last_login=datetime.now())
            
            return JsonResponse({
                'info': '登录成功',
                'uuid': user.UniqueIdentification,
                'is_banned': user.is_banned,
                'is_vip': user.is_vip,
                'ds': str(user.coins),
                'session_token': session_token,
                'expires_in': 3600,
            }, status=200)
            
        except database.users.DoesNotExist:
            return JsonResponse({'error': '用户名不存在'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': f'服务器错误: {str(e)}'}, status=500)

@csrf_exempt
def function_info_api_v3(request):
    method = request.method
    if method == "GET":
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    else:
        operationtypes = database.operationtype.objects.all()
        data = [
            {
                'id': ot.id,
                'name': ot.name,
                'coins': ot.coins
            } for ot in operationtypes
        ]
        return JsonResponse(data, safe=False, status=200)
    
@csrf_exempt
def bulletinboard_api_v3(request):
    method = request.method
    if method == "GET":
         return JsonResponse({'error': '仅支持POST请求'}, status=405)
    else:
        try:
            id = request.POST.get("id")
        except KeyError:
            id = None
        if not id:
            try:
                latest_bbs = database.BulletinBoard_api.objects.order_by('-id').first()
                if latest_bbs:
                    return JsonResponse({'info': '获取成功',
                                        'text':f'{latest_bbs.content}',
                                        },
                                        safe=False,status=200)
                else:
                    return JsonResponse({'error': '暂无公告'}, status=404)
            except database.BulletinBoard_api.DoesNotExist:
                return JsonResponse({'error': '暂无公告'}, status=404)
        else:
            try:
                bbs_item = database.BulletinBoard_api.objects.get(id=int(id))
                return JsonResponse({'info': '获取成功',
                                     'text':f'{bbs_item.content}',
                                     },
                                    safe=False,status=200)
            except database.BulletinBoard_api.DoesNotExist:
                return JsonResponse({'error': '公告不存在'}, status=404)

      
@csrf_exempt
def GetAvatar_api_v3(request):
    method = request.method
    if method == "GET":
        return JsonResponse({'error': '仅支持POST请求'}, status=405)
    
    try:
        uuid = request.POST.get("uuid")
    except KeyError:
        uuid = None
    
    if not uuid:
        return JsonResponse({'error': '缺少参数"uuid"'}, status=404)
    
    user = database.users.objects.filter(UniqueIdentification=uuid)
    if not user.exists():
        return JsonResponse({'error': '用户不存在'}, status=404)
    
    avatar_filename = user.first().avatar
    if not avatar_filename:
        return JsonResponse({'error': '用户未设置头像'}, status=404)
    

    now_time = datetime.now().timestamp()
    
    last_record = database.OperationLog.objects.filter(
        uuid=uuid, 
        operation_type='GetAvatar'
    ).order_by('-operation_time').first()
    
    if last_record:
        up_time = last_record.operation_time.timestamp()
        time_diff = now_time - up_time
        
        if time_diff < 5:
            remaining = 5 - time_diff
            return JsonResponse({
                'error': f'操作过于频繁，请等待 {remaining:.1f} 秒后再试'
            }, status=429)


    avatar_path = os.path.join(settings.BASE_DIR, 'static', 'avatar', avatar_filename)
    
    try:
        with open(avatar_path, 'rb') as f:
            image_data = f.read()
            base64_str = base64.b64encode(image_data).decode('utf-8')
    except FileNotFoundError:
        return JsonResponse({'error': '头像文件不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'读取头像失败: {str(e)}'}, status=500)
    

    ext = os.path.splitext(avatar_filename)[1].lower()
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp',
        '.svg': 'image/svg+xml',
    }
    mime_type = mime_map.get(ext, 'application/octet-stream')
    
    Account = database.users.objects.get(UniqueIdentification=uuid).Account
    
    OperationLog(
        Account=Account,
        uuid=uuid,
        operation_type='GetAvatar',
        description=f'用户 {Account} 获取了头像 {avatar_filename}'
    )
    
    return JsonResponse({
        'info': '获取成功',
        'avatar_base64': f'data:{mime_type};base64,{base64_str}',
        'filename': avatar_filename,
        'size': len(image_data)
    }, status=200)
    
def OperationLog(Account,uuid,operation_type,description):
    try:
        database.users.objects.get(Account=Account)
    except database.users.DoesNotExist:
        return False
    if database.OperationLog.objects.create(
        Account=Account,
        uuid=uuid,
        operation_type=operation_type,
        operation_time=time_now(),
        description=description
    ):
        return True
    else:
        return False
    
def time_now():
    return timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE))

@csrf_exempt 
def upload_file_api_v3(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        Account = request.POST.get("Account")
        uuid = request.POST.get("uuid")
        print(Account)
        if not Account:
            return JsonResponse({'error': '未登录'}, status=403)
        else:
            try:
                database.users.objects.get(Account=Account)
            except database.users.DoesNotExist:
                return JsonResponse({'error': '未找到用户'}, status=403)
            
        if not uuid:
            return JsonResponse({'error': 'uuid为空'}, status=400)
        else:
            if database.users.objects.get(Account=Account).UniqueIdentification == uuid:
                pass
            else:
                return JsonResponse({'error': 'uuid不匹配'}, status=403)
            if ONLINE_USERS.get(uuid, None):
                pass
            else:
                return JsonResponse({'error': '客户端不在线'}, status=403)
        if not file:
            return JsonResponse({'error': '文件为空'}, status=400)
        last_log = (database.OperationLog.objects
                .filter(Account=Account, operation_type='upload_file')
                .order_by('-operation_time')
                .first())
        if last_log:
            elapsed = (time_now() - last_log.operation_time).total_seconds()
            if elapsed < settings.UPLOAD_OPTIME:
                return JsonResponse({'error': f'上传过于频繁，还需等待 {int(settings.UPLOAD_OPTIME) - int(elapsed)} 秒'}, status=429)
        if file.size > settings.MAX_UPLOAD_SIZE:
            return JsonResponse({'error': f'文件大小超过 {settings.MAX_UPLOAD_SIZE}，拒绝上传'}, status=413)
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        safe_ts = time_now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{Account}_{safe_ts}_{file.name}"
        dest_path = os.path.join(upload_dir, new_name)
        with open(dest_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        database.UploadFile.objects.create(
            file=f"{upload_dir}/{new_name}",
            upload_time=datetime.now(),
            Account=Account,
            FileType="log"
        )
        OperationLog(
            Account=Account,
            uuid=database.users.objects.get(Account=Account).UniqueIdentification,
            operation_type='upload_file',
            description=f'用户 {Account} 上传日志文件 {file.name}'
        )
        return JsonResponse({'message': '文件上传成功'}, status=200)
    else:
        return JsonResponse({'error': '仅支持POST请求'}, status=405)
    

@csrf_exempt  
def function_user_api_v3(request):
    if request.method != "POST":
        return JsonResponse({'error': '仅支持POST请求'}, status=405)
    
    try:

        uuids = request.POST.get("uuids")
        opid = request.POST.get("opid")
        session_token = request.POST.get("session_token")
        timestamp = request.POST.get("timestamp")
        nonce = request.POST.get("nonce")
        signature = request.POST.get("signature")
        client_key = request.POST.get("client_key")
        

        if not all([uuids, opid, session_token, timestamp, nonce, signature]):
            return JsonResponse({
                'error': '缺少必要参数',
                'required': ['uuids', 'opid', 'session_token', 'timestamp', 'nonce', 'signature']
            }, status=400)

        try:
            timestamp_int = int(timestamp)
            if not verify_timestamp(timestamp_int, timeout=300):
                return JsonResponse({'error': '请求已过期，请重试'}, status=401)
        except ValueError:
            return JsonResponse({'error': '时间戳格式无效'}, status=400)
        

        if len(nonce) < 16:
            return JsonResponse({'error': 'nonce 长度不足'}, status=400)

        if len(session_token) != 64:  # SHA256 固定长度
            return JsonResponse({'error': '会话令牌无效'}, status=401)

        sign_data = {
            'uuids': uuids,
            'opid': opid,
            'session_token': session_token,
            'timestamp': timestamp,
            'nonce': nonce,
        }
        
        if not verify_signature(sign_data, signature):
            return JsonResponse({'error': '签名验证失败'}, status=401)
        

        try:
            op_type = database.operationtype.objects.get(id=opid)
        except database.operationtype.DoesNotExist:
            return JsonResponse({'error': '操作ID不存在'}, status=404)
        

        if not ONLINE_USERS.get(uuids, None):
            return JsonResponse({'error': '用户未在线，操作被拒绝'}, status=409)

        try:
            user = database.users.objects.get(UniqueIdentification=uuids)
            if user.is_banned:
                return JsonResponse({'error': '该用户被封禁'}, status=403)
            if user.coins + op_type.coins < 0:
                return JsonResponse({'error': '用户点数不足'}, status=403)
            
            user.coins += op_type.coins
            user.save()
        except database.users.DoesNotExist:
            return JsonResponse({'error': '用户不存在'}, status=404)
        

        OperationLog(
            Account=user.Account,
            uuid=user.UniqueIdentification,
            operation_type=op_type.name,
            description=f'用户 {user.Account} 执行操作 {op_type.name}，点数变更 {op_type.coins}'
        )
        
        import time
        response_data = {
            'message': '操作成功',
            'ds': str(user.coins),
            'timestamp': str(int(time.time())),
        }
        

        response_signature = generate_signature(response_data)
        response_data['signature'] = response_signature
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        return JsonResponse({'error': f'服务器错误: {str(e)}'}, status=500)
    
def captcha():
    hashkey = CaptchaStore.generate_key()
    image_url = captcha_image_url(hashkey)
    return {'hashkey': hashkey, 'image_url': image_url}

def refresh_captcha(request):
    return HttpResponse(json.dumps(captcha()), content_type='application/json')

@csrf_exempt
def register(request):
    try:
        if request.session['Account']:
            return HttpResponseRedirect('/home')
    except KeyError:
        pass
    Account = request.session.get('Account')
    try:
        user_list = database.users.objects.get(Account=Account)
    except database.users.DoesNotExist:
        user_list = None
    if request.method == "GET":
        hashkey = CaptchaStore.generate_key()
        return render(request, "register.html", {
            "captcha_0": hashkey,
            "user_list":user_list,
        })
    elif request.method == "POST":
        captcha_key = request.POST.get('captcha_0')
        captcha_value = request.POST.get('captcha_1')

        try:
            CaptchaStore.objects.get(hashkey=captcha_key, response=captcha_value.lower())
        except CaptchaStore.DoesNotExist:
            hashkey = CaptchaStore.generate_key()
            return render(request, "register.html", {
                "captcha_0": hashkey,
                "captcha_error": "验证码错误",
                "user_list":user_list,
            })


        Account = request.POST.get('Account')
        pwd = request.POST.get('password1')
        rePwd = request.POST.get('password2')
        registrationcode = request.POST.get('registrationcode')
        if database.users.objects.filter(Account=Account):
            register = {'Txt':'账号已被注册！','SignIn':'none','SignUp':'block'}
        elif len(Account) < 6:
            register = {'Txt':'账号少于6位数！','SignIn':'none','SignUp':'block'}
        elif pwd != rePwd:
            register = {'Txt':'两次密码不一致!','SignIn':'none','SignUp':'block'}
            
        elif not database.registrationcode.objects.filter(codes=registrationcode):
            register = { 'Txt': '注册码不存在!', 'SignIn': 'none', 'SignUp': 'block'}

        elif database.registrationcode.objects.get(codes=registrationcode).is_used:
            register = {'Txt': '注册码已被使用!', 'SignIn': 'none', 'SignUp': 'block'}
            
        else:
            temp_id = str(uuid.uuid4().hex)[:16]
            while database.users.objects.filter(UniqueIdentification=temp_id).exists():
                temp_id = str(uuid.uuid4().hex)[:16]
            user = database.users.objects.create(Account=Account, password=rePwd, UniqueIdentification=temp_id,date_joined=timezone.now())
            user.save()
            database.registrationcode.objects.filter(codes=registrationcode).update(user=Account,is_used=True,used_time=datetime.now())
            register = { 'Txt': '注册完成！','SignIn': 'block', 'SignUp': 'none'}
            OperationLog(
                Account=Account,
                uuid=user.UniqueIdentification,
                operation_type='register',
                description=f'用户 {Account} 注册成功'
            )

            
        return render(request, "register.html"
                       ,context={
        "user_list":user_list,
        "register": register})


def DeveloperDocumentation(request):
    Account = request.session.get('Account')
    try:
        user_list = database.users.objects.get(Account=Account)
    except database.users.DoesNotExist:
        user_list = None
    if not Account:
        return redirect('/login/')
    else:
        user = database.users.objects.filter(Account=Account).first()
        if not user:
            auth.logout(request)
            return redirect(reverse('login'))

        if not user.is_developer:
            info = {"txt":"403!你没有访问权限！","tile":"403错误"}
            return render(request, "error.html",context={
                    "user_list":user_list,
                    "info":info,
                }, status=403)
        database.OperationLog.objects.create(
            Account=Account,
            uuid=user.UniqueIdentification,
            operation_type='view_developer_documentation',
            description=f'用户 {Account} 查看开发者文档'
        )

    # 获取所有启用的文档章节和API端点
    sections = database.APIDocSection.objects.filter(is_active=True).order_by('order')
    endpoints = database.APIEndpoint.objects.filter(is_active=True).order_by('order')

    return render(request, "DeveloperDocumentation.html",context={
        "user_list":user_list,
        "sections": sections,
        "endpoints": endpoints,
    })



@csrf_exempt
def paste_upload_image(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'msg': '仅支持POST请求'}, status=405)

    Account = request.session.get('Account')
    if not Account:
        return JsonResponse({'code': 403, 'msg': '请先登录'}, status=403)

    try:
        user_list = database.users.objects.get(Account=Account)
    except database.users.DoesNotExist:
        return JsonResponse({'code': 403, 'msg': '用户不存在'}, status=403)

    try:
        file = request.FILES.get('image')
        if not file:
            return JsonResponse({'code': 400, 'msg': '未获取到图片文件'}, status=400)
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return JsonResponse({'code': 400, 'msg': '仅支持jpg/png/gif/webp格式'}, status=400)

        try:
            img = Image.open(file)
            img.verify()
            img = Image.open(file)
            if img.format.lower() not in ['jpeg', 'png', 'gif', 'webp']:
                return JsonResponse({'code': 400, 'msg': '图片内容格式不正确'}, status=400)
        except Exception:
            return JsonResponse({'code': 400, 'msg': '文件内容不是有效图片'}, status=400)

        file_ext = os.path.splitext(file.name)[-1]
        if not file_ext:
            file_ext = '.png'
        time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"paste_{Account}_{time_str}{file_ext}"

        upload_dir = os.path.join("static", "uploads", datetime.now().strftime('%Y%m%d'))
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, file_name)

        with open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        image_url = save_path.replace('\\', '/')

        return JsonResponse({
            'code': 200,
            'msg': '上传成功',
            'data': {'image_url': image_url, 'image_name': file_name}
        }, status=200)
    except Exception as e:
        return JsonResponse({'code': 500, 'msg': f'上传失败：{str(e)}'}, status=500)
