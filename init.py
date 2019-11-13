#!/usr/bin/env python3

import os
import re
import sys
import json
import secrets
import argparse
import tempfile
import subprocess

KUBE_CONTEXT_INFO_PARSER = re.compile(r"^\* +[^ ]+ +([^ ]+) +([^ ]+) +([^ \n]*)\n", re.MULTILINE)
AUTH_TOKEN_PARSER = re.compile(r"  Token: ([0-9a-f]+)", re.MULTILINE)

BASE_CONFIG = """
hub:
  image:
    name: ysimonson/jupyterhub-pachyderm-hub
    tag: 0.8.2
singleuser:
  image:
    name: ysimonson/jupyterhub-pachyderm-user
    tag: 0.8.2
auth:
  type: custom
  custom:
    className: pachyderm_authenticator.PachydermAuthenticator
    config:
      pach_auth_token: "{}"
      pach_tls_certs: "{}"
      global_password: "{}"
proxy:
  secretToken: "{}"
"""

TLS_CONFIG = """
  https:
    hosts:
      - "{}"
    letsencrypt:
      contactEmail: "{}"
"""

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

def main():
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
        return 1
    if args.tls_email and not args.tls_host:
        print("TLS email specified, but no host", file=sys.stderr)
        return 1

    # print versions, which in the process validates that dependencies are installed
    print("===> getting kubectl version")
    run("kubectl", "version")
    print("===> getting pachyderm version")
    run("pachctl", "version")

    install_tiller = False
    try:
        print("===> getting helm version")
        run("helm", "version")
    except subprocess.CalledProcessError:
        if args.install_tiller:
            # make sure helm is installed still
            run("helm", "version", "--client")
            install_tiller = True
        else:
            raise

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
        print("could not parse pach context info: {}".format(e), file=sys.stderr)
        if args.debug:
            raise
        return 2
    if args.debug:
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
        print("could not parse kube context info: {}".format(e), file=sys.stderr)
        if args.debug:
            raise
        return 2
    if args.debug:
        print("kube cluster: {}".format(kube_cluster))
        print("kube auth info: {}".format(kube_auth_info))
        print("kube namespace: {}".format(kube_namespace))

    # verify that the contexts are pointing to the same thing
    print("===> comparing pachyderm/kubernetes contexts")
    if pach_cluster != kube_cluster:
        print("the active pach context's cluster name ('{}') is not the same as the current kubernetes context's cluster name ('{}')".format(pach_cluster, kube_cluster), file=sys.stderr)
        return 3
    if pach_auth_info != kube_auth_info:
        print("the active pach context's auth info ('{}') is not the same as the current kubernetes context's auth info ('{}')".format(pach_auth_info, kube_auth_info), file=sys.stderr)
        return 3
    if pach_namespace != kube_namespace:
        print("the active pach context's namespace ('{}') is not the same as the current kubernetes context's namespace ('{}')".format(pach_namespace, kube_namespace), file=sys.stderr)
        return 3

    # install tiller
    if install_tiller:
        print("===> installing tiller")
        run("kubectl", "--namespace", "kube-system", "create", "serviceaccount", "tiller")
        run("kubectl", "create", "clusterrolebinding", "tiller", "--clusterrole", "cluster-admin", "--serviceaccount=kube-system:tiller")
        run("helm", "init", "--service-account", "tiller", "--wait")
        run("kubectl", "patch", "deployment", "tiller-deploy", "--namespace=kube-system", "--type=json", """--patch='[{"op": "add", "path": "/spec/template/spec/containers/0/command", "value": ["/tiller", "--listen=localhost:44134"]}]'""")

    # generate pach auth token
    print("===> generating a pach auth token")
    pach_auth_token = ""
    auth_token_stdout, auth_token_stderr = run("pachctl", "auth", "get-auth-token", capture_stdout=True, capture_stderr=True, raise_on_error=False)
    if auth_token_stderr:
        if auth_token_stderr.strip() != "the auth service is not activated":
            print(auth_token_stderr, file=sys.stderr)
            return 4
    else:
        pach_auth_token = AUTH_TOKEN_PARSER.search(auth_token_stdout).groups()[0]

    # get pach tls certs
    pach_tls_certs = ""
    if args.pach_tls_certs_path != "":
        with open(args.pach_tls_certs_path, "r") as f:
            pach_tls_certs = f.read()

    # generate the config
    global_password = secrets.token_hex(32)
    secret_token = secrets.token_hex(32)
    config = BASE_CONFIG.format(pach_auth_token, pach_tls_certs, global_password, secret_token)

    if args.tls_host:
        config += TLS_CONFIG.format(args.tls_host, args.tls_email)

    print("===> generating config")
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(config.encode("utf8"))
        f.close()
        config_path = f.name

    # install JupyterHub
    try:
        print("===> installing jupyterhub")
        run("helm", "upgrade", "--install", "jupyterhub", "jupyterhub/jupyterhub", "--version=0.8.2", "--values", config_path)
    finally:
        if not args.debug:
            os.unlink(config_path)

    print("===> notes")
    if not pach_auth_token:
        print("- Since Pachyderm auth doesn't appear to be enabled, JupyterHub will expect the following global password for users: {}".format(global_password))
    if args.debug:
        print("- Since debug is enabled, the config was not deleted. Because it contains sensitive data that can compromise your JupyterHub cluster, you should delete it. It's located locally at: {}".format(config_path))

    return 0

if __name__ == "__main__":
    sys.exit(main())
