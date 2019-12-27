from mongoengine import EmbeddedDocument, StringField, IntField, ListField, EmbeddedDocumentField, FloatField, \
    BooleanField

import pyfastocloud_models.constants as constants


class Url(EmbeddedDocument):
    meta = {'allow_inheritance': True, 'auto_create_index': False}

    _next_url_id = 0

    id = IntField(default=lambda: Url.generate_id(), required=True)
    uri = StringField(default='test', max_length=constants.MAX_URL_LENGTH, required=True)

    @staticmethod
    def generate_id():
        current_value = Url._next_url_id
        Url._next_url_id += 1
        return current_value


class HttpProxy(EmbeddedDocument):
    INVALID_URL = str()
    DEFAULT_USER = str()
    DEFAULT_PASSWORD = str()

    url = StringField(default=INVALID_URL, required=True)
    user = StringField(default=DEFAULT_USER, required=False)
    password = StringField(default=DEFAULT_PASSWORD, required=False)

    def is_valid(self):
        return self.url != HttpProxy.INVALID_URL

    def to_dict(self) -> dict:
        return {'url': self.url}


class InputUrl(Url):
    user_agent = IntField(default=constants.UserAgent.GSTREAMER, required=True)
    stream_link = BooleanField(default=False, required=True)
    proxy = EmbeddedDocumentField(HttpProxy)


class OutputUrl(Url):
    http_root = StringField(default='/', max_length=constants.MAX_PATH_LENGTH, required=False)


# {"urls": [{"id": 81,"uri": "tcp://localhost:1935"}]}
class InputUrls(EmbeddedDocument):
    urls = ListField(EmbeddedDocumentField(InputUrl))


class OutputUrls(EmbeddedDocument):
    urls = ListField(EmbeddedDocumentField(OutputUrl))


class Size(EmbeddedDocument):
    width = IntField(default=constants.INVALID_WIDTH, required=True)
    height = IntField(default=constants.INVALID_HEIGHT, required=True)

    def is_valid(self):
        return self.width != constants.INVALID_WIDTH and self.height != constants.INVALID_HEIGHT

    def __str__(self):
        return '{0}x{1}'.format(self.width, self.height)


class Logo(EmbeddedDocument):
    path = StringField(default=constants.INVALID_LOGO_PATH, required=True)
    x = IntField(default=constants.DEFAULT_LOGO_X, required=True)
    y = IntField(default=constants.DEFAULT_LOGO_Y, required=True)
    alpha = FloatField(default=constants.DEFAULT_LOGO_ALPHA, required=True)
    size = EmbeddedDocumentField(Size, default=Size())

    def is_valid(self):
        return self.path != constants.INVALID_LOGO_PATH

    def to_dict(self) -> dict:
        return {'path': self.path, 'position': '{0},{1}'.format(self.x, self.y), 'alpha': self.alpha,
                'size': str(self.size)}


class RSVGLogo(EmbeddedDocument):
    path = StringField(default=constants.INVALID_LOGO_PATH, required=True)
    x = IntField(default=constants.DEFAULT_LOGO_X, required=True)
    y = IntField(default=constants.DEFAULT_LOGO_Y, required=True)
    size = EmbeddedDocumentField(Size, default=Size())

    def is_valid(self):
        return self.path != constants.INVALID_LOGO_PATH

    def to_dict(self) -> dict:
        return {'path': self.path, 'position': '{0},{1}'.format(self.x, self.y), 'size': str(self.size)}


class Rational(EmbeddedDocument):
    num = IntField(default=constants.INVALID_RATIO_NUM, required=True)
    den = IntField(default=constants.INVALID_RATIO_DEN, required=True)

    def is_valid(self):
        return self.num != constants.INVALID_RATIO_NUM and self.den != constants.INVALID_RATIO_DEN

    def __str__(self):
        return '{0}:{1}'.format(self.num, self.den)


class HostAndPort(EmbeddedDocument):
    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 6317
    host = StringField(default=DEFAULT_HOST, required=True)
    port = IntField(default=DEFAULT_PORT, required=True)

    def __str__(self):
        return '{0}:{1}'.format(self.host, self.port)
