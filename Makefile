.PHONY: test-e2e docker-build-local

venv:
	virtualenv -p python3.7 venv
	. venv/bin/activate && pip3 install -r etc/test_requirements.txt

test-e2e: venv
	. venv/bin/activate && python3 ./etc/test_e2e.py \
		"$(shell minikube service proxy-public --url | head -n 1)" \
        "github:admin" "$(shell pachctl auth get-otp)" --debug

docker-build-local:
	cd images/hub && VERSION=local make docker-build
	cd images/user && VERSION=local make docker-build
