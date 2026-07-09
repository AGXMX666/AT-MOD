from django.db import models
from django.utils import timezone
from datetime import datetime
from django.conf import settings
import uuid
from channels.generic.websocket import WebsocketConsumer
import json
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from AT.online_state import ONLINE_USERS, ONLINE_INFO
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)
layer = get_channel_layer()


def generate_default_nickname():
    """生成默认昵称的函数"""
    return f'AT用户{random.randint(10000000, 99999999)}'


class Users(models.Model):
    """用户模型"""
    # 基本信息
    Account = models.CharField(max_length=12, unique=True, verbose_name='账号', db_index=True)
    nick_name = models.CharField(
        max_length=20,
        default=generate_default_nickname,
        verbose_name='昵称'
    )
    password = models.CharField(max_length=100, verbose_name='密码')
    avatar = models.CharField(max_length=200, default='default/default.png', verbose_name='头像')
    signature = models.CharField(max_length=60, default='这是新的一天', verbose_name='签名')
    UniqueIdentification = models.CharField(
        max_length=16,
        verbose_name='唯一标识',
        blank=True, 
        unique=True,
        db_index=True
    )

    # 状态字段
    is_banned = models.BooleanField(default=False, verbose_name='是否封禁')
    is_vip = models.BooleanField(default=False, verbose_name='是否VIP')
    is_developer = models.BooleanField(default=False, verbose_name='是否开发者')

    # 数值字段
    coins = models.IntegerField(default=0, verbose_name='金币')

    # 时间字段
    last_login = models.DateTimeField(default=timezone.now, verbose_name='最后登录时间')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='注册时间')

    def save(self, *args, **kwargs):
        if not self.UniqueIdentification:
            unique_id = str(uuid.uuid4().hex)[:16]
            while Users.objects.filter(UniqueIdentification=unique_id).exists():
                unique_id = str(uuid.uuid4().hex)[:16]
            self.UniqueIdentification = unique_id
        if not self.nick_name:
            self.nick_name = generate_default_nickname()
        super().save(*args, **kwargs)

    def _kick_sync(self, uid: str) -> bool:
        """同步踢出用户"""
        ch = ONLINE_USERS.pop(uid, None)
        info = ONLINE_INFO.pop(uid, None)
        if ch:
            async_to_sync(layer.send)(ch, {"type": "force_close"})
            async_to_sync(layer.group_send)(
                'online_admin',
                {'type': 'online_event', 'payload': list(ONLINE_INFO.values())}
            )
            return True
        return False

    def kick_now(self):
        """立即踢出用户"""
        return executor.submit(self._kick_sync, self.UniqueIdentification).result()

    def ban_now(self):
        """立即封禁用户"""
        self.is_banned = True
        self.save(update_fields=['is_banned'])
        self.kick_now()

    def __str__(self):
        return self.Account

    class Meta:
        db_table = "user"
        managed = True
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-date_joined']


# 为了向后兼容，保留旧的类名作为别名
users = Users


class RegistrationCode(models.Model):
    """注册码模型"""
    codes = models.CharField(max_length=20, unique=True, verbose_name='注册码', db_index=True)
    user = models.CharField(max_length=50, verbose_name='使用账号', blank=True)
    is_used = models.BooleanField(default=False, verbose_name='是否已使用')
    used_time = models.DateTimeField(verbose_name='使用时间', blank=True, null=True)
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    def __str__(self):
        return self.codes

    class Meta:
        db_table = "RegistrationCode"
        managed = True
        verbose_name = '注册码'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']


# 为了向后兼容，保留旧的类名作为别名
registrationcode = RegistrationCode


class OperationLog(models.Model):
    """操作日志模型"""
    Account = models.CharField(max_length=50, verbose_name='账号', blank=True, db_index=True)
    uuid = models.CharField(max_length=16, verbose_name='用户唯一标识', db_index=True)
    operation_type = models.CharField(max_length=50, verbose_name='操作类型', db_index=True)
    operation_time = models.DateTimeField(default=timezone.now, verbose_name='操作时间', db_index=True)
    description = models.TextField(verbose_name='操作描述', blank=True, null=True)

    def __str__(self):
        return f"{self.Account} - {self.operation_type}"

    class Meta:
        db_table = "OperationLog"
        managed = True
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name
        ordering = ['-operation_time']


