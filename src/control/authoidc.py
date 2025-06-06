from flask_oidc import OpenIDConnect
import json


def json_loads(content):
    """Handles loading of json content as unicode strings."""
    if not isinstance(content, str):
        content = content.decode("utf-8")
    return json.loads(content)


class AuthOidc:
    """Invoke the OIDC authentication.

    Here the Pure3D app is configured to work with the CLARIAH authentication provider.

    For that we use the Python module
    [flask-oidc](https://github.com/puiterwijk/flask-oidc).
    """

    OIDC_CLIENT_SECRETS = "/app/secret/client_secrets.json"

    @classmethod
    def load_secrets(cls):
        """Reads secrets used in encryption and decryption."""
        return json_loads(open(cls.OIDC_CLIENT_SECRETS, "r").read())

    @classmethod
    def prepare(cls, app):
        """Injects the OIDC module into the main app."""
        authconf = {
            # 'SECRET_KEY': app.secret_key,
            "TESTING": True,
            "DEBUG": True,
            "OIDC_CLIENT_SECRETS": cls.OIDC_CLIENT_SECRETS,
            # 'OIDC_USER_INFO_ENABLED': True,
            "OIDC_ID_TOKEN_COOKIE_SECURE": False,
            # 'OIDC_REQUIRE_VERIFIED_EMAIL': False,
            # 'OIDC_OPENID_REALM': 'auth realm',
            # 'OVERWRITE_REDIRECT_URI': OpenIDConnect.client_secrets.get("redirect_uris"),
            "CLAIMS": {"userinfo": {"nickname": None, "eppn": None}},
        }
        secrets = cls.load_secrets()
        client_secrets = list(secrets.values())[0]

        # check and set custom redirect
        custom_redirect = client_secrets.get("custom_redirect", None)
        if custom_redirect:
            authconf["OVERWRITE_REDIRECT_URI"] = custom_redirect

        # check and set custom scopes
        custom_scopes = client_secrets.get("custom_scopes", None)
        if custom_scopes:
            authconf["OIDC_SCOPES"] = custom_scopes

        app.config.update(authconf)

        return OpenIDConnect(app)
