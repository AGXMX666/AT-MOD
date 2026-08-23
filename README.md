# AT登录接口平台
[项目DEMO](https://frp-run.com:41414/)
## 项目简介
AT登录接口平台是一个基于Django开发的用户登录与管理系统，支持用户注册、登录、公告获取、用户信息管理等功能。平台集成了前后端页面、API接口、用户权限管理等模块，适用于需要统一用户认证和管理的场景。

## 目录结构说明

- `manage.py`：Django项目管理脚本。
- `AT/`：主应用目录
  - `settings.py`：Django配置文件。
  - `urls.py`：URL路由配置。
  - `views.py`：视图函数。
  - `forms.py`：表单定义。
  - `middleware.py`：中间件。
  - `consumers.py`：WebSocket相关。
  - `online_state.py`：在线状态管理。
  - `templates/`：前端模板页面（如登录、注册、主页等）。
- `database/`：数据库相关应用
  - `migrations/`：migrations文件夹。
   - `__init__.py`：init文件。
  - `models.py`：数据模型定义。
  - `admin.py`：后台管理配置。
  - `views.py`：数据库相关视图。
  - `templates/admin/`：后台管理页面模板。
- `static/`：静态资源
  - `css/`、`js/`、`img/`、`avatar/`等静态文件。
  - `uploads/`：上传文件存储目录。
- `README`：更多文档。
  - `settings_README.md`：settings.py配置说明。
- `templates/`：全局模板（如`base.html`）。
- `requirements.txt`：依赖包列表。
- `TEST/`：AT项目配套的工具。
   - `registration_codes_build.py`：方便生成注册码。
   - `api_test.py`：用于测试api。
   - `config.json`：api_test.py的配置文件。
- `README.md`：项目说明文档。

## 更多文档
[settings.py配置说明](README/settings_README.md)

## 安装与运行
1.**一些说明**
   建议使用python3.11版本及以上
2. **克隆项目到本地**
   ```bash
   git clone git@github.com:XEKZHX/AT.git
   cd AT
   ```
3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
4. **数据库迁移**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
5. **创建管理员**
   ```bash
   python manage.py createsuperuser
   ```
6. **启动服务**
   ```bash
   python manage.py runserver
   ```
7. **访问平台**
   - 前端页面: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - 后台管理: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

8. **使用 daphne 启动**
   - 收集静态资源
    ```bash
   python manage.py collectstatic
    ```
   - daphne服务启动
    ```bash
   daphne -b 0.0.0.0 -p 8000 AT.asgi:application
    ```

9. **环境变量配置（可选，生产环境推荐）**
   - `DJANGO_SECRET_KEY`：Django 密钥，生产环境务必设置。
   - `API_SECRET_KEY`：API 签名共享密钥，需与客户端保持一致，建议与 `DJANGO_SECRET_KEY` 分开设置。
   - `DJANGO_DEBUG`：设为 `False` 关闭调试模式（Windows 下双击 `start.bat` 已默认关闭）。
   - `DJANGO_SESSION_COOKIE_SECURE` / `DJANGO_CSRF_COOKIE_SECURE`：Cookie 的 Secure 标记开关，本地用 http 访问时设为 `False`，否则无法登录。

10. **关于静态资源与关闭 DEBUG**
    - 项目内置静态文件服务，关闭 `DEBUG` 后前端页面（css/js/img）与运行时上传文件（头像、日志）仍可正常访问，无需 nginx。
    - 后台管理界面（admin/SimpleUI）的样式文件会自动从应用安装包内加载，无需 `collectstatic` 也能正常显示。
    - 生产环境仍建议执行 `python manage.py collectstatic` 将静态文件收集到 `resources/` 目录，提升加载性能。
    
## 推荐使用虚拟环境（venv）部署

强烈建议在项目根目录下使用 Python 虚拟环境（venv）进行依赖隔离和部署，避免与全局环境冲突。

### 步骤如下：

1. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```
2. **激活虚拟环境**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
4. **后续操作**
   - 后续所有命令（如数据库迁移、启动服务等）均在虚拟环境激活状态下进行。
   - 退出虚拟环境：
     ```bash
     deactivate
     ```

> 建议每次开发或部署前先激活虚拟环境，确保依赖一致性。

## 主要功能

- 用户注册与登录
- 用户信息管理与设置
- 公告API获取
- 用户列表与权限管理
- 静态资源与美化页面
- 后台管理界面

## 更新日志

- **2026-08-23**
   - **功能性修复**：
      - 修复登录接口封禁检查失效问题：被封禁账号此前仍可通过正确密码登录，现已拦截。
      - 修复注册码导入导出字段与模型不匹配的问题。
      - 修复 `manage.py` 中异常捕获拼写错误，Django 未安装时能给出正确提示。
      - 修复文件上传接口变量遮蔽问题：局部变量 `uuid` 遮蔽模块导致上传报错，已改名 `client_uuid`。
      - 修正依赖声明：`websocket` → `websocket-client`（API 测试工具的 WebSocket 连接依赖正确的包）。
   - **安全增强**：
      - 用户密码改为哈希存储（PBKDF2），旧明文密码在首次登录成功后自动升级。
      - 注册与修改密码强制校验密码长度（至少 8 位），修改密码增加服务端二次确认。
      - 新增 API 会话令牌模型（`ApiSessionToken`）：令牌仅存哈希、带过期时间，服务端真实校验，杜绝伪造。
      - 文件上传增加文件名安全校验：拒绝路径穿越与非法字符，落盘文件名随机化防止覆盖。
      - 网页登录与注册移除 CSRF 豁免，图形验证码校验后立即销毁。
      - `SECRET_KEY` 与 API 签名密钥支持环境变量注入，`DEBUG` 由环境变量控制，登录日志不再输出明文密码。
   - **部署改进**：
      - 新增独立静态文件服务：关闭 `DEBUG` 后前端与后台静态资源不再丢失；服务会回退到应用包查找器并自动补全 `admin/` 前缀，admin/SimpleUI 样式无需 `collectstatic` 也能正常显示。
      - `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` 支持环境变量覆盖，本地 http 环境关闭 DEBUG 也能正常登录。
      - `start.bat` 默认以关闭 DEBUG 模式启动。
      - API 测试工具（`TEST/api_test_gui.py`）配置全部迁移至 `TEST/config.json`（含 `api_url`、`use_https`、`SECRET_KEY`），代码不再硬编码。

- **2026-07-10**
   - **移除冗余功能**：删除了产品列表（product list）相关模块，精简系统架构，降低维护成本。
   - **新增功能**：增加客户端获取头像 API（`GetAvatar_api_v3`），支持通过 `uuid` 获取用户头像，返回 Base64 格式数据。
   - **安全增强**：
      - 登录接口引入 HMAC-SHA256 签名验证机制，防止请求篡改。
      - 增加时间戳 + 随机数（nonce）防重放攻击，请求有效期 300 秒。
      - 登录成功后返回会话令牌（session_token），后续 API 调用需携带令牌验证身份。
      - 所有 API 接口统一强制使用 POST 方法。

- **2025-11-24**
   - 使用bootstarp5重写前端页面。
   - 修复部分BUG。

- **2025-10-20**
   - 加入新的api接口(api_v3/upload_logfile_api_v3/)用于上传文件(日志),上传的文件将保存在"static/uploads"。
   - 修复部分BUG，优化日志创建流程。

- **2025-10-19**
   - 优化主页渲染方式：采用 iframe 隔离后台定制内容，实现样式互不干扰，提升安全性与灵活性。
   - 用户界面调整：美化用户设置、个人主页等界面，提升操作体验和视觉效果。
   - 修复部分已知BUG，提升系统稳定性。
   - 其他细节优化与性能提升。

- **2025-10-18**
  - 修复用户列表的部分BUG
  - 加入可以在api获取某公告
  - 优化了部分细节

## 其他说明

- 如需自定义页面或功能，请在`AT/templates/`或`database/templates/`下修改对应HTML文件。
- 静态资源可在`static/`目录下替换或新增。
- 如有问题请联系项目维护者。
