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

    def __init__(self, Settings, Messages, Mongo):
        """Making responses that can be displayed as web pages.

        This class has methods that correspond to routes in the app,
        for which they get the data (using `control.content.Content`),
        which gets then wrapped in HTML.

        It is instantiated by a singleton object.

        Most methods generate a response that contains the content of a complete
        page. For those methods we do not document the return value.

        Some methods return something different.
        If so, it the return value will be documented.

        Parameters
        ----------
        Settings: `control.helpers.generic.AttrDict`
            App-wide configuration data obtained from
            `control.config.Config.Settings`.
        Messages: object
            Singleton instance of `control.messages.Messages`.
        Mongo: object
            Singleton instance of `control.mongo.Mongo`.
        """
        self.Settings = Settings
        self.Mongo = Mongo
        self.Messages = Messages
        Messages.debugAdd(self)

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
            message="This is a test message",
            is_html=False)
        self.send(email)

    def _send(self, email: EmailMessage):
        with self.app.app_context():
            self.debug(f"sending to {email=}")
            msg = self.create_email_message(email)

            try:
                self.mail_client.send(msg)
                self.debug("mail sent successfully")
            except Exception as ex:
                self.debug(f"sending failed: {ex}")

    def send(self, email: EmailMessage):
        if email.message and email.title and email.recipient and self.is_valid_email(email.recipient):
            self._send(email)
        else:
            print(f"cannot send invalid email {email=}")
            sys.stdout.flush()

    def send_raw(self, title: str, recipient: str, message: str):
        email = EmailMessage(title=title, recipient=recipient, message=message)
        self.send(email)
