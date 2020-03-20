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

import yaml

KUBE_CONTEXT_INFO_PARSER = re.compile(r"^\* +[^ ]+ +([^ ]+) +([^ ]+) +([^ \n]*)\n", re.MULTILINE)
AUTH_TOKEN_PARSER = re.compile(r"  Token: ([0-9a-f]+)", re.MULTILINE)
WHO_AM_I_PARSER = re.compile(r"You are \"(.+)\"")

BASE_CONFIG = """
hub:
  image:
    name: pachyderm/jupyterhub-pachyderm-hub
    tag: "{version}"
singleuser:
  image:
    name: pachyderm/jupyterhub-pachyderm-user
    tag: "{version}"
auth:
  state:
    enabled: true
    cryptoKey: "{auth_state_crypto_key}"
  type: custom
  custom:
    className: pachyderm_authenticator.PachydermAuthenticator
    config:
      pach_auth_token: "{pach_auth_token}"
  admin:
    users:
      - "{admin_user}"
proxy:
  secretToken: "{secret_token}"
"""

PROXY_TLS_CONFIG = """
  https:
    hosts:
      - "{tls_host}"
    letsencrypt:
      contactEmail: "{tls_email}"
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
        if "the auth service is not activated" in stderr:
            return None
        else:
            print(stderr, file=sys.stderr)
            raise ApplicationError("unexpected stderr")

    return stdout

def run_version_check(cmd, *args):
    try:
        run(cmd, *args)
    except subprocess.CalledProcessError as e:
        raise ApplicationError("could not check {} version; ensure {} is installed".format(cmd, cmd)) from e
    
def print_section(section):
    print("===> {}".format(section))

def main(tls_host, tls_email, jupyterhub_version, version):
    # print versions, which in the process validates that dependencies are installed
    print_section("checking dependencies are installed")
    run_version_check("kubectl", "version")
    run_version_check("pachctl", "version")
    run_version_check("helm", "version")

    print_section("configuring helm")
    run("helm", "repo", "add", "jupyterhub", "https://jupyterhub.github.io/helm-chart/")
    run("helm", "repo", "update")

    # parse pach context
    print_section("getting pachyderm context")
    try:
        pach_context_name = run("pachctl", "config", "get", "active-context", capture_stdout=True).strip()
        pach_context_output = run("pachctl", "config", "get", "context", pach_context_name, capture_stdout=True)
        pach_context_json = json.loads(pach_context_output)
        pach_cluster = pach_context_json["cluster_name"]
        pach_auth_info = pach_context_json["auth_info"]
        pach_namespace = pach_context_json.get("namespace", "default")
    except Exception as e:
        raise ApplicationError("could not parse pach context info") from e

    # parse kubectl context
    print_section("getting kubernetes context")
    try:
        kube_context_name = run("kubectl", "config", "current-context", capture_stdout=True).strip()
        kube_context_output = run("kubectl", "config", "get-contexts", kube_context_name, capture_stdout=True)
        kube_cluster, kube_auth_info, kube_namespace = KUBE_CONTEXT_INFO_PARSER.search(kube_context_output).groups()
        kube_namespace = kube_namespace or "default"
    except Exception as e:
        raise ApplicationError("could not parse kube context info") from e

    # verify that the contexts are pointing to the same thing
    print_section("comparing pachyderm/kubernetes contexts")
    if pach_cluster != kube_cluster:
        raise ApplicationError("the active pach context's cluster name ('{}') is not the same as the current kubernetes context's cluster name ('{}')".format(pach_cluster, kube_cluster))
    if pach_auth_info != kube_auth_info:
        raise ApplicationError("the active pach context's auth info ('{}') is not the same as the current kubernetes context's auth info ('{}')".format(pach_auth_info, kube_auth_info))
    if pach_namespace != kube_namespace:
        raise ApplicationError("the active pach context's namespace ('{}') is not the same as the current kubernetes context's namespace ('{}')".format(pach_namespace, kube_namespace))

    # check auth
    print_section("checking auth")
    admin_user_stdout = run_auth_command("whoami")
    if not admin_user_stdout:
        raise ApplicationError("you must be logged into pachyderm to deploy JupyterHub")
    admin_user = WHO_AM_I_PARSER.match(admin_user_stdout).groups()[0]

    # generate pach auth token
    print_section("generating a pach auth token")    
    pach_auth_token_stdout = run_auth_command("get-auth-token")
    pach_auth_token = AUTH_TOKEN_PARSER.search(pach_auth_token_stdout).groups()[0]

    # generate the config
    print_section("generating config")
    auth_state_crypto_key = secrets.token_hex(32)
    secret_token = secrets.token_hex(32)

    config = BASE_CONFIG.format(
        version=version,
        auth_state_crypto_key=auth_state_crypto_key,
        pach_auth_token=pach_auth_token,
        admin_user=admin_user,
        secret_token=secret_token,
    )

    if tls_host:
        config += PROXY_TLS_CONFIG.format(tls_host=tls_host, tls_email=tls_email)

    with tempfile.NamedTemporaryFile() as f:
        f.write(config.encode("utf8"))
        f.flush()
        config_path = f.name

        # install JupyterHub
        print_section("installing jupyterhub")
        dry_run_output = run(
            "helm",
            "upgrade",
            "--install",
            "jhub",
            "jupyterhub/jupyterhub",
            "--version", jupyterhub_version,
            "--values", config_path,
            "--dry-run",
            capture_stdout=True,
        )

        buf = []
        buffering = False

        for line in dry_run_output.split("\n"):
            if buffering:
                if line == "NOTES:":
                    buffering = False
                elif line != "MANIFEST:": # bug in helm causing this to be printed in the wrong place
                    buf.append(line)
            else:
                if line == "HOOKS:":
                    buffering = True
                else:
                    print(line)

        manifests = list(yaml.load_all("\n".join(buf)))
        manifests.sort(key=lambda m: (m["kind"], m["metadata"]["name"]))

        with open("test.yaml", "w") as f:
            yaml.dump_all(manifests, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sets up JupyterHub on a kubernetes cluster that has Pachyderm running on it.")
    parser.add_argument("--tls-host", default="", help="If set, TLS is enabled on JupyterHub via Let's Encrypt. The value is a hostname associated with the TLS certificate.")
    parser.add_argument("--tls-email", default="", help="If set, TLS is enabled on JupyterHub via Let's Encrypt. The value is an email address associated with the TLS certificate.")
    args = parser.parse_args()

    # validate args
    if args.tls_host and not args.tls_email:
        print("TLS host specified, but no email", file=sys.stderr)
        sys.exit(1)
    if args.tls_email and not args.tls_host:
        print("TLS email specified, but no host", file=sys.stderr)
        sys.exit(1)

    # get the version
    with open("version.json", "r") as f:
        j = json.load(f)
        jupyterhub_version = j["jupyterhub"]
        version = j["jupyterhub_pachyderm"]

    main(args.tls_host, args.tls_email, jupyterhub_version, version)
