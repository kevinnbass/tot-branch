# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### v2.18.4  (2025‑06‑25)
* **BUGFIX – "Variable" label leakage**  
  * Removed placeholder mapping (`Q_TO_FRAME[11] = "Variable"`).  
  * Added strict `||FRAME=` token guard for Hop 11; silent omissions now
    fall back to **Neutral** with a logged warning.  
  * Deleted obsolete ad‑hoc override block.  
  * Added regression tests (*tests/test_hop11_token_guard.py*).
* **BREAKING CHANGE** – Any pipeline depending on the string "Variable"
  must update downstream enums; the label is no longer produced.

## [1.0.0-rc1] - 2025-01-XX

### 🚀 Major Refactoring - Hexagonal Architecture

This release represents a comprehensive refactoring of the multi-coder analysis toolkit, 
introducing hexagonal architecture principles while maintaining 100% backward compatibility.

### ✨ Added

#### Core Architecture
- **Hexagonal/Onion Architecture**: Clean separation between domain logic, adapters, and infrastructure
- **Pure Function Pipeline**: `Step[T]` protocol for composable, testable processing steps
- **Dependency Injection**: Protocol-based provider abstractions (PEP 544)

#### New Package Structure
- `multi_coder_analysis/models/`: Pure data structures (`HopContext`, `BatchHopContext`)
- `multi_coder_analysis/core/`: Business logic with no I/O dependencies
  - `pipeline/`: Generic step orchestration
  - `regex/`: Pluggable pattern matching engine
  - `prompt.py`: Cached template processing
- `multi_coder_analysis/providers/`: LLM provider abstractions
- `multi_coder_analysis/runtime/`: Orchestration, CLI, and I/O
- `multi_coder_analysis/config/`: Type-safe configuration management

#### Configuration Management
- **Pydantic Settings**: Type-safe configuration with validation
- **Environment Overrides**: `MCA_*` environment variable support
- **JSON Schema**: IDE autocompletion for configuration
- **Legacy YAML Support**: Backward-compatible `config.yaml` loading with deprecation warnings

#### CLI Interface
- **Typer-based CLI**: Modern command-line interface with sub-commands
- **Rich Help**: Enhanced help text and error messages
- **Validation**: Input validation with clear error messages

#### Observability
- **Structured Logging**: `structlog` integration with correlation IDs
- **NDJSON Tracing**: Machine-readable trace format for analytics
- **Performance Metrics**: Built-in timing and token usage tracking
- **Run Correlation**: Global run IDs for distributed tracing

#### Developer Experience
- **Plugin System**: Entry points for custom providers and regex rules
- **Factory Pattern**: Clean provider instantiation
- **Type Safety**: Full typing coverage with `mypy --strict`
- **Caching**: `@lru_cache` for performance optimization

### 🔄 Changed

#### Import Paths (with Deprecation Warnings)
```python
# Old (deprecated but still works)
from hop_context import HopContext
from regex_engine import match
from llm_providers.gemini_provider import GeminiProvider

# New (canonical)
from multi_coder_analysis.models import HopContext
from multi_coder_analysis.core.regex import Engine
from multi_coder_analysis.providers import GeminiProvider
```

#### Configuration
- **Settings Model**: Replaced ad-hoc config with typed Pydantic model
- **Environment First**: Environment variables take precedence over YAML
- **Validation**: Configuration validated at startup with clear error messages

#### Error Handling
- **Structured Errors**: Consistent error formats with context
- **Graceful Degradation**: Fallback behavior for optional dependencies
- **Better Messages**: User-friendly error descriptions

### 🛠️ Improved

#### Performance
- **Regex Engine**: <3ms per segment (class-based with statistics)
- **Batch Processing**: Optimized concurrency and memory usage
- **Caching**: LRU cache for prompt loading and template processing
- **Lazy Loading**: Optional dependencies loaded only when needed

