import os

CLIENTS_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class Auth:
    """Google Project Credentials"""
    CLIENT_ID = ('355555968186-5c3625bhidt1php2r43o99l54'
    '9b330pg.apps.googleusercontent.com')
    CLIENT_SECRET = 'PBuraFRzRNmjSuQBBFx-7HVE'
    REDIRECT_URI = 'http://localhost:5000/gCallback'
    #REDIRECT_URI = 'https://cryptic-atoll-57043.herokuapp.com/gCallback'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']

class Config:
    APP_NAME = "Test Google Login"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "somethingsecret"

class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/database'

class ProdConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgres://bshmgrkejlgotn:5ece12ee68b3873c94f6e26b3fbc6ff56ee2e7be06da7c207a056504bda48c5f@ec2-174-129-22-84.compute-1.amazonaws.com:5432/d1h8g0af3p6rag'

config = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "default": DevConfig
}
