.PHONY: test-e2e docker-build-local deploy-native-local deploy-local dev-jupyterhub

venv:
	virtualenv -p python3.7 venv
	. venv/bin/activate && pip3 install -r etc/test_requirements.txt

test-e2e: venv
	. venv/bin/activate && python3 ./etc/test_e2e.py \
		"$(shell minikube service proxy-public --url | head -n 1)" \
        "" "$(shell pachctl auth get-otp)" --debug

docker-build-local:
	cd images/hub && VERSION=local make docker-build
	cd images/user && VERSION=local make docker-build

# NOTE: requires pachctl >= 1.11
deploy-native-local:
	$(GOPATH)/bin/pachctl deploy jupyterhub \
        --user-image "pachyderm/jupyterhub-pachyderm-user:local" \
        --hub-image "pachyderm/jupyterhub-pachyderm-hub:local"

deploy-local:
	python3.7 init.py --use-version=local

jupyterhub-dev:
	. venv/bin/activate && pip install jupyterhub
	sudo npm install -g configurable-http-proxy
	. venv/bin/activate && jupyterhub --config=etc/config/dev_jupyterhub.py
