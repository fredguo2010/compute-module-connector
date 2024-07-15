# simple makefile to simplify repetitive tasks under posix

black:
# auto-formatter for .py files
		black .

cython-lint:
# manual-formatter for .pyx files
		cython-lint .

ruff:
		ruff check . --fix

mypy:
		mypy .
