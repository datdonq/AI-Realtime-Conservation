import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, Unicode
from sqlalchemy.inspection import inspect

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    client_id = Column(Integer)  # deprecated, use user_id instead
    # deprecated, use client_message_unicode instead
    client_message = Column(String)
    # deprecated, use server_message_unicode instead
    server_message = Column(String)
    client_message_unicode = Column(Unicode(65535))
    server_message_unicode = Column(Unicode(65535))

    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    platform = Column(String(50))
    action_type = Column(String(50))
    character_id = Column(String(100))
    tools = Column(String(100))
    language = Column(String(10))
    message_id = Column(String(64))
    llm_config = Column(JSON())

    def to_dict(self):
        return {
            c.key: getattr(self, c.key).isoformat()
            if isinstance(getattr(self, c.key), datetime.datetime)
            else getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }

    def save(self, db):
        db.add(self)
        db.commit()
