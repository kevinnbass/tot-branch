# Architecture Overview

## Hexagonal Architecture (Onion Model)

The `multi_coder_analysis` package follows hexagonal/onion architecture principles:

```
┌─────────────────────────────────────────────────────────────┐
│                        Runtime Layer                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Providers Layer                    │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │                Core Layer                   │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │            Models Layer             │   │   │   │
│  │  │  │                                     │   │   │   │
│  │  │  │  • HopContext                       │   │   │   │
│  │  │  │  • BatchHopContext                  │   │   │   │
│  │  │  │  • Pure data structures             │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  │                                             │   │   │
│  │  │  • Pipeline orchestration                   │   │   │
│  │  │  • Regex engine                             │   │   │
│  │  │  • Prompt processing                        │   │   │
│  │  │  • Pure business logic                      │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │  • LLM providers (Gemini, OpenRouter)              │   │
│  │  • Protocol-based abstractions                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  • CLI interface                                           │
│  • File I/O                                                │
│  • Configuration loading                                   │
│  • Tracing and logging                                     │
└─────────────────────────────────────────────────────────────┘
```

## Package Structure

### `/models` - Pure Data Structures
- `hop.py`: `HopContext`, `BatchHopContext` dataclasses
- No dependencies on frameworks or I/O
- Typed aliases for complex data structures

### `/core` - Business Logic
- `pipeline/`: Generic `Step[T]` protocol and ToT implementation
- `regex/`: Pattern matching engine with plugin support
- `prompt.py`: Template processing with caching
- Pure functions with no side effects

### `/providers` - External Service Adapters
- `base.py`: `ProviderProtocol` (PEP 544)
- `gemini.py`, `openrouter.py`: LLM provider implementations
- Factory pattern for provider instantiation

### `/runtime` - Orchestration & I/O
- `cli.py`: Typer-based command-line interface
- `tot_runner.py`: Main execution orchestrator
- `tracing.py`: Structured logging and NDJSON tracing

### `/config` - Configuration Management
- `settings.py`: Pydantic Settings with environment overrides
- `run_config.py`: Runtime configuration model
- JSON schema generation for IDE support

## Key Design Principles

### 1. Dependency Inversion
- Core logic depends only on abstractions (protocols)
- Infrastructure adapts to core interfaces
- No framework dependencies in business logic

### 2. Pure Function Pipeline
- Each `Step[T]` is a pure function: `T → T`
- Deterministic, testable, composable
- No hidden global state

### 3. Configuration as Code
- Pydantic models with validation
- Environment variable overrides
- Type-safe configuration throughout

### 4. Observability First
- Structured logging with correlation IDs
- NDJSON trace format for analytics
- Performance metrics and debugging

## Migration Strategy

The refactoring maintains 100% backward compatibility through:

1. **Deprecation Shims**: Old import paths emit warnings but still work
2. **Feature Flags**: New pipeline can be enabled via `phase="pipeline"`
3. **Gradual Migration**: Core components moved while preserving APIs

## Testing Strategy

- **Unit Tests**: 100% coverage on `/core`, 90% project-wide
- **Integration Tests**: Provider mocking with `pytest-httpx`
- **Golden Dataset**: Bit-wise output comparison for regression testing
- **Performance Tests**: <3ms regex engine, <125s batch processing

## Future Extensions

- **Plugin System**: Entry points for custom providers and rules
- **Distributed Processing**: Batch processing across multiple nodes
- **Real-time Processing**: Stream-based ToT for live data
- **ML Integration**: Embedding-based similarity for rule discovery 