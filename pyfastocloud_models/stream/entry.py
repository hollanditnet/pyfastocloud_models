from datetime import datetime
from enum import IntEnum
from urllib.parse import urlparse
import os

from mongoengine import StringField, IntField, EmbeddedDocumentField, Document, BooleanField, DateTimeField, FloatField

from pyfastocloud_models.utils.utils import date_to_utc_msec
import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import Rational, Size, Logo, RSVGLogo, InputUrls, InputUrl, OutputUrls, \
    OutputUrl


class ConfigFields:
    ID_FIELD = 'id'
    TYPE_FIELD = 'type'
    FEEDBACK_DIR_FIELD = 'feedback_directory'
    LOG_LEVEL_FIELD = 'log_level'
    INPUT_FIELD = 'input'
    OUTPUT_FIELD = 'output'
    AUDIO_SELECT_FIELD = 'audio_select'
    HAVE_VIDEO_FIELD = 'have_video'
    HAVE_AUDIO_FIELD = 'have_audio'
    LOOP_FIELD = 'loop'
    AVFORMAT_FIELD = 'avformat'
    AUTO_EXIT_TIME_FIELD = 'auto_exit_time'
    RESTART_ATTEMPTS_FIELD = 'restart_attempts'

    # encode
    RELAY_VIDEO_FIELD = 'relay_video'
    RELAY_AUDIO_FIELD = 'relay_audio'
    DEINTERLACE_FIELD = 'deinterlace'
    FRAME_RATE_FIELD = 'frame_rate'
    VOLUME_FIELD = 'volume'
    VIDEO_CODEC_FIELD = 'video_codec'
    AUDIO_CODEC_FIELD = 'audio_codec'
    AUDIO_CHANNELS_COUNT_FIELD = 'audio_channels'
    SIZE_FIELD = 'size'
    VIDEO_BIT_RATE_FIELD = 'video_bitrate'
    AUDIO_BIT_RATE_FIELD = 'audio_bitrate'
    LOGO_FIELD = 'logo'
    RSVG_LOGO_FIELD = 'rsvg_logo'
    ASPCET_RATIO_FIELD = 'aspect_ratio'
    # relay
    VIDEO_PARSER_FIELD = 'video_parser'
    AUDIO_PARSER_FIELD = 'audio_parser'
    # timeshift recorder
    TIMESHIFT_CHUNK_DURATION = 'timeshift_chunk_duration'
    TIMESHIFT_CHUNK_LIFE_TIME = 'timeshift_chunk_life_time'
    TIMESHIFT_DIR = 'timeshift_dir'
    # timeshift player
    TIMESHIFT_DELAY = 'timeshift_delay'
    # vods
    VODS_CLEANUP_TS = 'cleanup_ts'


class BaseFields:
    NAME_FIELD = 'name'
    ID_FIELD = 'id'
    PRICE_FIELD = 'price'
    GROUP_FIELD = 'group'
    VISIBLE_FIELD = 'visible'
    IARC_FIELD = 'iarc'

    TYPE_FIELD = 'type'
    INPUT_STREAMS_FIELD = 'input_streams'
    OUTPUT_STREAMS_FIELD = 'output_streams'
    LOOP_START_TIME_FIELD = 'loop_start_time'
    RSS_FIELD = 'rss'
    CPU_FIELD = 'cpu'
    STATUS_FIELD = 'status'
    RESTARTS_FIELD = 'restarts'
    START_TIME_FIELD = 'start_time'
    TIMESTAMP_FIELD = 'timestamp'
    IDLE_TIME_FIELD = 'idle_time'


class StreamFields(BaseFields):
    ICON_FIELD = 'icon'
    QUALITY_FIELD = 'quality'


class VodFields(BaseFields):
    DESCRIPTION_FIELD = 'description'  #
    VOD_TYPE_FIELD = 'vod_type'
    TRAILER_URL_FIELD = 'trailer_url'
    USER_SCORE_FIELD = 'user_score'
    PRIME_DATE_FIELD = 'date'
    COUNTRY_FIELD = 'country'
    DURATION_FIELD = 'duration'


