from datetime import datetime

from mongoengine import Document, StringField, DateTimeField, IntField, BooleanField

import pyfastocloud_models.constants as constants


class Serial(Document):
    DEFAULT_SERIES_NAME = 'Serial'
    MIN_SERIES_NAME_LENGTH = 3
    MAX_SERIES_NAME_LENGTH = 30

    meta = {'collection': 'series', 'auto_create_index': False}

    created_date = DateTimeField(default=datetime.now)  # for inner use
    name = StringField(unique=True, default=DEFAULT_SERIES_NAME, max_length=MAX_SERIES_NAME_LENGTH,
                       min_length=MIN_SERIES_NAME_LENGTH)
    group = StringField(default=constants.DEFAULT_STREAM_GROUP_TITLE,
                        max_length=constants.MAX_STREAM_GROUP_TITLE_LENGTH,
                        min_length=constants.MIN_STREAM_GROUP_TITLE_LENGTH, required=True)
    description = StringField(default=constants.DEFAULT_STREAM_DESCRIPTION,
                              min_length=constants.MIN_STREAM_DESCRIPTION_LENGTH,
                              max_length=constants.MAX_STREAM_DESCRIPTION_LENGTH,
                              required=True)
    season = IntField(default=1, min_value=0, required=True)
    visible = BooleanField(default=True, required=True)
