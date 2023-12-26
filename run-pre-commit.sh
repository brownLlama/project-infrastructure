poetry lock
poetry install
poetry update
poetry add --group dev 'black'
poetry add --group dev tomli
poetry add tomli
pre-commit install
pre-commit autoupdate
pre-commit run --all-files
