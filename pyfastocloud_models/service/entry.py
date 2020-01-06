from enum import IntEnum

from bson import ObjectId
from mongoengine import Document, ListField, EmbeddedDocumentField, ReferenceField, EmbeddedDocument, IntField, \
    StringField, EmbeddedDocumentListField, PULL

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import HostAndPort
from pyfastocloud_models.stream.entry import IStream
from pyfastocloud_models.series.entry import Serial


# #EXTM3U
# #EXTINF:-1 tvg-id="" tvg-name="" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Amptv.png/330px-Amptv.png" group-title="Armenia(Հայաստան)",1TV
# http://amtv1.livestreamingcdn.com/am2abr/tracks-v1a1/index.m3u8

class ProviderPair(EmbeddedDocument):
    class Roles(IntEnum):
        READ = 0
        WRITE = 1
        SUPPORT = 2
        ADMIN = 3

        @classmethod
        def choices(cls):
            return [(choice, choice.name) for choice in cls]

        @classmethod
        def coerce(cls, item):
            return cls(int(item)) if not isinstance(item, cls) else item

        def __str__(self):
            return str(self.value)

    user = ReferenceField('Provider')
    role = IntField(min_value=Roles.READ, max_value=Roles.ADMIN, default=Roles.ADMIN)


def safe_delete_stream(stream: IStream):
    if stream:
        from pyfastocloud_models.subscriber.entry import Subscriber
        subscribers = Subscriber.objects()
        for subscriber in subscribers:
            subscriber.remove_official_stream(stream)
        stream.delete()


class ServiceSettings(Document):
    DEFAULT_SERVICE_NAME = 'Service'
    MIN_SERVICE_NAME_LENGTH = 3
    MAX_SERVICE_NAME_LENGTH = 30

    DEFAULT_FEEDBACK_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/feedback'
    DEFAULT_TIMESHIFTS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/timeshifts'
    DEFAULT_HLS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/hls'
    DEFAULT_PLAYLISTS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/playlists'
    DEFAULT_DVB_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/dvb'
    DEFAULT_CAPTURE_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/capture_card'
    DEFAULT_VODS_IN_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/vods_in'
    DEFAULT_VODS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/vods'
    DEFAULT_CODS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/cods'

    DEFAULT_SERVICE_HOST = 'localhost'
    DEFAULT_SERVICE_PORT = 6317
    DEFAULT_SERVICE_HTTP_HOST = 'localhost'
    DEFAULT_SERVICE_HTTP_PORT = 8000
    DEFAULT_SERVICE_VODS_HOST = 'localhost'
    DEFAULT_SERVICE_VODS_PORT = 7000
    DEFAULT_SERVICE_CODS_HOST = 'localhost'
    DEFAULT_SERVICE_CODS_PORT = 6001

    meta = {'collection': 'services', 'auto_create_index': False}

    streams = ListField(ReferenceField(IStream, reverse_delete_rule=PULL), default=[])
    series = ListField(ReferenceField(Serial, reverse_delete_rule=PULL), default=[])
    providers = EmbeddedDocumentListField(ProviderPair, default=[])

    name = StringField(unique=True, default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                       min_length=MIN_SERVICE_NAME_LENGTH)
    host = EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT))
    http_host = EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_HTTP_HOST,
                                                                       port=DEFAULT_SERVICE_HTTP_PORT))
    vods_host = EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_VODS_HOST,
                                                                       port=DEFAULT_SERVICE_VODS_PORT))
    cods_host = EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_CODS_HOST,
                                                                       port=DEFAULT_SERVICE_CODS_PORT))

    feedback_directory = StringField(default=DEFAULT_FEEDBACK_DIR_PATH)
    timeshifts_directory = StringField(default=DEFAULT_TIMESHIFTS_DIR_PATH)
    hls_directory = StringField(default=DEFAULT_HLS_DIR_PATH)
    playlists_directory = StringField(default=DEFAULT_PLAYLISTS_DIR_PATH)
    dvb_directory = StringField(default=DEFAULT_DVB_DIR_PATH)
    capture_card_directory = StringField(default=DEFAULT_CAPTURE_DIR_PATH)
    vods_in_directory = StringField(default=DEFAULT_VODS_IN_DIR_PATH)
    vods_directory = StringField(default=DEFAULT_VODS_DIR_PATH)
    cods_directory = StringField(default=DEFAULT_CODS_DIR_PATH)

    def get_host(self) -> str:
        return str(self.host)

    def get_http_host(self) -> str:
        return 'http://{0}'.format(str(self.http_host))

    def get_vods_host(self) -> str:
        return 'http://{0}'.format(str(self.vods_host))

    def get_cods_host(self) -> str:
        return 'http://{0}'.format(str(self.cods_host))

    def generate_http_link(self, url: str) -> str:
        return url.replace(self.hls_directory, self.get_http_host())

    def generate_vods_link(self, url: str) -> str:
        return url.replace(self.vods_directory, self.get_vods_host())

    def generate_cods_link(self, url: str) -> str:
        return url.replace(self.cods_directory, self.get_cods_host())

    def generate_playlist(self) -> str:
        result = '#EXTM3U\n'
        for stream in self.streams:
            result += stream.generate_playlist(False)

        return result

    def add_streams(self, streams: [IStream]):
        for stream in streams:
            self.streams.append(stream)
        self.save()

    def add_stream(self, stream: IStream):
        self.streams.append(stream)
        self.save()

    def remove_stream(self, stream: IStream):
        self.streams.remove(stream)
        self.save()

    def remove_all_streams(self):
        self.streams = []
        self.save()

    def add_provider(self, user: ProviderPair):
        self.providers.append(user)
        self.save()

    def remove_provider(self, provider):
        providers = self.providers.filter(user=provider)
        providers.delete()
        self.providers.save()

    def find_stream_settings_by_id(self, sid: ObjectId):
        for stream in self.streams:
            if stream.id == sid:
                return stream

        return None

    def delete(self, *args, **kwargs):
        for stream in self.streams:
            safe_delete_stream(stream)
        return super(ServiceSettings, self).delete(*args, **kwargs)
