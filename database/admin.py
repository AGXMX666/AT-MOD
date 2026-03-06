from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from import_export.admin import ImportExportModelAdmin
from .models import *
from .resources import RegistrationCodeResource, BookResource
from django.utils.html import format_html
from datetime import datetime
from django.contrib import messages
from django.http import HttpResponseRedirect
admin.site.site_header = 'AT'
admin.site.site_title  = 'AT后台'

@admin.register(users)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'Account', 'nick_name', 'is_banned', 'is_vip', 'is_developer', 'coins',
        'UniqueIdentification', 'kick_button', 'ban_button'
    )
    list_filter = ('is_banned', 'is_vip', 'is_developer')
    readonly_fields = ('kick_button', 'ban_button')
    change_list_template = 'admin/users_changelist.html'

    def kick_button(self, obj):
        return format_html(
            '<a class="button" href="{}" onclick="return confirm(\'确定踢下线？\')">踢下线</a>',
            f'/admin/database/users/{obj.pk}/kick/'
        )
    kick_button.short_description = '踢线'

    def ban_button(self, obj):
        return format_html(
            '<a class="button" href="{}" onclick="return confirm(\'确定封号？\')">封号</a>',
            f'/admin/database/users/{obj.pk}/ban/'
        )
    ban_button.short_description = '封号'

    def get_urls(self):
        urls = super().get_urls()
        return [
            path('<int:pk>/kick/', self.kick_view),
            path('<int:pk>/ban/', self.ban_view),
        ] + urls

    def kick_view(self, request, pk):
        user = users.objects.get(pk=pk)
        ok = user.kick_now()        
        OperationLog.objects.create(
            Account=user.Account,
            uuid=user.UniqueIdentification,
            operation_type='kick',
            operation_time=datetime.now(),
            description=f'用户 {user.Account} 被管理员踢下线'
        )
        messages.success(request, f'{user.Account} 已被踢下线' if ok else '用户已不在线')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def ban_view(self, request, pk):
        user = users.objects.get(pk=pk)
        user.ban_now()               
        OperationLog.objects.create(
            Account=user.Account,
            uuid=user.UniqueIdentification,
            operation_type='ban',
            operation_time=datetime.now(),
            description=f'用户 {user.Account} 被管理员封禁'
        )
        messages.success(request, f'{user.nick_name} 已被封号')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
@admin.register(OperationLog) 
class LogAdmin(admin.ModelAdmin):
    list_display = ('Account','uuid', 'operation_type', 'operation_time','description')
    search_fields = ('uuid',)
    list_filter = ('operation_type',)

@admin.register(registrationcode)
class RegistrationCodeAdmin(ImportExportModelAdmin):
    resource_class = RegistrationCodeResource
    list_display = ('codes', 'user', 'is_used', 'used_time', 'created_time')
    search_fields = ('codes', 'user')
    list_filter = ('is_used',)

@admin.register(operationtype)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'coins')

@admin.register(DownloadUrls)
class DownloadUrlsAdmin(admin.ModelAdmin):
    list_display = ('title', 'urls', 'text', 'image', 'is_active', 'created_time')

@admin.register(bbs)
class bbsAdmin(admin.ModelAdmin):
     list_display = ('text','height') 


@admin.register(BulletinBoard_api)
class BulletinBoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'content')
    search_fields = ('title',)

@admin.register(UploadFile)
class UploadFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'upload_time', 'Account','FileType')
    search_fields = ('Account','file')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'postage')
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(ImportExportModelAdmin):
    resource_class = BookResource
    list_display = ('code', 'name', 'cost', 'supplier', 'shelf_time', 'is_display')
    list_filter = ('is_display', 'shelf_time', 'supplier')
    search_fields = ('code', 'name', 'supplier__name')
    list_editable = ('is_display',)

    def get_import_data_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_data_kwargs(request, *args, **kwargs)
        kwargs['user'] = request.user
        return kwargs

@admin.register(APIDocSection)
class APIDocSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_time', 'updated_time')
    list_filter = ('is_active',)
    search_fields = ('title', 'content')
    list_editable = ('order', 'is_active')
    ordering = ('order',)

@admin.register(APIEndpoint)
class APIEndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'endpoint', 'method', 'order', 'is_active', 'updated_time')
    list_filter = ('method', 'is_active')
    search_fields = ('name', 'endpoint', 'description')
    list_editable = ('order', 'is_active')
    ordering = ('order',)
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'endpoint', 'method', 'description', 'order', 'is_active')
        }),
        ('请求与响应', {
            'fields': ('request_params', 'response_success', 'response_error', 'notes')
        }),
        ('代码示例', {
            'fields': ('code_python', 'code_javascript', 'code_java', 'code_csharp', 'code_go', 'code_php'),
            'classes': ('collapse',)
        }),
    )

