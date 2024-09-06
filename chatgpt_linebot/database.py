from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
import logging

# 設置 SQLAlchemy 的日誌級別為 WARNING
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

Base = declarative_base()
engine = create_engine('sqlite:///user_settings.db', echo=True)
Session = sessionmaker(bind=engine)

class UserSettings(Base):
    __tablename__ = 'user_settings'

    line_user_id = Column(String, primary_key=True)
    threads_user_id = Column(String)
    encrypted_token = Column(String)

Base.metadata.create_all(engine)

# 加密相關函數
def generate_key():
    return Fernet.generate_key()

def load_key():
    try:
        with open("encryption_key.key", "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        key = generate_key()
        with open("encryption_key.key", "wb") as key_file:
            key_file.write(key)
        return key

def encrypt_token(token):
    key = load_key()
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    key = load_key()
    f = Fernet(key)
    return f.decrypt(encrypted_token.encode()).decode()

# 數據庫操作函數
def get_user_settings(line_user_id):
    session = Session()
    user_settings = session.query(UserSettings).filter_by(line_user_id=line_user_id).first()
    session.close()
    return user_settings

def save_user_settings(line_user_id, threads_user_id, token):
    session = Session()
    user_settings = session.query(UserSettings).filter_by(line_user_id=line_user_id).first()
    if user_settings:
        user_settings.threads_user_id = threads_user_id
        user_settings.encrypted_token = encrypt_token(token)
    else:
        user_settings = UserSettings(line_user_id=line_user_id, threads_user_id=threads_user_id, encrypted_token=encrypt_token(token))
        session.add(user_settings)
    session.commit()
    session.close()
