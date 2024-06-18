from celery import shared_task
from django.core.mail import send_mail
# from django.conf import settings
from channels_tutorial.settings import EMAIL_HOST_USER
@shared_task
def send():
    subject = 'welcome to GFG world'
    message = f'Hi arsenal, thank you for registering in geeksforgeeks.'
    email_from = EMAIL_HOST_USER
    recipient_list = ["arsenalgunner636@gmail.com", "tessemayenoh94@gmail.com" ]
    print("sending....")
    # send_mail( subject, message, email_from, recipient_list )
    return 1

# ybub ohks saqy pqyo