
#!/bin/bash
cd ..
python3 setup.py sdist bdist_wheel && \
python3 -m twine upload --disable-progress-bar --verbose --skip-existing --repository-url http://pip.whitemoonlabs.com/ -u pyadmin -p Passw0rd1! dist/*
cd setup