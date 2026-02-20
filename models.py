from datetime import datetime, timezone
from peewee import (Model, AutoField, CharField, TextField, BooleanField,
                    DateTimeField, IntegerField, ForeignKeyField, CompositeKey)
from playhouse.postgres_ext import JSONField
from database import db


class BaseModel(Model):
    class Meta:
        database = db


class Profile(BaseModel):
    id = AutoField()
    name = CharField(max_length=100, default='')
    bio = TextField(default='')
    avatar_filename = CharField(max_length=255, null=True)
    links = JSONField(default=list)

    class Meta:
        table_name = 'profile'


class Post(BaseModel):
    id = AutoField()
    caption = TextField(default='')
    location = CharField(max_length=255, null=True)
    published = BooleanField(default=False)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = 'posts'


class PostImage(BaseModel):
    id = AutoField()
    post = ForeignKeyField(Post, on_delete='CASCADE', column_name='post_id')
    filename = CharField(max_length=255)
    order = IntegerField(default=0)

    class Meta:
        table_name = 'post_images'


class Tag(BaseModel):
    id = AutoField()
    name = CharField(max_length=100, unique=True, index=True)

    class Meta:
        table_name = 'tags'


class PostTag(BaseModel):
    post = ForeignKeyField(Post, on_delete='CASCADE')
    tag = ForeignKeyField(Tag, on_delete='CASCADE')

    class Meta:
        table_name = 'post_tags'
        primary_key = CompositeKey('post', 'tag')
