from datetime import datetime
from enum import IntEnum

from mongoengine import Document, StringField, DateTimeField, IntField, ListField, ReferenceField, PULL
from werkzeug.security import generate_password_hash, check_password_hash

from pyfastocloud_models.service.entry import ServiceSettings
import pyfastocloud_models.constants as constants


class Provider(Document):
    class Status(IntEnum):
        NO_ACTIVE = 0
        ACTIVE = 1
        BANNED = 2

    class Type(IntEnum):
        GUEST = 0,
        USER = 1

    meta = {'allow_inheritance': False, 'collection': 'providers', 'auto_create_index': False}
    email = StringField(max_length=64, required=True)
    password = StringField(required=True)
    created_date = DateTimeField(default=datetime.now)
    status = IntField(default=Status.NO_ACTIVE)
    type = IntField(default=Type.USER)
    country = StringField(min_length=2, max_length=3, required=True)
    language = StringField(default=constants.DEFAULT_LOCALE, required=True)

    servers = ListField(ReferenceField(ServiceSettings, reverse_delete_rule=PULL), default=[])

    def add_server(self, server):
        self.servers.append(server)
        self.save()

    def remove_server(self, server):
        self.servers.remove(server)
        self.save()

    @staticmethod
    def generate_password_hash(password: str) -> str:
        return generate_password_hash(password, method='sha256')

    @staticmethod
    def check_password_hash(hash: str, password: str) -> bool:
        return check_password_hash(hash, password)
