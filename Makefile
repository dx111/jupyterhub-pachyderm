.PHONY: test

venv:
	virtualenv -p python3.7 venv
	. venv/bin/activate && pip3 install -r etc/test_requirements.txt

test: venv
	. venv/bin/activate && python3 ./etc/test.py \
		"$(shell minikube service proxy-public --url | head -n 1)" \
        "" "$(shell pachctl auth get-otp)" --debug
