from flask_mail import Mail, Message
from dataclasses import dataclass
import json
import re
import sys


def _json_loads(content):
    if not isinstance(content, str):
        content = content.decode('utf-8')
    return json.loads(content)


@dataclass
class EmailMessage:
    title: str
    message: str
    recipient: str
    is_html: bool = True


class SendMail:
    SEND_MAIL_CONFIGS = "/app/src/pure3d/secret/send_mail_config.json"
    email_re = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    mail_client = None
    app = None

    @classmethod
    def load_config(cls):
        return _json_loads(open(cls.SEND_MAIL_CONFIGS, 'r').read())

    @classmethod
    def prepare(cls, app):
        # configuration of mail
        configs = cls.load_config()
        client_configs = list(configs.values())[0]

        for k, v in client_configs.items():
            app.config[k] = v

        cls.mail_client = Mail(app)
        cls.app = app
        return SendMail()

    @classmethod
    def is_valid_email(cls, email: str):
        return re.fullmatch(cls.email_re, email)

    @classmethod
    def create_email_message(cls, email: EmailMessage):
        # todo: return html or non-html depends on email.is_html
        return Message(
            subject=email.title,
            recipients=[email.recipient],
            body=email.message,
            html=f"<html><body>{email.message}</body></html>"
        ) if email.is_html else Message(
            subject=email.title,
            recipients=[email.recipient],
            body=email.message,
            html=f"<html><body>{email.message}</body></html>"
        )

    def send_test_mail(self, email_address: str):
        email = EmailMessage(
            title="Test message",
            recipient=email_address,
            message="This is a test message", is_html=False)
        try:
            self.send(email)
            print(f"Test email sent to {email_address}")
        except Exception as ex:
            print(f"Test email failed! Recp is {email_address}; {email=}")

    def _send(self, email: EmailMessage):
        with self.app.app_context():
            print(f"sending to {email=}")
            msg = self.create_email_message(email, True)
            sys.stdout.flush()

            try:
                self.mail_client.send(msg)
                print("mail sent")
                sys.stdout.flush()
            except Exception as ex:
                print(f"sending failed {ex}")
                sys.stdout.flush()

    def send(self, email: EmailMessage):
        if email.message and email.title and email.recipient and self.is_valid_email(email.recipient):
            self._send(email)
        else:
            print(f"cannot send email {email=}")
            sys.stdout.flush()
