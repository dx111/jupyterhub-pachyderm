from traitlets import Unicode
from jupyterhub.auth import Authenticator

from tornado import gen
import python_pachyderm

class PachydermAuthenticator(Authenticator):
    password = Unicode(
        "",
        config=True,
        help="If pachyderm auth is not enabled, this global password will be used for all logins."
    )

    @gen.coroutine
    def authenticate(self, handler, data):
        if data['password'] == self.password:
            return data['username']
        return None
