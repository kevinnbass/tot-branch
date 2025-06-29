# System Architecture

## Overview

The Tree-of-Thought Multi-Coder Analysis system is designed as a modular, scalable, and maintainable framework for complex text analysis using hybrid approaches combining rule-based regex patterns and large language models.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  CLI Interface  │  Configuration  │  Logging & Monitoring       │
├─────────────────────────────────────────────────────────────────┤
│                         Core Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  Pipeline Engine │  Consensus Logic │  Error Handling           │
├─────────────────────────────────────────────────────────────────┤
│                      Processing Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  Regex Engine   │  LLM Providers   │  Validation               │
├─────────────────────────────────────────────────────────────────┤
│                        Data Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  Input/Output   │  Tracing        │  Analytics Database        │
└─────────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. **Separation of Concerns**
- Each module has a single, well-defined responsibility
- Clear interfaces between components
- Minimal coupling between layers

### 2. **Configuration-Driven**
- Behavior controlled through configuration files
- Environment variable overrides
- Runtime parameter adjustment

### 3. **Error Resilience**
- Comprehensive error handling with custom exception hierarchy
- Graceful degradation when components fail
- Retry mechanisms for transient failures

### 4. **Observability**
- Detailed logging at all levels
- Performance metrics collection
- Execution tracing for debugging

### 5. **Extensibility**
- Plugin architecture for new LLM providers
- Configurable pipeline stages
- Custom regex rule sets

## Component Details

### Application Layer

#### CLI Interface (`runtime/cli.py`)
```python
class CLIInterface:
    """Command-line interface with argument parsing and validation."""
    
    def parse_arguments() -> argparse.Namespace
    def validate_arguments(args: argparse.Namespace) -> None
    def run_application(args: argparse.Namespace) -> int
```

**Responsibilities:**
- Command-line argument parsing
- Input validation
- Application lifecycle management
- Error reporting to user

#### Configuration Management (`config/manager.py`)
```python
@dataclass
class ConfigManager:
    """Centralized configuration from multiple sources."""
    
    settings: Settings
    _config_sources: list[str]
    _raw_config: Dict[str, Any]
    
    @classmethod
    def from_sources(...) -> ConfigManager
    def get(key: str, default: Any) -> Any
    def update(**kwargs) -> None
```

**Configuration Sources (Priority Order):**
1. Command-line arguments (highest)
2. Environment variables (`MCA_*`)
3. YAML configuration files
4. Default settings (lowest)

### Core Layer

#### Pipeline Engine (`core/pipeline/tot.py`)
```python
class ToTPipeline:
    """12-hop Tree-of-Thought reasoning pipeline."""
    
    def __init__(config: ConfigManager, providers: List[LLMProvider])
    def execute(segments: List[Segment]) -> List[Result]
    def execute_hop(hop: int, segments: List[Segment]) -> List[HopResult]
```

**Features:**
- Configurable hop execution order
- Batch processing with configurable sizes  
- Parallel processing support
- Progress tracking and interruption handling

#### Consensus System (`core/consensus.py`)
```python
class ConsensusEngine:
    """Multiple voting strategies for robust results."""
    
    def majority_vote(results: List[HopResult]) -> ConsensusResult
    def weighted_consensus(results: List[HopResult], weights: Dict[str, float]) -> ConsensusResult
    def confidence_based(results: List[HopResult], threshold: float) -> ConsensusResult
```

#### Error Handling (`core/exceptions.py`)
```python
class AnalysisError(Exception):
    """Base exception with severity levels and structured details."""
    
    severity: ErrorSeverity
    error_code: Optional[str]
    details: Dict[str, Any]

@error_handler(logger=logger, reraise=True)
def critical_operation():
    """Decorator-based error handling."""
```

**Exception Hierarchy:**
- `AnalysisError` (base)
  - `ConfigurationError`
  - `LLMProviderError` 
  - `RegexEngineError`
  - `PipelineError`
  - `ValidationError`
  - `RetryableError`

### Processing Layer

#### Regex Engine (`core/regex/engine.py`)
```python
class Engine:
    """Stateless regex matching with configurable rule sets."""
    
    def __init__(rules: Dict[int, List[PatternInfo]], ...)
    def match(ctx: HopContext) -> Optional[Answer]
    def get_rule_stats() -> Dict[str, Counter]
```

**Features:**
- Compiled pattern caching
- Performance statistics
- Shadow mode (evaluation without short-circuiting)
- Thread-safe operation

#### LLM Providers (`providers/`)
```python
class LLMProvider(ABC):
    """Abstract base for LLM providers."""
    
    @abstractmethod
    def generate(prompt: str, **kwargs) -> LLMResponse
    
    @abstractmethod  
    def batch_generate(prompts: List[str], **kwargs) -> List[LLMResponse]
```

**Implementations:**
- `GeminiProvider`: Google Gemini API
- `OpenRouterProvider`: OpenRouter API gateway
- Extensible for additional providers

### Data Layer

