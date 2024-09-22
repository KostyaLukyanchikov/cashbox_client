src := src

black := poetry run black
ruff := poetry run ruff
pyup_dirs := poetry run pyup_dirs
mypy := poetry run mypy
bandit := poetry run bandit

all: format lint

format:
	@echo "Форматирование кода..."
	$(black) $(src)
	$(ruff) check $(src) --fix
	$(pyup_dirs) --py311-plus --recursive $(src)

lint:
	@echo "Статический анализ кода..."
	$(mypy) $(src) --show-absolute-path --follow-imports=silent
	$(bandit) $(src)

help:
	@echo "Использование:"
	@echo "    make help            - отображает эту справку"
	@echo "    make                 - форматирует и линтует"
	@echo "    make lint            - выполняет все проверки линтинга"
	@echo "    make format          - форматирует код с использованием"
