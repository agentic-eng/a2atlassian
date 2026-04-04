.PHONY: lint fix test check coverage-diff security-audit bootstrap test-fixtures test-integration record-fixtures

lint:
	agent-harness lint

fix:
	agent-harness fix

test:
	uv run pytest tests/ -v

coverage-diff:
	@uv run diff-cover coverage.xml --compare-branch=origin/main --fail-under=95

security-audit:
	agent-harness security-audit

check: lint test coverage-diff security-audit

test-fixtures:
	uv run pytest tests/fixture_tests/ -v --no-cov

test-integration:
	uv run pytest tests/integration/ -v --no-cov --integration

record-fixtures:
	uv run python scripts/record_fixtures.py

bootstrap: ## First-time setup after clone
	uv sync
	agent-harness init --apply
	@if command -v prek >/dev/null; then prek install; \
	elif command -v pre-commit >/dev/null; then pre-commit install; \
	else echo "Install prek (brew install prek) or pre-commit for git hooks"; fi
	@echo "Done. Run 'make check' to verify."