class OperationType(models.Model):
    """操作类型模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='操作名称')
    coins = models.IntegerField(default=0, verbose_name='点数变化')
    description = models.TextField(verbose_name='说明', blank=True)
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    def __str__(self):
        return self.name

    class Meta:
        db_table = "operationtype"
        managed = True
        verbose_name = '操作类型'
        verbose_name_plural = verbose_name


# 为了向后兼容，保留旧的类名作为别名
operationtype = OperationType


class DownloadUrls(models.Model):
    """下载链接模型"""
    title = models.CharField(verbose_name='名称', max_length=50, default='NEWPROGRAM')
    urls = models.URLField(verbose_name='下载链接', max_length=500)
    image = models.URLField(verbose_name='演示图片链接', max_length=500, blank=True)
    text = models.TextField(verbose_name='说明(支持html)', blank=True, null=True)
    height = models.IntegerField(default=400, verbose_name='高度(px)', null=True)
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    def __str__(self):
        return self.title

    class Meta:
        db_table = "downloadurls"
        managed = True
        verbose_name = '下载链接'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']


class BBS(models.Model):
    """首页公告模型"""
    title = models.CharField(max_length=100, verbose_name='标题', blank=True)
    text = models.TextField(verbose_name='首页内容(支持html)')
    height = models.IntegerField(default=800, verbose_name='高度(px)', null=True)
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    def __str__(self):
        return self.title or f'公告 {self.id}'

    class Meta:
        db_table = "bbs"
        managed = True
        verbose_name = '首页公告'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']


# 为了向后兼容，保留旧的类名作为别名
bbs = BBS


class BulletinBoardAPI(models.Model):
    """API公告模型"""
    title = models.CharField(max_length=50, verbose_name='标题', blank=True, null=True)
    content = models.TextField(verbose_name='内容')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    def __str__(self):
        return self.title or f'API公告 {self.id}'

    class Meta:
        db_table = "BulletinBoard"
        managed = True
        verbose_name = '公告API'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']


# 为了向后兼容，保留旧的类名作为别名
BulletinBoard_api = BulletinBoardAPI


class UploadFile(models.Model):
    """上传文件模型"""
    FILE_TYPE_CHOICES = [
        ('log', '日志文件'),
        ('image', '图片文件'),
        ('document', '文档文件'),
        ('other', '其他文件'),
    ]

    file = models.FileField(upload_to='static/uploads/admin/%Y%m%d/', verbose_name='文件')
    upload_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    Account = models.CharField(max_length=50, verbose_name='上传用户', blank=True, db_index=True)
    FileType = models.CharField(
        max_length=20,
        verbose_name='文件类型',
        choices=FILE_TYPE_CHOICES,
        default='other'
    )

    def __str__(self):
        return f"{self.Account} - {self.file.name}"

    class Meta:
        db_table = "UploadFile"
        managed = True
        verbose_name = '上传文件'
        verbose_name_plural = verbose_name
        ordering = ['-upload_time']




class UserConsumer(WebsocketConsumer):
    """WebSocket消费者"""
    def connect(self):
        uuid = self.scope['url_route']['kwargs']['uuid']
        try:
            self.user = Users.objects.get(UniqueIdentification=uuid)
            self.accept()
            print(f"{self.user.Account} 上线")
        except Users.DoesNotExist:
            self.close()

    def disconnect(self, close_code):
        if hasattr(self, 'user'):
            print(f"{self.user.Account} 下线")

    def receive(self, text_data):
        data = json.loads(text_data)
        self.send(text_data=json.dumps({
            "from": self.user.nick_name,
            "message": data.get("message")
        }))


class APIEndpoint(models.Model):
    """API端点模型 - 用于管理API文档"""
    name = models.CharField(max_length=100, verbose_name='API名称')
    endpoint = models.CharField(max_length=200, verbose_name='端点路径')
    method = models.CharField(
        max_length=10,
        choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('DELETE', 'DELETE')],
        default='POST',
        verbose_name='请求方法'
    )
    description = models.TextField(verbose_name='接口描述')

    # 请求参数（JSON格式存储）
    request_params = models.TextField(
        verbose_name='请求参数(JSON格式)',
        help_text='格式: [{"name": "参数名", "type": "类型", "required": true, "description": "说明"}]',
        blank=True
    )

    # 响应示例
    response_success = models.TextField(verbose_name='成功响应示例', blank=True)
    response_error = models.TextField(verbose_name='错误响应示例', blank=True)

    # 代码示例
    code_python = models.TextField(verbose_name='Python示例', blank=True)
    code_javascript = models.TextField(verbose_name='JavaScript示例', blank=True)
    code_java = models.TextField(verbose_name='Java示例', blank=True)
    code_csharp = models.TextField(verbose_name='C#示例', blank=True)
    code_go = models.TextField(verbose_name='Go示例', blank=True)
    code_php = models.TextField(verbose_name='PHP示例', blank=True)

    # 其他信息
    notes = models.TextField(verbose_name='注意事项', blank=True)
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return f"{self.name} ({self.method} {self.endpoint})"

    class Meta:
        db_table = "api_endpoint"
        managed = True
        verbose_name = 'API端点'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']


class APIDocSection(models.Model):
    """API文档章节模型"""
    title = models.CharField(max_length=100, verbose_name='章节标题')
    content = models.TextField(verbose_name='章节内容(支持Markdown)')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return self.title

    class Meta:
        db_table = "api_doc_section"
        managed = True
        verbose_name = 'API文档章节'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']
