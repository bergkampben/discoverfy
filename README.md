# eecs-441-project

*Setting up your environment*

`deactivate  # Make sure no old virtual env is active`
`python3 -m venv env`
`source env/bin/activate`
`pip install --upgrade pip setuptools wheel`
`pip install nodeenv`
`nodeenv --python-virtualenv`
`deactivate`
`source env/bin/activate`

*Install back end and front end*

`pip install -e .`
`npm install .`