#### Input/Output (`utils/`)
```python
class DataValidator:
    """Input validation and sanitization."""
    
    def validate_csv(file_path: Path) -> ValidationResult
    def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]

class OutputFormatter:
    """Consistent output formatting."""
    
    def format_results(results: List[Result], format: str) -> str
    def generate_report(results: List[Result], template: str) -> str
```

#### Tracing System (`runtime/tracing.py`)
```python
class TraceWriter:
    """Execution trace recording for debugging."""
    
    def __init__(trace_dir: Path)
    def record_hop(hop_result: HopResult) -> None
    def finalize() -> Path
```

**Trace Information:**
- Input/output for each hop
- Timing and performance data
- Error conditions and recovery
- Decision rationale

## Data Flow

### 1. **Initialization Phase**
```
CLI Args → ConfigManager → Validation → Logger Setup → Provider Init
```

### 2. **Processing Phase**
```
Input CSV → Validation → Segments → ToT Pipeline → Results → Output
```

### 3. **Per-Hop Processing**
```
Segment → Regex Engine → [Match?] → LLM Provider → Consensus → Result
                     ↓
                   [No Match] ───────────────────────────┘
```

### 4. **Error Handling Flow**
```
Exception → Error Reporter → Log + Context → [Retry?] → Continue/Fail
```

## Configuration Schema

```yaml
# Core execution settings
provider: "gemini"                    # LLM provider name
model: "models/gemini-2.5-flash"     # Model identifier
batch_size: 10                       # Batch size for LLM calls
concurrency: 4                       # Thread pool size

# Feature flags
enable_regex: true                    # Enable regex short-circuiting
regex_mode: "live"                    # live|shadow|off
shuffle_batches: false               # Randomize batch order
shuffle_segments: false              # Randomize within batches

# Observability
log_level: "INFO"                    # Log verbosity
json_logs: false                     # Structured JSON logging
archive_enable: true                 # Archive completed results

# Provider-specific settings
google_api_key: "${GOOGLE_API_KEY}"  # API key from environment
openrouter_api_key: "${OPENROUTER_API_KEY}"

# Performance tuning
timeout: 30                          # Request timeout seconds
max_retries: 3                       # Retry attempts
backoff_factor: 1.5                  # Exponential backoff
```

## Extension Points

### 1. **Custom LLM Providers**
```python
class CustomProvider(LLMProvider):
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implementation for new provider
        pass
```

### 2. **Pipeline Stages**
```python
class CustomStage(PipelineStage):
    def process(self, segments: List[Segment]) -> List[Segment]:
        # Custom processing logic
        pass
```

### 3. **Output Formatters**
```python
class CustomFormatter(OutputFormatter):
    def format(self, results: List[Result]) -> str:
        # Custom output format
        pass
```

## Performance Considerations

### 1. **Concurrency Model**
- **Thread-based**: For I/O-bound LLM API calls
- **Process-based**: For CPU-intensive regex operations (future)
- **Async/Await**: For high-concurrency scenarios (future)

### 2. **Memory Management**
- Streaming processing for large datasets
- Configurable batch sizes
- Garbage collection hints

### 3. **Caching Strategy**
- Compiled regex pattern cache
- LLM response cache (configurable)
- Configuration cache

### 4. **Optimization Opportunities**
- Pre-compilation of all regex patterns
- Connection pooling for LLM providers
- Result streaming to disk

## Security Considerations

### 1. **API Key Management**
- Environment variable injection
- No keys in configuration files
- Secure credential storage

### 2. **Input Validation**  
- CSV structure validation
- Content sanitization
- Size limits

### 3. **Output Security**
- Path traversal prevention
- File permission settings
- Sensitive data redaction

## Testing Strategy

### 1. **Unit Tests**
- Individual component testing
- Mock LLM provider responses
- Configuration validation

### 2. **Integration Tests**
- End-to-end pipeline testing
- Provider integration
- Error handling scenarios

### 3. **Performance Tests**
- Load testing with large datasets
- Concurrency stress testing
- Memory usage profiling

## Deployment Considerations

### 1. **Environment Setup**
- Python 3.8+ requirement
- Dependency management with requirements.txt
- Environment variable configuration

### 2. **Monitoring**
- Log aggregation setup
- Performance metric collection
- Error alerting

### 3. **Scaling**
- Horizontal scaling with multiple instances
- Load balancing for API requests  
- Database scaling for analytics

## Migration Path

### Phase 1: Core Refactoring ✅
- [x] Configuration management
- [x] Error handling
- [x] Documentation

### Phase 2: Pipeline Improvements
- [ ] Async processing
- [ ] Enhanced caching
- [ ] Performance optimization

### Phase 3: Advanced Features
- [ ] Custom provider plugins
- [ ] Real-time monitoring dashboard
- [ ] Auto-scaling capabilities

## Glossary

- **Hop**: Individual step in the 12-step reasoning chain
- **Segment**: Input text unit being analyzed
- **Provider**: LLM API service (Gemini, OpenRouter, etc.)
- **Shadow Mode**: Regex evaluation without short-circuiting LLM calls
- **Consensus**: Agreement mechanism for multiple results
- **Trace**: Detailed execution log for debugging 