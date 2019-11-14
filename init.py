#!/usr/bin/env python3

import os
import re
import sys
import json
import secrets
import argparse
import tempfile
import traceback
import subprocess

KUBE_CONTEXT_INFO_PARSER = re.compile(r"^\* +[^ ]+ +([^ ]+) +([^ ]+) +([^ \n]*)\n", re.MULTILINE)
AUTH_TOKEN_PARSER = re.compile(r"  Token: ([0-9a-f]+)", re.MULTILINE)
WHO_AM_I_PARSER = re.compile(r"You are \"(.+)\"")

BASE_CONFIG = """
hub:
  image:
    name: ysimonson/jupyterhub-pachyderm-hub
    tag: 0.8.2
singleuser:
  image:
    name: ysimonson/jupyterhub-pachyderm-user
    tag: 0.8.2
"""

AUTH_BASE_CONFIG = """
auth:
  state:
    enabled: true
    cryptoKey: "{}"
  type: custom
  custom:
    className: pachyderm_authenticator.PachydermAuthenticator
    config:
      pach_auth_token: "{}"
      pach_tls_certs: "{}"
      global_password: "{}"
"""

AUTH_ADMIN_CONFIG = """
  admin:
    users:
      - "{}"
"""

PROXY_BASE_CONFIG = """
proxy:
  secretToken: "{}"
"""

PROXY_TLS_CONFIG = """
  https:
    hosts:
      - "{}"
    letsencrypt:
      contactEmail: "{}"
"""

class ApplicationError(Exception):
    pass

def run(cmd, *args, capture_stdout=False, capture_stderr=False, raise_on_error=True):
    proc = subprocess.run(
        [cmd, *args],
        stdout=subprocess.PIPE if capture_stdout else None,
        stderr=subprocess.PIPE if capture_stderr else None,
    )

    stdout = proc.stdout.decode("utf8") if proc.stdout else None
    stderr = proc.stderr.decode("utf8") if proc.stderr else None

    if raise_on_error:
        try:
            proc.check_returncode()
        except:
            print(stdout)
            print(stderr, file=sys.stderr)
            raise

    if capture_stdout and capture_stderr:
        return (stdout, stderr)
    elif capture_stdout:
        return stdout
    elif capture_stderr:
        return stderr

def run_auth_command(*args):
    stdout, stderr = run("pachctl", "auth", *args, capture_stdout=True, capture_stderr=True, raise_on_error=False)

    if stderr:
        print(stderr, file=sys.stderr)
        if "the auth service is not activated" in stderr:
            return None
        else:
            raise Exception("unexpected stderr")

    return stdout

def run_version_check(cmd, *args):
    try:
        run(cmd, *args)
    except subprocess.CalledProcessError as e:
        raise ApplicationError("could not check {} version; ensure {} is installed".format(cmd, cmd)) from e

