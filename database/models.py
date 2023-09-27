from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON,BigInteger, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Bot(Base):
    __tablename__ = 'bots'

    bot_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    phone = Column(String, nullable=False)
    proxy = Column(String, nullable=False)
    api_id = Column(String, nullable=False)
    api_hash = Column(String, nullable=False)
    request_count = Column(BigInteger, default=0)

    channels = relationship("ChannelBotRelation", back_populates="bot")


class Channel(Base):
    __tablename__ = 'channels'

    channel_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    username = Column(String)
    telegram_id = Column(BigInteger, nullable=False)
    date_added = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="channel")
    subscribers = relationship("ChannelSubscriber", back_populates="channel")
    bots = relationship("ChannelBotRelation", back_populates="channel")


class ChannelSubscriber(Base):
    __tablename__ = 'channel_subscribers'

    subscriber_id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, ForeignKey('channels.channel_id'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    subscribers_count = Column(BigInteger, nullable=False)

    channel = relationship("Channel", back_populates="subscribers")


class Media(Base):
    __tablename__ = 'media'

    media_id = Column(BigInteger, primary_key=True)
    post_id = Column(BigInteger, ForeignKey('posts.post_id'), nullable=False)
    media_type = Column(String, nullable=False)
    caption = Column(String)
    content = Column(String, nullable=False)  # base64 encoded media content
    is_deleted = Column(Boolean, default=False)

    post = relationship("Post", back_populates="media")


class Post(Base):
    __tablename__ = 'posts'

    post_id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, ForeignKey('channels.channel_id'), nullable=False)
    date_time = Column(DateTime, default=datetime.utcnow)
    content = Column(JSON, nullable=False)  # JSON for text and other non-media content
    views_count = Column(BigInteger, nullable=False)
    is_deleted = Column(Boolean, default=False)
    link = Column(String)
    forwarded_from = Column(BigInteger)  # You can also use ForeignKey if you want to link to another table

    channel = relationship("Channel", back_populates="posts")
    media = relationship("Media", back_populates="post", cascade="all, delete-orphan")


class ChannelBotRelation(Base):
    __tablename__ = 'channel_bot_relations'

    relation_id = Column(BigInteger, primary_key=True)
    bot_id = Column(BigInteger, ForeignKey('bots.bot_id'), nullable=False)
    channel_id = Column(BigInteger, ForeignKey('channels.channel_id'), nullable=False)

    bot = relationship("Bot", back_populates="channels")
    channel = relationship("Channel", back_populates="bots")