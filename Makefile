env:
	# for fabfile
	test -e .venv || python3 -m venv .venv
	.venv/bin/pip install -r fabfile/requirements.txt
