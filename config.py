class Config:
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    RESULT_BACKEND = 'redis://localhost:6379/0'

    @staticmethod
    def init_app(app):
        pass


