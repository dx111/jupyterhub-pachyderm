from traitlets import Unicode
from jupyterhub.auth import Authenticator

from tornado import gen
import python_pachyderm

class PachydermAuthenticator(Authenticator):
    pach_auth_token = Unicode(
        "",
        config=True,
        help="Pachyderm auth token. Leave blank if Pachyderm auth is not enabled."
    )

    pach_tls_certs = Unicode(
        "",
        config=True,
        help="Pachyderm root certs. Leave blank if Pachyderm TLS is not enabled, or if system certs should be used."
    )

    global_password = Unicode(
        "",
        config=True,
        help="If Pachyderm auth is not enabled, this global password will be used for all logins."
    )

    @gen.coroutine
    def authenticate(self, handler, data):
        client = python_pachyderm.Client.new_in_cluster(
            auth_token=self.pach_auth_token or None,
            root_certs=self.pach_tls_certs or None,
        )

        auth_activated = True
        try:
            client.who_am_i()
        except python_pachyderm.RpcError as e:
            details = e.details()

            if details == "the auth service is not activated":
                auth_activated = False
            elif details == "no authentication token (try logging in)":
                self.log.error("JupyterHub is configured to not use Pachyderm auth, even though it is enabled. Please manually reconfigure, or redeploy JupyterHub.")
                return
            elif details == "provided auth token is corrupted or has expired (try logging in again)":
                self.log.error("JupyterHub is configured with a bad Pachyderm auth token. Please manually reconfigure, or redeploy JupyterHub.")
                return
            else:
                raise

        if not auth_activated:
            if data["password"] == self.global_password:
                return data["username"]
            return None

        try:
            if data["password"].startswith("otp/"):
                user_auth_token = client.authenticate_one_time_password(data["password"])
            else:
                user_auth_token = client.authenticate_github(data["password"])

            user_client = python_pachyderm.Client.new_in_cluster(
                auth_token=user_auth_token,
                root_certs=self.pach_tls_certs or None,
            )

            username = user_client.who_am_i().username

            return {
                "name": username,
                "auth_state": {
                    "token": user_auth_token,
                }
            }
        except python_pachyderm.RpcError as e:
            self.log.error("auth failed: %s", e)
            return
