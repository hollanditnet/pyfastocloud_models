from flask_login import UserMixin, login_user, logout_user

from datetime import datetime
from hashlib import md5
from bson.objectid import ObjectId
from enum import IntEnum

from mongoengine import Document, EmbeddedDocument, StringField, DateTimeField, IntField, ListField, ReferenceField, \
    PULL, ObjectIdField, BooleanField, EmbeddedDocumentListField

from pyfastocloud_models.service.entry import ServiceSettings
from pyfastocloud_models.stream.entry import IStream, StreamFields
import pyfastocloud_models.constants as constants
from pyfastocloud_models.utils.utils import date_to_utc_msec


def login_user_wrap(user):
    login_user(user)


class Device(EmbeddedDocument):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    STATUS_FIELD = 'status'
    CREATED_DATE_FIELD = 'created_date'

    DEFAULT_DEVICE_NAME = 'Device'
    MIN_DEVICE_NAME_LENGTH = 3
    MAX_DEVICE_NAME_LENGTH = 32

    class Status(IntEnum):
        NOT_ACTIVE = 0
        ACTIVE = 1
        BANNED = 2

        @classmethod
        def choices(cls):
            return [(choice, choice.name) for choice in cls]

        @classmethod
        def coerce(cls, item):
            return cls(int(item)) if not isinstance(item, cls) else item

        def __str__(self):
            return str(self.value)

    meta = {'auto_create_index': True}
    id = ObjectIdField(required=True, default=ObjectId, unique=True, primary_key=True)
    created_date = DateTimeField(default=datetime.now)
    status = IntField(default=Status.NOT_ACTIVE)
    name = StringField(default=DEFAULT_DEVICE_NAME, min_length=MIN_DEVICE_NAME_LENGTH,
                       max_length=MAX_DEVICE_NAME_LENGTH, required=True)

    def get_id(self):
        return str(self.id)

    def to_dict(self) -> dict:
        return {Device.ID_FIELD: self.get_id(), Device.NAME_FIELD: self.name, Device.STATUS_FIELD: self.status,
                Device.CREATED_DATE_FIELD: date_to_utc_msec(self.created_date)}


class UserStream(EmbeddedDocument):
    FAVORITE_FIELD = 'favorite'
    PRIVATE_FIELD = 'private'
    RECENT_FIELD = 'recent'

    sid = ReferenceField(IStream, required=True)
    favorite = BooleanField(default=False)
    private = BooleanField(default=False)
    recent = DateTimeField(default=datetime.utcfromtimestamp(0))
    interruption_time = IntField(default=0, min_value=0, max_value=constants.MAX_VIDEO_DURATION_MSEC, required=True)

    def get_id(self):
        return str(self.sid.id)

    def to_dict(self) -> dict:
        res = self.sid.to_dict()
        res[UserStream.FAVORITE_FIELD] = self.favorite
        res[UserStream.PRIVATE_FIELD] = self.private
        res[UserStream.RECENT_FIELD] = date_to_utc_msec(self.recent)
        return res

    def to_front_dict(self):
        res = self.sid.to_front_dict()
        res[UserStream.FAVORITE_FIELD] = self.favorite
        res[UserStream.PRIVATE_FIELD] = self.private
        res[UserStream.RECENT_FIELD] = date_to_utc_msec(self.recent)
        return res