class StreamStatus(IntEnum):
    NEW = 0
    INIT = 1
    STARTED = 2
    READY = 3
    PLAYING = 4
    FROZEN = 5
    WAITING = 6


class StreamLogLevel(IntEnum):
    LOG_LEVEL_EMERG = 0
    LOG_LEVEL_ALERT = 1
    LOG_LEVEL_CRIT = 2
    LOG_LEVEL_ERR = 3
    LOG_LEVEL_WARNING = 4
    LOG_LEVEL_NOTICE = 5
    LOG_LEVEL_INFO = 6
    LOG_LEVEL_DEBUG = 7

    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return cls(int(item)) if not isinstance(item, cls) else item

    def __str__(self):
        return str(self.value)


class IStream(Document):
    meta = {'collection': 'streams', 'allow_inheritance': True, 'auto_create_index': True}

    created_date = DateTimeField(default=datetime.now)  # for inner use
    name = StringField(default=constants.DEFAULT_STREAM_NAME, max_length=constants.MAX_STREAM_NAME_LENGTH,
                       min_length=constants.MIN_STREAM_NAME_LENGTH, required=True)
    group = StringField(default=constants.DEFAULT_STREAM_GROUP_TITLE,
                        max_length=constants.MAX_STREAM_GROUP_TITLE_LENGTH,
                        min_length=constants.MIN_STREAM_GROUP_TITLE_LENGTH, required=True)

    tvg_id = StringField(default=constants.DEFAULT_STREAM_TVG_ID, max_length=constants.MAX_STREAM_TVG_ID_LENGTH,
                         min_length=constants.MIN_STREAM_TVG_ID_LENGTH,
                         required=True)
    tvg_name = StringField(default=constants.DEFAULT_STREAM_TVG_NAME, max_length=constants.MAX_STREAM_NAME_LENGTH,
                           min_length=constants.MIN_STREAM_NAME_LENGTH, required=True)  #
    tvg_logo = StringField(default=constants.DEFAULT_STREAM_ICON_URL, max_length=constants.MAX_URL_LENGTH,
                           min_length=constants.MIN_URL_LENGTH, required=True)  #

    price = FloatField(default=0.0, min_value=constants.MIN_PRICE, max_value=constants.MAX_PRICE, required=True)
    visible = BooleanField(default=True, required=True)
    iarc = IntField(default=21, min_value=0, required=True)  # https://support.google.com/googleplay/answer/6209544

    output = EmbeddedDocumentField(OutputUrls, default=OutputUrls())  #

    def get_groups(self) -> list:
        return self.group.split(';')

    def to_dict(self) -> dict:
        return {StreamFields.NAME_FIELD: self.name, StreamFields.ID_FIELD: self.get_id(),
                StreamFields.TYPE_FIELD: self.get_type(),
                StreamFields.ICON_FIELD: self.tvg_logo, StreamFields.PRICE_FIELD: self.price,
                StreamFields.VISIBLE_FIELD: self.visible,
                StreamFields.IARC_FIELD: self.iarc, StreamFields.GROUP_FIELD: self.group}

    def to_front_dict(self) -> dict:
        return {StreamFields.NAME_FIELD: self.name, StreamFields.ID_FIELD: self.get_id(),
                StreamFields.TYPE_FIELD: self.get_type(),
                StreamFields.ICON_FIELD: self.tvg_logo, StreamFields.PRICE_FIELD: self.price,
                StreamFields.VISIBLE_FIELD: self.visible,
                StreamFields.IARC_FIELD: self.iarc, StreamFields.GROUP_FIELD: self.group}

    def __init__(self, *args, **kwargs):
        super(IStream, self).__init__(*args, **kwargs)
        self._settings = None

    def set_server_settings(self, settings):
        self._settings = settings

    def get_type(self):
        raise NotImplementedError('subclasses must override get_type()!')

    def get_id(self) -> str:
        return str(self.id)

    def config(self) -> dict:
        return {
            ConfigFields.ID_FIELD: self.get_id(),  # required
            ConfigFields.TYPE_FIELD: self.get_type(),  # required
            ConfigFields.OUTPUT_FIELD: self.output.to_mongo()  # required empty in timeshift_record
        }

    def fixup_output_urls(self):
        return

    def reset(self):
        return

    def generate_playlist(self, header=True) -> str:
        result = '#EXTM3U\n' if header else ''
        stream_type = self.get_type()
        if stream_type == constants.StreamType.RELAY or stream_type == constants.StreamType.VOD_RELAY or stream_type == constants.StreamType.COD_RELAY or \
                stream_type == constants.StreamType.ENCODE or stream_type == constants.StreamType.VOD_ENCODE or stream_type == constants.StreamType.COD_ENCODE or \
                stream_type == constants.StreamType.PROXY or stream_type == constants.StreamType.VOD_PROXY or stream_type == constants.StreamType.VOD_ENCODE or \
                stream_type == constants.StreamType.TIMESHIFT_PLAYER or stream_type == constants.StreamType.CATCHUP:
            for out in self.output.urls:
                result += '#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" tvg-logo="{2}" group-title="{3}",{4}\n{5}\n'.format(
                    self.tvg_id,
                    self.tvg_name,
                    self.tvg_logo,
                    self.group,
                    self.name,
                    out.uri)

        return result

    def generate_device_playlist(self, uid: str, passwd: str, did: str, lb_server_host_and_port: str,
                                 header=True) -> str:
        result = '#EXTM3U\n' if header else ''
        stream_type = self.get_type()
        if stream_type == constants.StreamType.RELAY or stream_type == constants.StreamType.VOD_RELAY or stream_type == constants.StreamType.COD_RELAY or \
                stream_type == constants.StreamType.ENCODE or stream_type == constants.StreamType.VOD_ENCODE or stream_type == constants.StreamType.COD_ENCODE or \
                stream_type == constants.StreamType.PROXY or stream_type == constants.StreamType.VOD_PROXY or stream_type == constants.StreamType.VOD_ENCODE or \
                stream_type == constants.StreamType.TIMESHIFT_PLAYER or stream_type == constants.StreamType.CATCHUP:
            for out in self.output.urls:
                parsed_uri = urlparse(out.uri)
                if parsed_uri.scheme == 'http' or parsed_uri.scheme == 'https':
                    file_name = os.path.basename(parsed_uri.path)
                    url = 'http://{0}/{1}/{2}/{3}/{4}/{5}/{6}'.format(lb_server_host_and_port, uid, passwd, did,
                                                                      self.id,
                                                                      out.id, file_name)
                    result += '#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" tvg-logo="{2}" group-title="{3}",{4}\n{5}\n'.format(
                        self.tvg_id,
                        self.tvg_name,
                        self.tvg_logo,
                        self.group,
                        self.name,
                        url)

        return result

    def generate_input_playlist(self, header=True) -> str:
        raise NotImplementedError('subclasses must override generate_input_playlist()!')

    def save(self, *args, **kwargs):
        super(IStream, self).save(*args, **kwargs)
        self.fixup_output_urls()
        return super(IStream, self).save(*args, **kwargs)


