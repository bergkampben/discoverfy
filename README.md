# eecs-441-project

_Setting up your environment_

```
deactivate  # Make sure no old virtual env is active
python3 -m venv env
source env/bin/activate
pip install --upgrade pip setuptools wheel
pip install nodeenv
nodeenv --python-virtualenv
deactivate
source env/bin/activate
```

_Install back end and front end_

```
pip install -e .
npm install .
```