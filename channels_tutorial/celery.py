from celery import Celery

app = Celery('channels_tutorial',broker="redis://localhost", include=["socket_api.tasks"] )
app.conf.broker_connection_retry_on_startup = True

