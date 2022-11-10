from flask_oidc import OpenIDConnect


class AuthOidc:
    def __init__(self):
        # self.Settings = Settings

        pass

    @classmethod
    def prepare(cls, app):
        app.config.update({
            # 'SECRET_KEY': app.secret_key,
            'TESTING': True,
            'DEBUG': True,
            'OIDC_CLIENT_SECRETS': '/app/src/pure3d/control/client_secrets.json',
            # 'OIDC_USER_INFO_ENABLED': True,
            'OIDC_ID_TOKEN_COOKIE_SECURE': False,
            'OIDC_REQUIRE_VERIFIED_EMAIL': False,
            # 'OIDC_OPENID_REALM': 'auth realm',
            'OVERWRITE_REDIRECT_URI': 'http://localhost:8000/oidc_callback'
        })

        return OpenIDConnect(app)
