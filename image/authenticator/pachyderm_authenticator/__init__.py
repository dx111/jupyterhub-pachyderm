from jupyterhub.auth import Authenticator

from tornado import gen
import python_pachyderm

class PachydermAuthenticator(Authenticator):
    @gen.coroutine
    def authenticate(self, handler, data):
        if data['password'] == "":
            return data['username']
        return None
