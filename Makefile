# Annotation System Management Makefile
# Provides convenient commands for annotation validation, documentation, and analytics

.PHONY: help validate docs test analytics clean install dev-setup

# Default target
help: ## Show this help message
	@echo "Annotation System Management"
	@echo "============================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation and setup
install: ## Install Python dependencies
	pip install -r requirements.txt

dev-setup: install ## Set up development environment
	@echo "Setting up development environment..."
	@mkdir -p docs/annotations
	@mkdir -p .vscode
	@python scripts/annotation_dev_tools.py ide-config --ide vscode > .vscode/tasks.json
	@echo "✅ Development environment ready!"
	@echo "   - VS Code tasks configured"
	@echo "   - Documentation directory created"
	@echo "   - Run 'make validate' to check annotation consistency"

# Validation
validate: ## Validate annotation consistency
	@echo "🔍 Validating annotation consistency..."
	@python scripts/validate_annotations.py --project-root .
	@echo "✅ Validation complete!"

validate-ci: ## Validate with CI mode (exit on errors)
	@python scripts/validate_annotations.py --project-root . --ci

# Documentation
docs: ## Generate all documentation
	@echo "📚 Generating documentation..."
	@python scripts/generate_coverage_report.py --project-root . --output-dir docs/annotations
	@echo "✅ Documentation generated in docs/annotations/"

docs-serve: docs ## Generate and serve documentation locally
	@echo "🌐 Serving documentation locally..."
	@cd docs/annotations && python -m http.server 8000
	@echo "📖 Documentation available at http://localhost:8000"

# Testing
test: ## Run unit tests
	@echo "🧪 Running unit tests..."
	@python -m pytest tests/test_annotation_system.py -v

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	@python -m pytest tests/test_annotation_system.py --cov=scripts --cov-report=html --cov-report=term

test-pattern: ## Test pattern matching interactively
	@echo "🔍 Pattern Testing Tool"
	@echo "Enter text to test against regex patterns (Ctrl+C to exit):"
	@while true; do \
		read -p "Test text: " text; \
		python scripts/annotation_dev_tools.py test "$$text"; \
		echo ""; \
	done

# Analytics
analytics: ## Run full analytics suite
	@echo "📊 Running analytics suite..."
	@python scripts/annotation_analytics.py --project-root . --output docs/annotations/analytics_report.json
	@echo "✅ Analytics complete! Report saved to docs/annotations/analytics_report.json"

analytics-summary: ## Show analytics summary
	@echo "📊 Analytics Summary"
	@echo "==================="
	@python -c "import json; data=json.load(open('docs/annotations/analytics_report.json')); print(f\"Coverage: {data['coverage_metrics']['overall']['coverage_percentage']:.1f}%\"); print(f\"Total Rules: {data['coverage_metrics']['overall']['total_rules']}\"); print(f\"Total Patterns: {data['coverage_metrics']['overall']['total_patterns']}\"); print(f\"High Complexity Rules: {len(data['performance_profile']['high_complexity_rules'])}\")"

# Development tools
dev-validate: ## Validate specific file (usage: make dev-validate FILE=path/to/file)
	@python scripts/annotation_dev_tools.py validate $(FILE)

dev-diff: ## Analyze diff impact (usage: make dev-diff FILE=path OLD=old_content NEW=new_content)
	@python scripts/annotation_dev_tools.py diff $(FILE) --old $(OLD) --new $(NEW)

# Maintenance
check-dead-code: ## Check for dead regex rules
	@echo "🧹 Checking for dead code..."
	@python -c "from scripts.annotation_analytics import AnnotationAnalytics; from pathlib import Path; analytics = AnnotationAnalytics(Path('.')); analytics._load_current_data(); maintenance = analytics._analyze_maintenance_needs(); dead = maintenance['dead_code']; print(f'Dead rules: {dead}' if dead else 'No dead code found ✅')"

check-coverage: ## Check coverage by hop
	@echo "📊 Coverage by Hop"
	@echo "=================="
	@python -c "from scripts.validate_annotations import AnnotationValidator; from pathlib import Path; validator = AnnotationValidator(Path('.')); validator._parse_regex_file(); validator._parse_prompt_files(); [print(f'{hop}: {len(meta.get(\"row_map\", {}))} patterns') for hop, meta in sorted(validator.prompt_metadata.items())]"

