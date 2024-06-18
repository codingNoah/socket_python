from celery import shared_task
from django.core.mail import send_mail
# from django.conf import settings
from channels_tutorial.settings import EMAIL_HOST_USER
@shared_task
def send():

    print("sending....")
    # send_mail( subject, message, email_from, recipient_list )
    return 1

# ybub ohks saqy pqyo