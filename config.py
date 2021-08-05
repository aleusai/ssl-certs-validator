class Config:
    celery_broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/0'
    worker_prefetch_multiplier = 128
    #worker_max_tasks_per_child = 20
    task_time_limit = 60

    @staticmethod
    def init_app(app):
        pass


