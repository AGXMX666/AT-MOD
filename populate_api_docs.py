#!/usr/bin/env python
"""
脚本用于填充API文档数据
运行方式: python populate_api_docs.py
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AT.settings')
django.setup()

from database.models import APIDocSection, APIEndpoint

def populate_sections():
    """创建文档章节"""
    sections = [
        {
            'title': '概述',
            'content': '''本文档提供了API接口的详细说明和多种编程语言的调用示例。所有API均使用POST方法，并返回JSON格式数据。

**重要提示：** function_user_api_v3接口需要使用时间戳生成key参数进行身份验证。''',
            'order': 1,
            'is_active': True
        },
        {
            'title': '时间戳加密说明',
            'content': '''在 `function_user_api_v3` 接口中，需要使用时间戳与其他数据生成哈希值作为 `key` 参数，用于身份验证和数据完整性校验。

### 生成规则

```python
timestamp_str = datetime.now().strftime('%Y%m%d%H%M')
data_to_hash = f"{timestamp_str}{uuids}{timestamp_str}"
key_server = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
```

时间戳格式为 `YYYYMMDDHHMM`（年月日时分），需要与UUID拼接两次，然后使用SHA256算法生成哈希值。

**注意：** 时间戳的有效期为当前分钟，即每分钟需要重新生成key。请确保客户端与服务器时间同步。''',
            'order': 2,
            'is_active': True
        },
    ]

    for section_data in sections:
        section, created = APIDocSection.objects.get_or_create(
            title=section_data['title'],
            defaults=section_data
        )
        if created:
            print(f"[+] 创建章节: {section.title}")
        else:
            print(f"[-] 章节已存在: {section.title}")

def populate_endpoints():
    """创建API端点文档"""
    endpoints = [
        {
            'name': '用户登录接口',
            'endpoint': '/login_api_v3',
            'method': 'POST',
            'description': '用户通过账号密码登录系统，返回用户的UUID、封禁状态、VIP状态和点数信息。',
            'request_params': '''[
    {"name": "Account", "type": "String", "required": true, "description": "用户账号"},
    {"name": "password", "type": "String", "required": true, "description": "用户密码"}
]''',
            'response_success': '''{
    "info": "登录成功",
    "uuid": "用户唯一标识",
    "is_banned": false,
    "is_vip": false,
    "ds": "用户点数"
}''',
            'response_error': '''{
    "error": "密码错误"
}
// 或
{
    "error": "用户名不存在"
}
// 或
{
    "error": "账号被封禁"
}''',
            'code_python': '''import requests

url = "http://your-domain.com/login_api_v3"
data = {
    "Account": "your_username",
    "password": "your_password"
}

response = requests.post(url, data=data)
result = response.json()

if response.status_code == 200:
    print(f"登录成功，UUID: {result['uuid']}")
    print(f"点数: {result['ds']}")
else:
    print(f"登录失败: {result['error']}")''',
            'code_javascript': '''const url = 'http://your-domain.com/login_api_v3';
const data = new URLSearchParams({
    'Account': 'your_username',
    'password': 'your_password'
});

fetch(url, {
    method: 'POST',
    body: data
})
.then(response => response.json())
.then(result => {
    if (result.info) {
        console.log(`登录成功，UUID: ${result.uuid}`);
        console.log(`点数: ${result.ds}`);
    } else {
        console.log(`登录失败: ${result.error}`);
    }
})
.catch(error => console.error('请求错误:', error));''',
            'code_java': '''import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class LoginAPI {
    public static void login() throws IOException {
        String url = "http://your-domain.com/login_api_v3";
        String postData = "Account=your_username&password=your_password";

        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);

        try (OutputStream os = conn.getOutputStream()) {
            byte[] input = postData.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        int responseCode = conn.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            try (BufferedReader br = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                StringBuilder response = new StringBuilder();
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
                System.out.println("响应: " + response.toString());
            }
        }
    }
}''',
            'code_csharp': '''using System;
using System.Net.Http;
using System.Threading.Tasks;

public class LoginAPI
{
    private static readonly HttpClient client = new HttpClient();

    public static async Task LoginAsync()
    {
        string url = "http://your-domain.com/login_api_v3";
        var values = new Dictionary<string, string>
        {
            { "Account", "your_username" },
            { "password", "your_password" }
        };

        var content = new FormUrlEncodedContent(values);
        var response = await client.PostAsync(url, content);
        var responseString = await response.Content.ReadAsStringAsync();

        Console.WriteLine($"响应: {responseString}");
    }
}''',
            'notes': '登录成功后请保存返回的UUID，后续API调用需要使用。',
            'order': 1,
            'is_active': True
        },
        {
            'name': '功能信息接口',
            'endpoint': '/function_info_api_v3',
            'method': 'POST',
            'description': '获取系统中所有可用的操作类型及其对应的点数变化。',
            'request_params': '[]',
            'response_success': '''[
    {
        "id": 1,
        "name": "功能名称",
        "coins": 10
    },
    {
        "id": 2,
        "name": "另一个功能",
        "coins": -5
    }
]''',
            'response_error': '''{
    "error": "Method not allowed"
}''',
            'code_python': '''import requests

url = "http://your-domain.com/function_info_api_v3"
response = requests.post(url)
result = response.json()

if response.status_code == 200:
    for func in result:
        print(f"ID: {func['id']}, 名称: {func['name']}, 点数: {func['coins']}")
else:
    print(f"请求失败: {result['error']}")''',
            'code_javascript': '''const url = 'http://your-domain.com/function_info_api_v3';

fetch(url, {
    method: 'POST'
})
.then(response => response.json())
.then(result => {
    result.forEach(func => {
        console.log(`ID: ${func.id}, 名称: ${func.name}, 点数: ${func.coins}`);
    });
})
.catch(error => console.error('请求错误:', error));''',
            'notes': '此接口无需参数，返回所有启用的操作类型列表。',
            'order': 2,
            'is_active': True
        },
        {
            'name': '公告获取接口',
            'endpoint': '/bulletinboard_api_v3',
            'method': 'POST',
            'description': '获取系统公告信息。可以获取最新公告或指定ID的公告。',
            'request_params': '''[
    {"name": "id", "type": "Integer", "required": false, "description": "公告ID（可选，不传则返回最新公告）"}
]''',
            'response_success': '''{
    "info": "获取成功",
    "text": "公告内容"
}''',
            'response_error': '''{
    "error": "暂无公告"
}
// 或
{
    "error": "公告不存在"
}''',
            'code_python': '''import requests

url = "http://your-domain.com/bulletinboard_api_v3"

# 获取最新公告
response = requests.post(url)
result = response.json()

if response.status_code == 200:
    print(f"公告内容: {result['text']}")
else:
    print(f"获取失败: {result['error']}")

# 获取指定ID的公告
data = {"id": 1}
response = requests.post(url, data=data)
result = response.json()''',
            'code_javascript': '''const url = 'http://your-domain.com/bulletinboard_api_v3';

// 获取最新公告
fetch(url, {
    method: 'POST'
})
.then(response => response.json())
.then(result => {
    if (result.info) {
        console.log(`公告内容: ${result.text}`);
    } else {
        console.log(`获取失败: ${result.error}`);
    }
});

// 获取指定ID的公告
const data = new URLSearchParams({ 'id': '1' });
fetch(url, {
    method: 'POST',
    body: data
})
.then(response => response.json())
.then(result => console.log(result));''',
            'notes': '如果不传id参数，将返回最新的公告。',
            'order': 3,
            'is_active': True
        },
        {
            'name': '用户操作接口',
            'endpoint': '/function_user_api_v3',
            'method': 'POST',
            'description': '执行用户操作，根据操作类型扣除或增加用户点数。需要时间戳加密验证。',
            'request_params': '''[
    {"name": "uuids", "type": "String", "required": true, "description": "用户唯一标识（从登录接口获取）"},
    {"name": "opid", "type": "Integer", "required": true, "description": "操作ID（从功能信息接口获取）"},
    {"name": "key", "type": "String", "required": true, "description": "使用时间戳生成的SHA256哈希值"}
]''',
            'response_success': '''{
    "message": "操作成功",
    "ds": "用户当前点数"
}''',
            'response_error': '''{
    "error": "非法请求"
}
// 或
{
    "error": "用户未在线，操作被拒绝"
}
// 或
{
    "error": "用户点数不足"
}
// 或
{
    "error": "该用户被封禁"
}''',
            'code_python': '''import requests
import hashlib
from datetime import datetime

def generate_key(uuids):
    # 生成当前时间戳，格式为YYYYMMDDHHMM
    timestamp_str = datetime.now().strftime('%Y%m%d%H%M')
    # 拼接数据: 时间戳 + uuid + 时间戳
    data_to_hash = f"{timestamp_str}{uuids}{timestamp_str}"
    # 生成SHA256哈希
    return hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

url = "http://your-domain.com/function_user_api_v3"
uuids = "user_unique_id"  # 从登录接口获取
opid = 1  # 操作ID

key = generate_key(uuids)

data = {
    "uuids": uuids,
    "opid": opid,
    "key": key
}

response = requests.post(url, data=data)
result = response.json()

if response.status_code == 200:
    print(f"操作成功，当前点数: {result['ds']}")
else:
    print(f"操作失败: {result['error']}")''',
            'code_javascript': '''const crypto = require('crypto');

function generateKey(uuids) {
    // 生成当前时间戳，格式为YYYYMMDDHHMM
    const now = new Date();
    const timestampStr =
        now.getFullYear().toString() +
        (now.getMonth() + 1).toString().padStart(2, '0') +
        now.getDate().toString().padStart(2, '0') +
        now.getHours().toString().padStart(2, '0') +
        now.getMinutes().toString().padStart(2, '0');

    // 拼接数据: 时间戳 + uuid + 时间戳
    const dataToHash = timestampStr + uuids + timestampStr;

    // 生成SHA256哈希
    return crypto.createHash('sha256').update(dataToHash).digest('hex');
}

const url = 'http://your-domain.com/function_user_api_v3';
const uuids = 'user_unique_id';  // 从登录接口获取
const opid = 1;  // 操作ID

const key = generateKey(uuids);

const data = new URLSearchParams({
    uuids: uuids,
    opid: opid,
    key: key
});

fetch(url, {
    method: 'POST',
    body: data
})
.then(response => response.json())
.then(result => {
    if (result.message) {
        console.log(`操作成功，当前点数: ${result.ds}`);
    } else {
        console.log(`操作失败: ${result.error}`);
    }
})
.catch(error => console.error('请求错误:', error));''',
            'code_java': '''import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class UserOperationAPI {
    public static String generateKey(String uuids) {
        // 生成当前时间戳，格式为YYYYMMDDHHMM
        LocalDateTime now = LocalDateTime.now();
        String timestampStr = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmm"));

        // 拼接数据: 时间戳 + uuid + 时间戳
        String dataToHash = timestampStr + uuids + timestampStr;

        // 生成SHA256哈希
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(dataToHash.getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public static void userOperation() throws IOException {
        String url = "http://your-domain.com/function_user_api_v3";
        String uuids = "user_unique_id";
        int opid = 1;

        String key = generateKey(uuids);

        String postData = String.format("uuids=%s&opid=%d&key=%s", uuids, opid, key);

        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);

        try (OutputStream os = conn.getOutputStream()) {
            byte[] input = postData.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        // 处理响应...
    }
}''',
            'code_csharp': '''using System;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;

public class UserOperationAPI
{
    private static readonly HttpClient client = new HttpClient();

    public static string GenerateKey(string uuids)
    {
        // 生成当前时间戳，格式为YYYYMMDDHHMM
        string timestampStr = DateTime.Now.ToString("yyyyMMddHHmm");

        // 拼接数据: 时间戳 + uuid + 时间戳
        string dataToHash = timestampStr + uuids + timestampStr;

        // 生成SHA256哈希
        using (SHA256 sha256Hash = SHA256.Create())
        {
            byte[] bytes = sha256Hash.ComputeHash(Encoding.UTF8.GetBytes(dataToHash));
            StringBuilder builder = new StringBuilder();
            for (int i = 0; i < bytes.Length; i++)
            {
                builder.Append(bytes[i].ToString("x2"));
            }
            return builder.ToString();
        }
    }

    public static async Task UserOperationAsync()
    {
        string url = "http://your-domain.com/function_user_api_v3";
        string uuids = "user_unique_id";
        int opid = 1;

        string key = GenerateKey(uuids);

        var values = new Dictionary<string, string>
        {
            { "uuids", uuids },
            { "opid", opid.ToString() },
            { "key", key }
        };

        var content = new FormUrlEncodedContent(values);
        var response = await client.PostAsync(url, content);
        var responseString = await response.Content.ReadAsStringAsync();

        Console.WriteLine($"响应: {responseString}");
    }
}''',
            'notes': '''**重要提示：**
1. 用户必须在线才能执行操作（通过WebSocket连接）
2. key参数必须使用当前分钟的时间戳生成，过期无效
3. 确保客户端与服务器时间同步
4. 操作会根据操作类型扣除或增加用户点数''',
            'order': 4,
            'is_active': True
        },
    ]

    for endpoint_data in endpoints:
        endpoint, created = APIEndpoint.objects.get_or_create(
            endpoint=endpoint_data['endpoint'],
            defaults=endpoint_data
        )
        if created:
            print(f"[+] 创建API端点: {endpoint.name}")
        else:
            print(f"[-] API端点已存在: {endpoint.name}")

def main():
    print("=" * 60)
    print("开始填充API文档数据...")
    print("=" * 60)

    print("\n[1/2] 创建文档章节...")
    populate_sections()

    print("\n[2/2] 创建API端点...")
    populate_endpoints()

    print("\n" + "=" * 60)
    print("API文档数据填充完成！")
    print("=" * 60)
    print("\n访问 /DeveloperDocumentation/ 查看文档")
    print("访问 /admin/ 管理文档内容")

if __name__ == '__main__':
    main()
