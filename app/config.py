import os

def getSettings():
    return '%s.%s' % (__name__, os.environ.get('CONFIG_SETTINGS', 'ProductionConfig'))

class Config(object):
    DEBUG = False
    TESTING = False
    BASE_DIR = os.path.abspath('app')

class ProductionConfig(Config):
    DEBUG = True

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True