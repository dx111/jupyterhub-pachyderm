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

ENTERPRISE_DISABLED_HTML = """
<h1>Enterprise disabled</h1>
<div>Please activate pachyderm enterprise before using jupyterhub-pachyderm.</div>
"""

ENTERPRISE_EXPIRED_HTML = """
<h1>Enterprise expired</h1>
<div>Your enterprise license is expired. Please re-activate before using jupyterhub-pachyderm.</div>
"""

class PachydermAuthenticator(Authenticator):
    # The Pachyderm auth token used for check if auth is enabled and
    # authenticating credentials
    pach_auth_token = Unicode(
        "",
        config=True,
        help="Pachyderm auth token. Leave blank if Pachyderm auth is not enabled."
    )

    # The root certs for pachd TLS
    pach_tls_certs = Unicode(
        "",
        config=True,
        help="Pachyderm root certs. Leave blank if Pachyderm TLS is not enabled, or if system certs should be used."
    )

    def pachyderm_client(self, auth_token):
        """Creates a new Pachyderm client"""
        return python_pachyderm.Client.new_in_cluster(
            auth_token=auth_token,
            root_certs=self.pach_tls_certs or None,
        )

    def is_pachyderm_auth_enabled(self, client):
        """
        Returns whether Pachyderm auth is enabled. Note that if this returns
        `None` (rather than `False`), there is a misconfiguration.
        """
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

        # Check enterprise state
        enterprise_state = client.get_enterprise_state().state
        if enterprise_state is python_pachyderm.State.NONE:
            return ENTERPRISE_DISABLED_HTML
        elif enterprise_state is python_pachyderm.State.EXPIRED:
            return ENTERPRISE_EXPIRED_HTML
        elif enterprise_state is not python_pachyderm.State.ACTIVE:
            return MISCONFIGURATION_HTML

        auth_activated = self.is_pachyderm_auth_enabled(client)
        if auth_activated is None:
            # Generate custom HTML to show on the login page if there's a
            # misconfiguration
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
        if not auth_activated:
            # auth check failed due to misconfiguration - bail
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

    @gen.coroutine
    def pre_spawn_start(self, user, spawner):
        auth_state = yield user.get_auth_state()

        if not auth_state:
            return

        token = auth_state["token"]

        spawner.environment.update({
            "PACH_PYTHON_AUTH_TOKEN": token,
        })

        spawner.lifecycle_hooks = {
            "postStart": {
                "exec": {
                    "command": ["/app/config.sh", token]
                }
            }
        }
