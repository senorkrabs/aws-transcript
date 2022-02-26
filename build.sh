python -m pip install pipenv
export PIPENV_VENV_IN_PROJECT="enabled"
pipenv install
pipenv run pyinstaller aws-transcript.py --onefile
cp dist/aws-transcript .
pipenv --rm
rm -r build
rm -r dist