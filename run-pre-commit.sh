poetry lock
poetry install
poetry update
poetry add --dev 'black'
poetry add --dev tomli
poetry add tomli
pre-commit install
pre-commit autoupdate
pre-commit run --all-files
