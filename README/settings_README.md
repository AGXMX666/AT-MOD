# 配置说明 - settings.py

## 2025-10-20更新速看
- 新增配置"MAX_UPLOAD_SIZE","UPLOAD_OPTIME"2个变量，用于设置"api_v3/upload_logfile_api_v3/"路由的上传文件的某些参数。
- "MAX_UPLOAD_SIZE"是设置文件大小限制，单位为字节（Byte），默认值为 `10485760` （即 10MB）。如果上传的文件超过此限制，则会返回错误信息。
- "UPLOAD_OPTIME"是设置文用户上传文件的间隔，默认是 60s 。

## 文件位置

`AT/settings.py` 是 Django 项目的核心配置文件，包含了项目的所有主要设置。

## 配置内容

### 1. DEBUG 模式

- **字段**: `DEBUG`
- **说明**: 控制是否启用调试模式。
- **示例**:
  ```python
  DEBUG = True  # 开发环境
  DEBUG = False # 生产环境
  ```

### 2. 数据库配置

- **字段**: `DATABASES`
- **说明**: 配置项目使用的数据库。
- **示例**:
  ```python
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': BASE_DIR / 'db.sqlite3',
      }
  }
  ```
- **注意**: 生产环境建议使用 MySQL 或 PostgreSQL。

### 3. 静态文件配置

- **字段**: `STATIC_URL` 和 `STATICFILES_DIRS`
- **说明**: 配置静态文件的访问路径。
- **示例**:
  ```python
  STATIC_URL = '/static/'
  STATICFILES_DIRS = [
      BASE_DIR / 'static',
  ]
  ```

### 4. 模板配置

- **字段**: `TEMPLATES`
- **说明**: 配置模板引擎和模板路径。
- **示例**:
  ```python
  TEMPLATES = [
      {
          'BACKEND': 'django.template.backends.django.DjangoTemplates',
          'DIRS': [BASE_DIR / 'templates'],
          'APP_DIRS': True,
          'OPTIONS': {
              'context_processors': [
                  'django.template.context_processors.debug',
                  'django.template.context_processors.request',
                  'django.contrib.auth.context_processors.auth',
                  'django.contrib.messages.context_processors.messages',
              ],
          },
      },
  ]
  ```

### 5. 语言和时区

- **字段**: `LANGUAGE_CODE` 和 `TIME_ZONE`
- **说明**: 配置项目的语言和时区。
- **示例**:
  ```python
  LANGUAGE_CODE = 'zh-hans'
  TIME_ZONE = 'Asia/Shanghai'
  ```

### 6. 安全配置

- **字段**: `ALLOWED_HOSTS`
- **说明**: 配置允许访问的主机名。
- **示例**:
  ```python
  ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'example.com']
  ```

### 7. 日志配置

- **字段**: `LOGGING`
- **说明**: 配置日志记录。
- **示例**:
  ```python
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'handlers': {
          'console': {
              'class': 'logging.StreamHandler',
          },
      },
      'root': {
          'handlers': ['console'],
          'level': 'WARNING',
      },
  }
  ```

## 注意事项

1. **生产环境配置**:
   - 如果有能力部署daphne和配置静态资源则 `DEBUG = False`，否则建议`DEBUG = True`，因为关闭DEBUG会导致静态资源无法加载，你担心页面报错会泄露重要信息？我们特意去写了中间件控制这个，你在`DEBUG = True`之后可以去`DEBUG_PAGE_OFF = True`,这样可以有效拦截django原本的报错页面。
   - 配置 `ALLOWED_HOSTS`。
   - 使用安全的数据库和静态文件存储。

2. **敏感信息**:
   - 不要将敏感信息（如 SECRET_KEY、数据库密码）直接写入代码。
   - 使用环境变量或配置文件管理敏感信息。

3. **扩展配置**:
   - 根据需要扩展 `INSTALLED_APPS` 和 `MIDDLEWARE`。

## 参考文档

- [Django 官方文档 - settings](https://docs.djangoproject.com/en/stable/ref/settings/)