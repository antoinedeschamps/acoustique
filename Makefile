install:
	pip install -r requirements.txt

black:
	black ./

mypy:
	mypy ./
