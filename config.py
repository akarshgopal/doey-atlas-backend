import os

CLIENTS_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class Auth:
    """Google Project Credentials"""
    CLIENT_ID = ('355555968186-5c3625bhidt1php2r43o99l54'
    '9b330pg.apps.googleusercontent.com')
    CLIENT_SECRET = 'PBuraFRzRNmjSuQBBFx-7HVE'
    REDIRECT_URI = 'https://doey-atlas-back-end.herokuapp.com/doey'
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
    SQLALCHEMY_DATABASE_URI = 'postgres://yjgnltcyjcaejp:af3d3ea4585d9a7f0442851a1583e8dfdd0fd1666ef2ae1ef2edafb77d1a0f17@ec2-50-16-241-91.compute-1.amazonaws.com:5432/d1nq2oqs795e81'

config = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "default": DevConfig
}

frontend_site="https://doey-atlas.herokuapp.com"
login_page = frontend_site + '/login'
home_page = frontend_site + '/doey'
