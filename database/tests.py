import hashlib
import hmac
import time

from django.conf import settings
from django.test import TestCase

from AT.online_state import ONLINE_USERS
from database.models import OperationType, users


class FunctionUserApiV3Tests(TestCase):
    def setUp(self):
        self.user = users.objects.create(
            Account='tester',
            password='123456',
            UniqueIdentification='1234567890abcdef',
            coins=0,
        )
        self.operation_type = OperationType.objects.create(
            name='test_operation',
            coins=10,
            description='test',
            is_active=True,
        )
        ONLINE_USERS[self.user.UniqueIdentification] = 'test-channel'

    def tearDown(self):
        ONLINE_USERS.pop(self.user.UniqueIdentification, None)

    def _build_signature(self, uuids, opid, session_token, timestamp, nonce):
        secret = getattr(settings, 'API_SECRET_KEY', getattr(settings, 'API_SHARED_SECRET', settings.SECRET_KEY))
        payload = {
            'uuids': uuids,
            'opid': opid,
            'session_token': session_token,
            'timestamp': timestamp,
            'nonce': nonce,
        }
        filtered_data = {k: v for k, v in payload.items() if v is not None}
        sorted_data = sorted(filtered_data.items())
        sign_str = '&'.join([f'{k}={v}' for k, v in sorted_data])
        return hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).hexdigest()

    def test_valid_signature_is_accepted(self):
        timestamp = str(int(time.time()))
        nonce = 'nonce-1234567890'
        session_token = 'a' * 64
        signature = self._build_signature(
            self.user.UniqueIdentification,
            self.operation_type.id,
            session_token,
            timestamp,
            nonce,
        )

        response = self.client.post('/api_v3/function_user_api_v3/', {
            'uuids': self.user.UniqueIdentification,
            'opid': self.operation_type.id,
            'session_token': session_token,
            'timestamp': timestamp,
            'nonce': nonce,
            'signature': signature,
        })

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 10)

    def test_invalid_signature_is_rejected(self):
        response = self.client.post('/api_v3/function_user_api_v3/', {
            'uuids': self.user.UniqueIdentification,
            'opid': self.operation_type.id,
            'session_token': 'b' * 64,
            'timestamp': str(int(time.time())),
            'nonce': 'nonce-bad',
            'signature': 'bad-signature',
        })

        self.assertEqual(response.status_code, 401)


class LoginApiV3SignatureTests(TestCase):
    def setUp(self):
        self.user = users.objects.create(
            Account='login-tester',
            password='123456',
            UniqueIdentification='fedcba9876543210',
            coins=0,
        )

    def test_login_signature_with_timestamp_is_accepted(self):
        timestamp = str(int(time.time()))
        nonce = 'nonce-login-123456'
        sign_data = {
            'Account': self.user.Account,
            'password': self.user.password,
            'timestamp': timestamp,
            'nonce': nonce,
        }
        filtered_data = {k: v for k, v in sign_data.items() if v is not None}
        sorted_data = sorted(filtered_data.items())
        sign_str = '&'.join([f'{k}={v}' for k, v in sorted_data])
        secret = getattr(settings, 'API_SECRET_KEY', getattr(settings, 'API_SHARED_SECRET', settings.SECRET_KEY))
        signature = hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).hexdigest()

        response = self.client.post('/api_v3/login/', {
            'Account': self.user.Account,
            'password': self.user.password,
            'timestamp': timestamp,
            'nonce': nonce,
            'signature': signature,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['info'], '登录成功')