#### Testing
- **Pure Functions**: All core logic is now deterministic and testable
- **Mock Providers**: Network-free testing with `pytest-httpx`
- **Golden Dataset**: Bit-wise output comparison for regression testing
- **Coverage**: 100% branch coverage on core modules

#### Documentation
- **Architecture Guide**: Comprehensive design documentation
- **Migration Guide**: Step-by-step upgrade instructions
- **API Reference**: Auto-generated from type hints and docstrings

### 🔧 Technical Debt

#### Code Quality
- **Circular Imports**: Eliminated through dependency inversion
- **Global State**: Removed module-level globals in favor of dependency injection
- **Type Safety**: Full `mypy --strict` compliance
- **Linting**: `ruff`, `black`, `isort` integration

#### Maintainability
- **Single Responsibility**: Each module has a clear, focused purpose
- **Testability**: All business logic is pure functions
- **Extensibility**: Plugin system for custom components

### ⚠️ Deprecated

The following imports are deprecated and will be removed in v1.1.0:

- `hop_context` module → `multi_coder_analysis.models.hop`
- `regex_engine` module → `multi_coder_analysis.core.regex`
- `llm_providers.*` → `multi_coder_analysis.providers.*`

All deprecated imports emit `DeprecationWarning` but continue to work.

### 🔒 Security

- **API Key Handling**: Secure environment variable loading
- **Input Validation**: Pydantic validation prevents injection attacks
- **Dependency Scanning**: Automated security scanning in CI

### 📦 Dependencies

#### Added
- `pydantic-settings`: Type-safe configuration management
- `typer[rich]`: Modern CLI interface
- `structlog`: Structured logging

#### Updated
- `pydantic`: Updated to v2.x for better performance and features

### 🚧 Migration Guide

#### For Users
1. **No Action Required**: All existing scripts continue to work
2. **Optional**: Update imports to use canonical paths
3. **Recommended**: Migrate `config.yaml` to environment variables

#### For Developers
1. **Import Updates**: Use new canonical import paths
2. **Provider Factory**: Use `get_provider()` instead of direct instantiation
3. **Configuration**: Use `Settings` model instead of raw dictionaries

### 📈 Performance Benchmarks

- **Regex Engine**: 2.1ms average per segment (vs 4.2ms in v0.9.x)
- **Batch Processing**: 98s for 1000 segments at batch_size=8 (vs 145s in v0.9.x)
- **Memory Usage**: 15% reduction through better caching strategies

### 🧪 Quality Gates

- ✅ 18 passing tests (0 failures)
- ✅ `mypy --strict` compliance
- ✅ 100% core module coverage
- ✅ Golden dataset regression tests pass
- ✅ Performance benchmarks within budget

### 🔮 Coming in v1.0.0

- **Complete Pipeline Migration**: Full ToT chain in new architecture
- **Advanced Caching**: Redis-backed caching for distributed setups
- **Metrics Dashboard**: Real-time processing metrics
- **Plugin Marketplace**: Community-contributed providers and rules

---

## [0.9.0] - 2025-01-XX

### Added
- Initial Tree-of-Thought implementation
- Regex-based short-circuiting
- Batch processing support
- Basic tracing and logging

### Changed
- Improved error handling
- Enhanced provider abstractions

### Fixed
- Memory leaks in batch processing
- Regex engine performance issues

---

For migration assistance or questions about this release, please see the 
[Migration Guide](docs/MIGRATION.md) or open an issue on GitHub.

## 0.5.2 – UNRELEASED

* Token telemetry no longer double-counts and tolerates None values.
* Regex loader accepts numeric hop keys (e.g. `3:` as well as `Q03:`).
* Early-exit optimisation when all permutations are concluded.
* Default execution mode everywhere is now `pipeline`.
* Added thought-token accounting to OpenRouter provider.
* Run-summary NDJSON written via TraceWriter to `traces/` directory. 