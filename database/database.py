from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base
from .models import Channel,ChannelBotRelation, Bot


class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def add_record(self, record):
        session = self.Session()
        session.add(record)
        session.commit()
        session.close()

    def get_record(self, model, **filters):
        session = self.Session()
        record = session.query(model).filter_by(**filters).first()
        session.close()
        return record

    def update_record(self, model, primary_key_value, **updates):
        session = self.Session()
        record = session.query(model).get(primary_key_value)
        for key, value in updates.items():
            setattr(record, key, value)
        session.commit()
        session.close()

    def delete_record(self, model, **filters):
        session = self.Session()
        record = session.query(model).filter_by(**filters).first()
        session.delete(record)
        session.commit()
        session.close()

    def get_channel_by_telegram_id(self, telegram_id):
        session = self.Session()
        channel = session.query(Channel).filter_by(telegram_id=telegram_id).first()
        session.close()
        return channel

    def get_channels_by_bot_id(self, bot_id):
        session = self.Session()
        relations = session.query(ChannelBotRelation).filter_by(bot_id=bot_id).all()
        channels = [session.query(Channel).get(relation.channel_id) for relation in relations]
        session.close()
        return channels

    def get_bot_id_by_phone(self, phone):
        session = self.Session()
        bot = session.query(Bot).filter_by(phone=phone).first()
        session.close()
        return bot.bot_id

    def get_channel_id_by_tg_id(self, channel_id):
        session = self.Session()
        channel = session.query(Channel).filter_by(telegram_id=channel_id).first()
        session.close()
        return channel.channel_id

    def is_channel_in_db(self, channel_id: int) -> bool:
        """
        Проверяет, существует ли канал с заданным ID в базе данных.

        :param channel_id: ID канала для проверки.
        :param session: Сессия SQLAlchemy для запросов к базе данных.
        :return: True, если канал существует, иначе False.
        """
        session = self.Session()

        return session.query(Channel.telegram_id).filter_by(telegram_id=channel_id).first() is not None