# Performance
benchmark: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks..."
	@python -c "import time; import sys; sys.path.insert(0, '.'); from scripts.annotation_dev_tools import AnnotationDevTools; from pathlib import Path; tools = AnnotationDevTools(Path('.')); test_cases = ['The virus is extremely dangerous.', 'Health officials say it is safe.', 'Prices rose 5% this quarter.']; times = []; [times.append((lambda: (time.time(), tools.test_pattern_matching(text, False), time.time()))()[2] - (lambda: (time.time(), tools.test_pattern_matching(text, False), time.time()))()[0]) for text in test_cases]; avg = sum(times) / len(times); print(f'Average pattern matching time: {avg:.3f}s'); print('✅ Benchmark complete' if avg < 0.1 else '⚠️ Performance warning: slow pattern matching')"

# Git hooks
install-hooks: ## Install git hooks for validation
	@echo "🪝 Installing git hooks..."
	@mkdir -p .git/hooks
	@echo '#!/bin/bash\nmake validate-ci' > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo '#!/bin/bash\nmake validate-ci && make test' > .git/hooks/pre-push
	@chmod +x .git/hooks/pre-push
	@echo "✅ Git hooks installed!"

# Cleanup
clean: ## Clean generated files
	@echo "🧹 Cleaning generated files..."
	@rm -rf docs/annotations/*.md
	@rm -rf docs/annotations/*.json
	@rm -rf docs/annotations/*.db
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@echo "✅ Cleanup complete!"

clean-all: clean ## Clean all generated files including documentation
	@rm -rf docs/annotations
	@echo "✅ Full cleanup complete!"

# Quick commands for common workflows
quick-check: validate test ## Quick validation and test run
	@echo "🚀 Quick check complete!"

full-check: validate test docs analytics ## Full validation, testing, documentation, and analytics
	@echo "🎉 Full check complete!"

# Release preparation
prepare-release: clean full-check ## Prepare for release (clean, validate, test, docs, analytics)
	@echo "🚀 Release preparation complete!"
	@echo "📋 Release checklist:"
	@echo "   ✅ Annotations validated"
	@echo "   ✅ Tests passing"
	@echo "   ✅ Documentation generated"
	@echo "   ✅ Analytics completed"
	@echo ""
	@echo "📊 Final stats:"
	@make analytics-summary

# Development workflow examples
example-workflow: ## Show example development workflow
	@echo "🔄 Example Development Workflow"
	@echo "=============================="
	@echo ""
	@echo "1. Set up development environment:"
	@echo "   make dev-setup"
	@echo ""
	@echo "2. Make changes to regex rules or prompts"
	@echo ""
	@echo "3. Validate changes:"
	@echo "   make validate"
	@echo ""
	@echo "4. Test pattern matching:"
	@echo "   make test-pattern"
	@echo ""
	@echo "5. Run tests:"
	@echo "   make test"
	@echo ""
	@echo "6. Update documentation:"
	@echo "   make docs"
	@echo ""
	@echo "7. Check analytics:"
	@echo "   make analytics"
	@echo ""
	@echo "8. Quick check before commit:"
	@echo "   make quick-check"

# Advanced debugging
debug-rule: ## Debug specific regex rule (usage: make debug-rule RULE=RuleName TEXT="test text")
	@echo "🐛 Debugging rule: $(RULE)"
	@echo "Test text: $(TEXT)"
	@python -c "import re; import yaml; from pathlib import Path; data = yaml.safe_load(Path('multi_coder_analysis/regex/hop_patterns.yml').read_text()); rules = [r for hop_rules in data.values() if isinstance(hop_rules, list) for r in hop_rules if r.get('name') == '$(RULE)']; rule = rules[0] if rules else None; print(f'Rule found: {rule[\"name\"]}' if rule else 'Rule not found'); pattern = rule.get('pattern', '') if rule else ''; veto = rule.get('veto_pattern', '') if rule else ''; print(f'Pattern match: {bool(re.search(pattern, \"$(TEXT)\", re.IGNORECASE))}' if pattern else 'No pattern'); print(f'Veto match: {bool(re.search(veto, \"$(TEXT)\", re.IGNORECASE))}' if veto else 'No veto pattern')"

# Watch mode for development
watch: ## Watch files and auto-validate on changes (requires inotify-tools)
	@echo "👀 Watching for changes... (Ctrl+C to stop)"
	@while inotifywait -e modify multi_coder_analysis/regex/hop_patterns.yml multi_coder_analysis/prompts/hop_Q*.txt 2>/dev/null; do \
		echo "🔄 Files changed, running validation..."; \
		make validate || true; \
		echo ""; \
	done

# Help for specific tools
help-validate: ## Show detailed help for validation
	@python scripts/validate_annotations.py --help

help-docs: ## Show detailed help for documentation generation
	@python scripts/generate_coverage_report.py --help

help-dev-tools: ## Show detailed help for development tools
	@python scripts/annotation_dev_tools.py --help

help-analytics: ## Show detailed help for analytics
	@python scripts/annotation_analytics.py --help 