class ProxyStream(IStream):
    def __init__(self, *args, **kwargs):
        super(ProxyStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.PROXY

    def generate_input_playlist(self, header=True) -> str:
        return self.generate_playlist(header)

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


class HardwareStream(IStream):
    log_level = IntField(default=StreamLogLevel.LOG_LEVEL_INFO, required=True)

    input = EmbeddedDocumentField(InputUrls, default=InputUrls())
    have_video = BooleanField(default=constants.DEFAULT_HAVE_VIDEO, required=True)
    have_audio = BooleanField(default=constants.DEFAULT_HAVE_AUDIO, required=True)
    audio_select = IntField(default=constants.INVALID_AUDIO_SELECT, required=True)
    loop = BooleanField(default=constants.DEFAULT_LOOP, required=True)
    avformat = BooleanField(default=constants.DEFAULT_AVFORMAT, required=True)
    restart_attempts = IntField(default=constants.DEFAULT_RESTART_ATTEMPTS, required=True)
    auto_exit_time = IntField(default=constants.DEFAULT_AUTO_EXIT_TIME, required=True)

    # runtime
    _status = StreamStatus.NEW
    _cpu = 0.0
    _timestamp = 0
    _idle_time = 0
    _rss = 0
    _loop_start_time = 0
    _restarts = 0
    _start_time = 0
    _input_streams = str()
    _output_streams = str()

    def __init__(self, *args, **kwargs):
        super(HardwareStream, self).__init__(*args, **kwargs)

    def get_type(self):
        raise NotImplementedError('subclasses must override get_type()!')

    def reset(self):
        self._status = StreamStatus.NEW
        self._cpu = 0.0
        self._timestamp = 0
        self._idle_time = 0
        self._rss = 0
        self._loop_start_time = 0
        self._restarts = 0
        self._start_time = 0
        self._input_streams = str()
        self._output_streams = str()

    def update_runtime_fields(self, params: dict):
        assert self.get_id() == params[StreamFields.ID_FIELD]
        assert self.get_type() == params[StreamFields.TYPE_FIELD]
        self._status = StreamStatus(params[StreamFields.STATUS_FIELD])
        self._cpu = params[StreamFields.CPU_FIELD]
        self._timestamp = params[StreamFields.TIMESTAMP_FIELD]
        self._idle_time = params[StreamFields.IDLE_TIME_FIELD]
        self._rss = params[StreamFields.RSS_FIELD]
        self._loop_start_time = params[StreamFields.LOOP_START_TIME_FIELD]
        self._restarts = params[StreamFields.RESTARTS_FIELD]
        self._start_time = params[StreamFields.START_TIME_FIELD]
        self._input_streams = params[StreamFields.INPUT_STREAMS_FIELD]
        self._output_streams = params[StreamFields.OUTPUT_STREAMS_FIELD]

    def to_dict(self) -> dict:
        front = super(HardwareStream, self).to_dict()
        front[StreamFields.STATUS_FIELD] = self._status
        front[StreamFields.CPU_FIELD] = self._cpu
        front[StreamFields.TIMESTAMP_FIELD] = self._timestamp
        front[StreamFields.IDLE_TIME_FIELD] = self._idle_time
        front[StreamFields.RSS_FIELD] = self._rss
        front[StreamFields.LOOP_START_TIME_FIELD] = self._loop_start_time
        front[StreamFields.RESTARTS_FIELD] = self._restarts
        front[StreamFields.START_TIME_FIELD] = self._start_time
        front[StreamFields.INPUT_STREAMS_FIELD] = self._input_streams
        front[StreamFields.OUTPUT_STREAMS_FIELD] = self._output_streams
        # runtime
        work_time = self._timestamp - self._start_time
        quality = 100 - (100 * self._idle_time / work_time) if work_time else 100
        front[StreamFields.QUALITY_FIELD] = quality
        return front

    def config(self) -> dict:
        conf = super(HardwareStream, self).config()
        conf[ConfigFields.FEEDBACK_DIR_FIELD] = self.generate_feedback_dir()
        conf[ConfigFields.LOG_LEVEL_FIELD] = self.get_log_level()
        conf[ConfigFields.AUTO_EXIT_TIME_FIELD] = self.get_auto_exit_time()
        conf[ConfigFields.LOOP_FIELD] = self.get_loop()
        conf[ConfigFields.AVFORMAT_FIELD] = self.get_avformat()
        conf[ConfigFields.HAVE_VIDEO_FIELD] = self.get_have_video()  # required
        conf[ConfigFields.HAVE_AUDIO_FIELD] = self.get_have_audio()  # required
        conf[ConfigFields.RESTART_ATTEMPTS_FIELD] = self.get_restart_attempts()
        conf[ConfigFields.INPUT_FIELD] = self.input.to_mongo()  # required empty in timeshift_player

        audio_select = self.get_audio_select()
        if audio_select != constants.INVALID_AUDIO_SELECT:
            conf[ConfigFields.AUDIO_SELECT_FIELD] = audio_select
        return conf

    def generate_feedback_dir(self):
        return '{0}/{1}/{2}'.format(self._settings.feedback_directory, self.get_type(), self.get_id())

    def generate_http_link(self, hls_type: constants.HlsType,
                           playlist_name=constants.DEFAULT_HLS_PLAYLIST) -> OutputUrl:
        oid = OutputUrl.generate_id()
        http_root = self._generate_http_root_dir(oid)
        link = '{0}/{1}'.format(http_root, playlist_name)
        return OutputUrl(id=oid, uri=self._settings.generate_http_link(link), http_root=http_root, hls_type=hls_type)

    def generate_vod_link(self, hls_type: constants.HlsType, playlist_name=constants.DEFAULT_HLS_PLAYLIST) -> OutputUrl:
        oid = OutputUrl.generate_id()
        vods_root = self._generate_vods_root_dir(oid)
        link = '{0}/{1}'.format(vods_root, playlist_name)
        return OutputUrl(id=oid, uri=self._settings.generate_vods_link(link), http_root=vods_root, hls_type=hls_type)

    def generate_cod_link(self, hls_type: constants.HlsType, playlist_name=constants.DEFAULT_HLS_PLAYLIST) -> OutputUrl:
        oid = OutputUrl.generate_id()
        cods_root = self._generate_cods_root_dir(oid)
        link = '{0}/{1}'.format(cods_root, playlist_name)
        return OutputUrl(id=oid, uri=self._settings.generate_cods_link(link), http_root=cods_root, hls_type=hls_type)

    def get_log_level(self):
        return self.log_level

    def get_audio_select(self):
        return self.audio_select

    def get_have_video(self):
        return self.have_video

    def get_have_audio(self):
        return self.have_audio

    def get_loop(self):
        return self.loop

    def get_avformat(self):
        return self.avformat

    def get_restart_attempts(self):
        return self.restart_attempts

    def get_auto_exit_time(self):
        return self.auto_exit_time

    def generate_input_playlist(self, header=True) -> str:
        result = '#EXTM3U\n' if header else ''
        stream_type = self.get_type()
        if stream_type == constants.StreamType.RELAY or \
                stream_type == constants.StreamType.ENCODE or \
                stream_type == constants.StreamType.TIMESHIFT_PLAYER or \
                stream_type == constants.StreamType.VOD_ENCODE or \
                stream_type == constants.StreamType.VOD_RELAY:
            for out in self.input.urls:
                result += '#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" tvg-logo="{2}" group-title="{3}",{4}\n{5}\n'.format(
                    self.tvg_id,
                    self.tvg_name,
                    self.tvg_logo,
                    self.group,
                    self.name,
                    out.uri)

        return result

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream

    # private
    def _generate_http_root_dir(self, oid: int):
        return '{0}/{1}/{2}/{3}'.format(self._settings.hls_directory, self.get_type(), self.get_id(), oid)

    def _generate_vods_root_dir(self, oid: int):
        return '{0}/{1}/{2}/{3}'.format(self._settings.vods_directory, self.get_type(), self.get_id(), oid)

    def _generate_cods_root_dir(self, oid: int):
        return '{0}/{1}/{2}/{3}'.format(self._settings.cods_directory, self.get_type(), self.get_id(), oid)

    def _fixup_http_output_urls(self):
        for idx, val in enumerate(self.output.urls):
            url = val.uri
            if url == constants.DEFAULT_TEST_URL:
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self.output.urls[idx] = self.generate_http_link(val.hls_type, filename)

    def _fixup_vod_output_urls(self):
        for idx, val in enumerate(self.output.urls):
            url = val.uri
            if url == constants.DEFAULT_TEST_URL:
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self.output.urls[idx] = self.generate_vod_link(val.hls_type, filename)

    def _fixup_cod_output_urls(self):
        for idx, val in enumerate(self.output.urls):
            url = val.uri
            if url == constants.DEFAULT_TEST_URL:
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self.output.urls[idx] = self.generate_cod_link(val.hls_type, filename)


class RelayStream(HardwareStream):
    def __init__(self, *args, **kwargs):
        super(RelayStream, self).__init__(*args, **kwargs)

    video_parser = StringField(default=constants.DEFAULT_VIDEO_PARSER, required=True)
    audio_parser = StringField(default=constants.DEFAULT_AUDIO_PARSER, required=True)

    def get_type(self):
        return constants.StreamType.RELAY

    def config(self) -> dict:
        conf = super(RelayStream, self).config()
        conf[ConfigFields.VIDEO_PARSER_FIELD] = self.get_video_parser()
        conf[ConfigFields.AUDIO_PARSER_FIELD] = self.get_audio_parser()
        return conf

    def get_video_parser(self):
        return self.video_parser

    def get_audio_parser(self):
        return self.audio_parser

    def fixup_output_urls(self):
        return self._fixup_http_output_urls()

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


class EncodeStream(HardwareStream):
    def __init__(self, *args, **kwargs):
        super(EncodeStream, self).__init__(*args, **kwargs)

    relay_video = BooleanField(default=constants.DEFAULT_RELAY_VIDEO, required=True)
    relay_audio = BooleanField(default=constants.DEFAULT_RELAY_AUDIO, required=True)
    deinterlace = BooleanField(default=constants.DEFAULT_DEINTERLACE, required=True)
    frame_rate = IntField(default=constants.INVALID_FRAME_RATE, required=True)
    volume = FloatField(default=constants.DEFAULT_VOLUME, required=True)
    video_codec = StringField(default=constants.DEFAULT_VIDEO_CODEC, required=True)
    audio_codec = StringField(default=constants.DEFAULT_AUDIO_CODEC, required=True)
    audio_channels_count = IntField(default=constants.INVALID_AUDIO_CHANNELS_COUNT, required=True)
    size = EmbeddedDocumentField(Size, default=Size())
    video_bit_rate = IntField(default=constants.INVALID_VIDEO_BIT_RATE, required=True)
    audio_bit_rate = IntField(default=constants.INVALID_AUDIO_BIT_RATE, required=True)
    logo = EmbeddedDocumentField(Logo, default=Logo())
    rsvg_logo = EmbeddedDocumentField(RSVGLogo, default=RSVGLogo())
    aspect_ratio = EmbeddedDocumentField(Rational, default=Rational())

    def get_type(self):
        return constants.StreamType.ENCODE

    def get_relay_video(self):
        return self.relay_video

    def get_relay_audio(self):
        return self.relay_audio

    def config(self) -> dict:
        conf = super(EncodeStream, self).config()
        conf[ConfigFields.RELAY_VIDEO_FIELD] = self.get_relay_video()
        conf[ConfigFields.RELAY_AUDIO_FIELD] = self.get_relay_audio()
        conf[ConfigFields.DEINTERLACE_FIELD] = self.get_deinterlace()
        frame_rate = self.get_frame_rate()
        if frame_rate != constants.INVALID_FRAME_RATE:
            conf[ConfigFields.FRAME_RATE_FIELD] = frame_rate
        conf[ConfigFields.VOLUME_FIELD] = self.get_volume()
        conf[ConfigFields.VIDEO_CODEC_FIELD] = self.get_video_codec()
        conf[ConfigFields.AUDIO_CODEC_FIELD] = self.get_audio_codec()
        audio_channels = self.get_audio_channels_count()
        if audio_channels != constants.INVALID_AUDIO_CHANNELS_COUNT:
            conf[ConfigFields.AUDIO_CHANNELS_COUNT_FIELD] = audio_channels

        if self.size.is_valid():
            conf[ConfigFields.SIZE_FIELD] = str(self.size)

        vid_rate = self.get_video_bit_rate()
        if vid_rate != constants.INVALID_VIDEO_BIT_RATE:
            conf[ConfigFields.VIDEO_BIT_RATE_FIELD] = vid_rate
        audio_rate = self.get_audio_bit_rate()
        if audio_rate != constants.INVALID_AUDIO_BIT_RATE:
            conf[ConfigFields.AUDIO_BIT_RATE_FIELD] = self.get_audio_bit_rate()
        if self.logo.is_valid():
            conf[ConfigFields.LOGO_FIELD] = self.logo.to_dict()
        if self.rsvg_logo.is_valid():
            conf[ConfigFields.RSVG_LOGO_FIELD] = self.rsvg_logo.to_dict()
        if self.aspect_ratio.is_valid():
            conf[ConfigFields.ASPCET_RATIO_FIELD] = str(self.aspect_ratio)
        return conf

    def get_deinterlace(self):
        return self.deinterlace

    def get_frame_rate(self):
        return self.frame_rate

    def get_volume(self):
        return self.volume

    def get_video_codec(self):
        return self.video_codec

    def get_audio_codec(self):
        return self.audio_codec

    def get_audio_channels_count(self):
        return self.audio_channels_count

    def get_video_bit_rate(self):
        return self.video_bit_rate

    def get_audio_bit_rate(self):
        return self.audio_bit_rate

    def fixup_output_urls(self):
        return self._fixup_http_output_urls()

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


class TimeshiftRecorderStream(RelayStream):
    def __init__(self, *args, **kwargs):
        super(TimeshiftRecorderStream, self).__init__(*args, **kwargs)

    timeshift_chunk_duration = IntField(default=constants.DEFAULT_TIMESHIFT_CHUNK_DURATION, required=True)
    timeshift_chunk_life_time = IntField(default=constants.DEFAULT_TIMESHIFT_CHUNK_LIFE_TIME, required=True)

    def get_type(self):
        return constants.StreamType.TIMESHIFT_RECORDER

    def config(self) -> dict:
        conf = super(TimeshiftRecorderStream, self).config()
        conf[ConfigFields.TIMESHIFT_CHUNK_DURATION] = self.get_timeshift_chunk_duration()
        conf[ConfigFields.TIMESHIFT_DIR] = self.generate_timeshift_dir()
        conf[ConfigFields.TIMESHIFT_CHUNK_LIFE_TIME] = self.timeshift_chunk_life_time
        return conf

    def get_timeshift_chunk_duration(self):
        return self.timeshift_chunk_duration

    def generate_timeshift_dir(self):
        return '{0}/{1}'.format(self._settings.timeshifts_directory, self.get_id())

    def fixup_output_urls(self):
        return

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream.visible = False
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        return stream


class CatchupStream(TimeshiftRecorderStream):
    def __init__(self, *args, **kwargs):
        super(CatchupStream, self).__init__(*args, **kwargs)
        self.timeshift_chunk_duration = constants.DEFAULT_CATCHUP_CHUNK_DURATION
        self.auto_exit_time = constants.DEFAULT_CATCHUP_EXIT_TIME

    def get_type(self):
        return constants.StreamType.CATCHUP

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        return stream


class TimeshiftPlayerStream(RelayStream):
    timeshift_dir = StringField(required=True)  # FIXME default
    timeshift_delay = IntField(default=constants.DEFAULT_TIMESHIFT_DELAY, required=True)

    def __init__(self, *args, **kwargs):
        super(TimeshiftPlayerStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.TIMESHIFT_PLAYER

    def config(self) -> dict:
        conf = super(TimeshiftPlayerStream, self).config()
        conf[ConfigFields.TIMESHIFT_DIR] = self.timeshift_dir
        conf[ConfigFields.TIMESHIFT_DELAY] = self.timeshift_delay
        return conf

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


class TestLifeStream(RelayStream):
    def __init__(self, *args, **kwargs):
        super(TestLifeStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.TEST_LIFE

    def config(self) -> dict:
        conf = super(TestLifeStream, self).config()
        return conf

    def fixup_output_urls(self):
        return

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.visible = False
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id(), uri=constants.DEFAULT_TEST_URL)])
        return stream


