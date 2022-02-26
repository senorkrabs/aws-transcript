python -m pip install pipenv
SET PIPENV_VENV_IN_PROJECT="enabled"
pipenv install
pipenv run pyinstaller aws-transcript.py --onefile
pipenv --rm
rmdir /s /q build
REM rmdir /s /q dist