class Subscriber(UserMixin, Document):
    def logout(self):
        logout_user()

    MAX_DATE = datetime(2100, 1, 1)
    ID_FIELD = 'id'
    EMAIL_FIELD = 'login'
    PASSWORD_FIELD = 'password'

    class Status(IntEnum):
        NOT_ACTIVE = 0
        ACTIVE = 1
        TRIAL_FINISHED = 2
        BANNED = 3

        @classmethod
        def choices(cls):
            return [(choice, choice.name) for choice in cls]

        @classmethod
        def coerce(cls, item):
            return cls(int(item)) if not isinstance(item, cls) else item

        def __str__(self):
            return str(self.value)

    SUBSCRIBER_HASH_LENGTH = 32

    meta = {'allow_inheritance': False, 'collection': 'subscribers', 'auto_create_index': False}

    email = StringField(max_length=64, required=True)
    first_name = StringField(max_length=64, required=True)
    last_name = StringField(max_length=64, required=True)
    password = StringField(min_length=SUBSCRIBER_HASH_LENGTH, max_length=SUBSCRIBER_HASH_LENGTH, required=True)
    created_date = DateTimeField(default=datetime.now)
    exp_date = DateTimeField(default=MAX_DATE)
    status = IntField(default=Status.NOT_ACTIVE)
    country = StringField(min_length=2, max_length=3, required=True)
    language = StringField(default=constants.DEFAULT_LOCALE, required=True)

    servers = ListField(ReferenceField(ServiceSettings, reverse_delete_rule=PULL), unique=True, default=[])
    devices = EmbeddedDocumentListField(Device, unique=True, default=[])
    max_devices_count = IntField(default=constants.DEFAULT_DEVICES_COUNT)
    streams = EmbeddedDocumentListField(UserStream, unique=True, default=[])

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    def expiration_date_utc_msec(self):
        return date_to_utc_msec(self.exp_date)

    def add_server(self, server: ServiceSettings):
        self.servers.append(server)
        self.save()

    def add_device(self, device: Device):
        if len(self.devices) < self.max_devices_count:
            self.devices.append(device)
            self.save()

    def remove_device(self, sid: ObjectId):
        devices = self.devices.filter(id=sid)
        devices.delete()
        self.devices.save()

    def generate_playlist(self, did: str, lb_server_host_and_port: str) -> str:
        result = '#EXTM3U\n'
        sid = str(self.id)
        for stream in self.streams:
            if stream.private:
                result += stream.sid.generate_playlist(False)
            else:
                result += stream.sid.generate_device_playlist(sid, self.password, did, lb_server_host_and_port, False)

        return result

    def all_streams(self):
        return self.streams

    def add_official_stream_by_id(self, oid: ObjectId):
        user_stream = UserStream(sid=oid)
        self.add_official_stream(user_stream)

    def add_official_stream(self, stream: UserStream):
        db_stream = stream.sid
        found_streams = self.streams.filter(sid=db_stream)
        if not found_streams:
            self.streams.append(stream)
            self.save()

    def add_own_stream(self, stream: IStream):
        user_stream = UserStream(sid=stream.id)
        user_stream.private = True
        found_streams = self.streams.filter(sid=stream)
        if not found_streams:
            self.streams.append(user_stream)
            self.save()

    def remove_official_stream(self, stream: IStream):
        streams = self.streams.filter(sid=stream)
        streams.delete()
        self.streams.save()

    def remove_official_stream_by_id(self, sid: ObjectId):
        original_stream = IStream.objects(id=sid).first()
        self.remove_official_stream(original_stream)

    def remove_own_stream_by_id(self, sid: ObjectId):
        stream = IStream.objects(id=sid).first()
        streams = self.streams.filter(sid=stream, private=True)
        for stream in streams:
            stream.sid.delete()
        streams.delete()
        self.streams.save()

    def remove_all_own_streams(self):
        streams = self.streams.filter(private=True)
        for stream in streams:
            stream.sid.delete()
        streams.delete()
        self.streams.save()

    def official_streams(self):
        return self.streams.filter(private=False)

    def own_streams(self):
        return self.streams.filter(private=True)

    def delete(self, *args, **kwargs):
        self.remove_all_own_streams()
        return super(Subscriber, self).delete(*args, **kwargs)

    @staticmethod
    def make_md5_hash_from_password(password: str) -> str:
        m = md5()
        m.update(password.encode())
        return m.hexdigest()

    @staticmethod
    def generate_password_hash(password: str) -> str:
        return Subscriber.make_md5_hash_from_password(password)

    @staticmethod
    def check_password_hash(hash: str, password: str) -> bool:
        return hash == Subscriber.generate_password_hash(password)

    @classmethod
    def make_subscriber(cls, email: str, first_name: str, last_name: str, password: str, country: str, language: str):
        return cls(email=email, first_name=first_name, last_name=last_name,
                   password=Subscriber.make_md5_hash_from_password(password), country=country,
                   language=language)


Subscriber.register_delete_rule(ServiceSettings, 'subscribers', PULL)