def main(debug, pach_tls_certs, tls_host, tls_email, install_tiller):
    # print versions, which in the process validates that dependencies are installed
    print("===> checking dependencies are installed")
    run_version_check("kubectl", "version")
    run_version_check("pachctl", "version")

    try:
        run_version_check("helm", "version")
        # no need to install tiller because it's already installed
        install_tiller = False
    except ApplicationError:
        if not install_tiller:
            raise
    if install_tiller:
        # make sure helm is installed still
        run_version_check("helm", "version", "--client")

    # parse pach context
    try:
        print("===> getting pachyderm context")
        pach_context_name = run("pachctl", "config", "get", "active-context", capture_stdout=True).strip()
        pach_context_output = run("pachctl", "config", "get", "context", pach_context_name, capture_stdout=True)
        pach_context_json = json.loads(pach_context_output)
        pach_cluster = pach_context_json["cluster_name"]
        pach_auth_info = pach_context_json["auth_info"]
        pach_namespace = pach_context_json["namespace"] or "default"
    except Exception as e:
        raise ApplicationError("could not parse pach context info") from e
    if debug:
        print("pach cluster: {}".format(pach_cluster))
        print("pach auth info: {}".format(pach_auth_info))
        print("pach namespace: {}".format(pach_namespace))

    # parse kubectl context
    try:
        print("===> getting kubernetes context")
        kube_context_name = run("kubectl", "config", "current-context", capture_stdout=True).strip()
        kube_context_output = run("kubectl", "config", "get-contexts", kube_context_name, capture_stdout=True)
        kube_cluster, kube_auth_info, kube_namespace = KUBE_CONTEXT_INFO_PARSER.search(kube_context_output).groups()
        kube_namespace = kube_namespace or "default"
    except Exception as e:
        raise ApplicationError("could not parse kube context info") from e
    if debug:
        print("kube cluster: {}".format(kube_cluster))
        print("kube auth info: {}".format(kube_auth_info))
        print("kube namespace: {}".format(kube_namespace))

    # verify that the contexts are pointing to the same thing
    print("===> comparing pachyderm/kubernetes contexts")
    if pach_cluster != kube_cluster:
        raise ApplicationError("the active pach context's cluster name ('{}') is not the same as the current kubernetes context's cluster name ('{}')".format(pach_cluster, kube_cluster))
    if pach_auth_info != kube_auth_info:
        raise ApplicationError("the active pach context's auth info ('{}') is not the same as the current kubernetes context's auth info ('{}')".format(pach_auth_info, kube_auth_info))
    if pach_namespace != kube_namespace:
        raise ApplicationError("the active pach context's namespace ('{}') is not the same as the current kubernetes context's namespace ('{}')".format(pach_namespace, kube_namespace))

    # generate pach auth token
    print("===> generating a pach auth token")
    admin_user_stdout = run_auth_command("whoami")
    admin_user = WHO_AM_I_PARSER.match(admin_user_stdout).groups()[0] if admin_user_stdout else None
    pach_auth_token_stdout = run_auth_command("get-auth-token")
    pach_auth_token = AUTH_TOKEN_PARSER.search(pach_auth_token_stdout).groups()[0] if pach_auth_token_stdout else ""
    assert (admin_user and pach_auth_token) or (not admin_user and not pach_auth_token)

    # generate the config
    auth_state_crypto_key = secrets.token_hex(32)
    global_password = secrets.token_hex(32)
    secret_token = secrets.token_hex(32)

    config = BASE_CONFIG
    config += AUTH_BASE_CONFIG.format(auth_state_crypto_key, pach_auth_token, pach_tls_certs, global_password)
    if admin_user:
        config += AUTH_ADMIN_CONFIG.format(admin_user)
    config += PROXY_BASE_CONFIG.format(secret_token)
    if tls_host:
        config += PROXY_TLS_CONFIG.format(tls_host, tls_email)

    print("===> generating config")
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(config.encode("utf8"))
        f.close()
        config_path = f.name

    # install tiller
    if install_tiller:
        print("===> installing tiller")
        try:
            run("kubectl", "--namespace", "kube-system", "create", "serviceaccount", "tiller")
            run("kubectl", "create", "clusterrolebinding", "tiller", "--clusterrole", "cluster-admin", "--serviceaccount=kube-system:tiller")
            run("helm", "init", "--service-account", "tiller", "--wait")
            run("kubectl", "patch", "deployment", "tiller-deploy", "--namespace=kube-system", "--type=json", """--patch='[{"op": "add", "path": "/spec/template/spec/containers/0/command", "value": ["/tiller", "--listen=localhost:44134"]}]'""")
        except subprocess.CalledProcessError as e:
            raise ApplicationError("failed to install tiller") from e

    # install JupyterHub
    try:
        print("===> installing jupyterhub")
        run("helm", "upgrade", "--install", "jupyterhub", "jupyterhub/jupyterhub", "--version=0.8.2", "--values", config_path)
    finally:
        if not debug:
            os.unlink(config_path)

    # print notes (if any)
    print("===> notes")
    if not admin_user:
        print("- Since Pachyderm auth doesn't appear to be enabled, JupyterHub will expect the following global password for users: {}".format(global_password))
    else:
        print("- Since Pachyderm auth is enabled, the logged in pachctl user ('{}') has been set as the JupyterHub admin".format(admin_user))
    if debug:
        print("- Since debug is enabled, the config was not deleted. Because it contains sensitive data that can compromise your JupyterHub cluster, you should delete it. It's located locally at: {}".format(config_path))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sets up JupyterHub on a kubernetes cluster that has Pachyderm running on it.")
    parser.add_argument("--debug", default=False, action="store_true", help="Debug mode")
    parser.add_argument("--pach-tls-certs-path", default="", help="Path to a root certs file for Pachyderm TLS.")
    parser.add_argument("--tls-host", default="", help="If set, TLS is enabled on JupyterHub via Let's Encrypt. The value is a hostname associated with the TLS certificate.")
    parser.add_argument("--tls-email", default="", help="If set, TLS is enabled on JupyterHub via Let's Encrypt. The value is an email address associated with the TLS certificate.")
    parser.add_argument("--install-tiller", default=False, action="store_true", help="Installs tiller if it's not installed already.")
    args = parser.parse_args()

    # validate args
    if args.tls_host and not args.tls_email:
        print("TLS host specified, but no email", file=sys.stderr)
        sys.exit(1)
    if args.tls_email and not args.tls_host:
        print("TLS email specified, but no host", file=sys.stderr)
        sys.exit(1)

    # get pach tls certs
    pach_tls_certs = ""
    if args.pach_tls_certs_path != "":
        try:
            with open(args.pach_tls_certs_path, "r") as f:
                pach_tls_certs = f.read()
        except Exception as e:
            print("failed to read pach TLS certs at '{}': {}".format(args.pach_tls_certs_path, e), file=sys.stderr)
            sys.exit(1)

    try:
        main(args.debug, pach_tls_certs, args.tls_host, args.tls_email, args.install_tiller)
    except ApplicationError as e:
        print("error: {}".format(e), file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        sys.exit(2)
