from email.message import EmailMessage
import os
import smtplib
import ssl


def send_email(subject, recipients, text_body, html_body=None,
               sender=os.environ.get('MAIL_DEFAULT_SENDER')):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype='html')
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(host=os.environ.get('MAIL_SERVER'),
                          port=os.environ.get('MAIL_PORT'),
                          context=context) as server:
        server.login(os.environ.get('MAIL_USERNAME'),
                     os.environ.get('MAIL_PASSWORD'))
        server.send_message(msg)
