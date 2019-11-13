from traitlets import Unicode
from jupyterhub.auth import Authenticator

from tornado import gen
import python_pachyderm

MISCONFIGURATION_HTML = """
<h1>Misconfiguration</h1>
<div>There is a misconfiguration with your JupyterHub deployment.</div>
<div>See the logs for the hub pod for details.</div>
<div>In most cases, manually reconfiguring or redeploying JupyterHub fixes the issue.</div>
"""

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

    def pachyderm_client(self, auth_token):
        return python_pachyderm.Client.new_in_cluster(
            auth_token=auth_token,
            root_certs=self.pach_tls_certs or None,
        )

    def is_pachyderm_auth_enabled(self, client):
        try:
            client.who_am_i()
        except python_pachyderm.RpcError as e:
            details = e.details()

            if details == "the auth service is not activated":
                return False
            elif details == "no authentication token (try logging in)":
                self.log.error("JupyterHub is configured to not use Pachyderm auth, even though it is enabled. Please manually reconfigure, or redeploy JupyterHub.")
                return None
            elif details == "provided auth token is corrupted or has expired (try logging in again)":
                self.log.error("JupyterHub is configured with a bad Pachyderm auth token. Please manually reconfigure, or redeploy JupyterHub.")
                return None
            else:
                raise

        return True

    @property
    def custom_html(self):
        client = self.pachyderm_client(self.pach_auth_token or None)
        auth_activated = self.is_pachyderm_auth_enabled(client)

        if auth_activated is None:
            return MISCONFIGURATION_HTML

        # If auth is activated, show the default login pane. This isn't ideal,
        # because the default login includes a username field which is ignored
        # when Pachyderm auth is enabled. However, overriding it here would
        # also remove a number of beneficial features (e.g. the ability to
        # show login error messages) because we can only use static HTML.
        return None

    @gen.coroutine
    def authenticate(self, handler, data):
        client = self.pachyderm_client(self.pach_auth_token or None)
        auth_activated = self.is_pachyderm_auth_enabled(client)
        if auth_activated is None:
            # auth check failed due to misconfiguration - bail
            return
        elif auth_activated is False:
            if data["password"] == self.global_password:
                return data["username"]
            return

        try:
            if data["password"].startswith("otp/"):
                user_auth_token = client.authenticate_one_time_password(data["password"])
            else:
                user_auth_token = client.authenticate_github(data["password"])

            user_client = self.pachyderm_client(user_auth_token)
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
