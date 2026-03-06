from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from AT.online_state import ONLINE_INFO 

channel_layer = get_channel_layer()
class AdminOnlineConsumer(WebsocketConsumer):
    group_name = 'online_admin'
    def connect(self):
        if not self.scope['user'].is_staff:
            self.close()
            return

        async_to_sync(channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        self.send(text_data=json.dumps(list(ONLINE_INFO.values())))

    def disconnect(self, close_code):
        async_to_sync(channel_layer.group_discard)(self.group_name, self.channel_name)

    def online_event(self, event):
        self.send(text_data=json.dumps(event['payload']))