class CodRelayStream(RelayStream):
    def __init__(self, *args, **kwargs):
        super(CodRelayStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.COD_RELAY

    def config(self) -> dict:
        conf = super(CodRelayStream, self).config()
        return conf

    def fixup_output_urls(self):
        return self._fixup_cod_output_urls()

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


class CodEncodeStream(EncodeStream):
    def __init__(self, *args, **kwargs):
        super(CodEncodeStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.COD_ENCODE

    def config(self) -> dict:
        conf = super(CodEncodeStream, self).config()
        return conf

    def fixup_output_urls(self):
        return self._fixup_cod_output_urls()

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


# VODS


class VodBasedStream:
    MAX_DATE = datetime(2100, 1, 1)
    MIN_DATE = datetime(1970, 1, 1)
    DEFAULT_COUNTRY = 'Unknown'
    vod_type = IntField(default=constants.VodType.VODS, required=True)
    description = StringField(default=constants.DEFAULT_STREAM_DESCRIPTION,
                              min_length=constants.MIN_STREAM_DESCRIPTION_LENGTH,
                              max_length=constants.MAX_STREAM_DESCRIPTION_LENGTH,
                              required=True)
    trailer_url = StringField(default=constants.INVALID_TRAILER_URL, max_length=constants.MAX_URL_LENGTH,
                              min_length=constants.MIN_URL_LENGTH, required=True)
    user_score = FloatField(default=0, min_value=0, max_value=100, required=True)
    prime_date = DateTimeField(default=MIN_DATE, min_value=MIN_DATE, max_value=MAX_DATE, required=True)
    country = StringField(default=DEFAULT_COUNTRY, required=True)
    duration = IntField(default=0, min_value=0, max_value=constants.MAX_VIDEO_DURATION_MSEC, required=True)

    def to_dict(self) -> dict:
        return {VodFields.DESCRIPTION_FIELD: self.description,
                VodFields.TRAILER_URL_FIELD: self.trailer_url, VodFields.USER_SCORE_FIELD: self.user_score,
                VodFields.PRIME_DATE_FIELD: date_to_utc_msec(self.prime_date), VodFields.COUNTRY_FIELD: self.country,
                VodFields.DURATION_FIELD: self.duration}


class ProxyVodStream(ProxyStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(ProxyVodStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.VOD_PROXY

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


class VodRelayStream(RelayStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(VodRelayStream, self).__init__(*args, **kwargs)
        self.loop = False

    def get_type(self):
        return constants.StreamType.VOD_RELAY

    def to_dict(self) -> dict:
        front = RelayStream.to_dict(self)
        base = VodBasedStream.to_dict(self)
        return {**front, **base}

    def config(self) -> dict:
        conf = RelayStream.config(self)
        conf[ConfigFields.VODS_CLEANUP_TS] = True
        return conf

    def fixup_output_urls(self):
        return self._fixup_vod_output_urls()

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


class VodEncodeStream(EncodeStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(VodEncodeStream, self).__init__(*args, **kwargs)
        self.loop = False

    def get_type(self):
        return constants.StreamType.VOD_ENCODE

    def to_dict(self) -> dict:
        front = EncodeStream.to_dict(self)
        base = VodBasedStream.to_dict(self)
        return {**front, **base}

    def config(self) -> dict:
        conf = EncodeStream.config(self)
        conf[ConfigFields.VODS_CLEANUP_TS] = True
        return conf

    def fixup_output_urls(self):
        return self._fixup_vod_output_urls()

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream


class EventStream(VodEncodeStream):
    def get_type(self):
        return constants.StreamType.EVENT

    @classmethod
    def make_stream(cls, settings):
        stream = cls()
        stream._settings = settings
        stream.input = InputUrls(urls=[InputUrl(id=InputUrl.generate_id())])
        stream.output = OutputUrls(urls=[OutputUrl(id=OutputUrl.generate_id())])
        return stream
