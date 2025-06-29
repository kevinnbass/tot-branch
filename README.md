# Tree-of-Thought Multi-Coder Analysis System

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

A sophisticated multi-agent analysis system that implements Tree-of-Thought reasoning for complex text classification and framing analysis. The system combines deterministic regex rules with large language models in a 12-hop reasoning chain to provide highly accurate and interpretable results.

## 🏗️ Architecture Overview

The system implements a layered architecture with the following core components:

- **Tree-of-Thought Pipeline**: 12-hop reasoning chain for complex analysis
- **Regex Engine**: High-performance pattern matching with shadow mode
- **LLM Providers**: Support for Gemini and OpenRouter APIs
- **Consensus System**: Multiple voting strategies for robust results
- **Annotation Analytics**: Advanced metrics and performance tracking
- **Tracing System**: Detailed execution traces for debugging and analysis

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Git
- API keys for your chosen LLM provider

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tot_branch
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # For Gemini
   export GOOGLE_API_KEY="your-gemini-api-key"
   
   # For OpenRouter
   export OPENROUTER_API_KEY="your-openrouter-api-key"
   ```

4. **Verify installation**
   ```bash
   python -m pytest tests/ -v
   ```

### Basic Usage

```bash
# Run with default settings (Gemini provider)
python multi_coder_analysis/main.py --use-tot --input data/sample.csv

# Use OpenRouter provider
python multi_coder_analysis/main.py --use-tot --provider openrouter --input data/sample.csv

# Run with custom configuration
python multi_coder_analysis/main.py --use-tot --config config.yaml --input data/sample.csv
```

## 📁 Project Structure

```
tot_branch/
├── multi_coder_analysis/          # Core analysis system
│   ├── config/                    # Configuration management
│   ├── core/                      # Core algorithms and pipelines
│   │   ├── pipeline/              # ToT pipeline implementation
│   │   └── regex/                 # Regex engine
│   ├── llm_providers/             # LLM provider implementations
│   ├── providers/                 # Provider abstractions
│   ├── runtime/                   # CLI and execution runtime
│   └── utils/                     # Utility functions
├── scripts/                       # Maintenance and analysis scripts
├── tests/                         # Test suite
├── docs/                          # Documentation
└── output/                        # Analysis results and traces
```

## 🔧 Configuration

The system uses a layered configuration approach:

1. **Default settings** in `multi_coder_analysis/config/settings.py`
2. **YAML configuration** files (optional)
3. **Environment variables** (prefixed with `MCA_`)
4. **Command-line arguments** (highest priority)

### Example Configuration

```yaml
# config.yaml
provider: "gemini"
model: "models/gemini-2.5-flash-preview-04-17"
batch_size: 10
concurrency: 4
regex_mode: "live"
log_level: "INFO"

# Feature flags
shuffle_batches: false
shuffle_segments: false
enable_regex: true

# Observability
json_logs: false
archive_enable: true
```

## 🧠 Tree-of-Thought Pipeline

The system implements a 12-hop reasoning chain where each hop represents a specific analytical step:

### Hop Structure

1. **Q1-Q3**: Initial framing detection
2. **Q4-Q6**: Context and stakeholder analysis  
3. **Q7-Q9**: Causal reasoning and implications
4. **Q10-Q12**: Final classification and confidence

### Execution Modes

- **Live Mode**: Regex rules short-circuit LLM calls when confident
- **Shadow Mode**: Regex runs alongside LLM for comparison
- **LLM-only Mode**: Disable regex entirely for pure neural processing

## 🎯 Features

### Advanced Analytics

- **Coverage Analysis**: Track regex rule effectiveness
- **Performance Profiling**: Identify bottlenecks and optimization opportunities  
- **Evolution Tracking**: Monitor system changes over time
- **Technical Debt Analysis**: Automated code quality assessment

### Flexible Execution

- **Batch Processing**: Configurable batch sizes for optimal performance
- **Concurrency Control**: Thread-based parallelization
- **Permutation Sweeps**: Test multiple configurations automatically
- **Consensus Strategies**: Multiple voting and agreement mechanisms

### Robust Error Handling

- **Graceful Degradation**: Fallback strategies for API failures
- **Retry Logic**: Automatic retry with exponential backoff
- **Detailed Logging**: Comprehensive trace information
- **Validation**: Input validation and sanity checking

## 📊 Output Formats

### Analysis Results

- **CSV Files**: Structured results with confidence scores
- **JSONL Traces**: Detailed execution traces for each input
- **Performance Metrics**: Token usage, timing, and accuracy statistics
- **Evaluation Reports**: Comparison against gold standards

## 🧪 Testing

The system includes comprehensive tests:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_regex_engine_basic.py -v
python -m pytest tests/test_annotation_system.py -v

# Run with coverage
python -m pytest tests/ --cov=multi_coder_analysis --cov-report=html
```

## 🔍 Debugging and Analysis

### Annotation Analytics

```bash
# Generate comprehensive analysis
python scripts/annotation_analytics.py --output analysis_report.json

# Coverage analysis only
python scripts/generate_coverage_report.py

# Validate annotation consistency
python scripts/validate_annotations.py
```

### Development Tools

```bash
# Set up development environment
python scripts/annotation_dev_tools.py setup

# Generate Vim syntax highlighting
python scripts/annotation_dev_tools.py vim-config

# Archive old results
python scripts/annotation_dev_tools.py archive-outputs
```

## 🚀 Performance Optimization

### Regex Engine Tuning

- **Pattern Optimization**: Automated suggestions for slow patterns
- **Complexity Scoring**: Identify resource-intensive rules
- **Hit Rate Analysis**: Remove ineffective patterns

### LLM Provider Optimization

- **Batch Size Tuning**: Find optimal batch sizes for your use case
- **Provider Comparison**: A/B test different LLM providers
- **Token Management**: Monitor and optimize token usage

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes**: Follow the coding standards
4. **Add tests**: Ensure comprehensive test coverage
5. **Update documentation**: Keep docs current
6. **Submit a pull request**: Include detailed description

### Code Standards

- **Type Hints**: Use type annotations for all functions
- **Docstrings**: Google-style docstrings for all modules/classes/functions
- **Error Handling**: Specific exception types, no bare except statements
- **Testing**: Unit tests for all new functionality
- **Logging**: Appropriate log levels and structured messages

## 📚 API Reference

### Core Classes

- `multi_coder_analysis.core.pipeline.tot.ToTPipeline`: Main pipeline orchestrator
- `multi_coder_analysis.core.regex.engine.Engine`: Regex matching engine
- `multi_coder_analysis.providers.base.LLMProvider`: Base provider interface
- `multi_coder_analysis.config.settings.Settings`: Configuration management

## 🐛 Troubleshooting

### Common Issues

**ImportError: No module named 'multi_coder_analysis'**
- Ensure you're running from the project root
- Try: `python -m multi_coder_analysis.main` instead of `python multi_coder_analysis/main.py`

**API Key Issues**
- Verify environment variables are set correctly
- Check API key permissions and quotas
- Test with a simple API call outside the system

**Performance Issues**
- Reduce batch size if experiencing memory issues
- Lower concurrency for rate-limited APIs
- Enable shadow mode to compare regex vs LLM performance

### Debug Mode

```bash
# Enable verbose logging
python multi_coder_analysis/main.py --use-tot --input data/test.csv --log-level DEBUG

# Run single hop for debugging
python multi_coder_analysis/main.py --use-tot --only-hop 1 --input data/test.csv

# Disable regex for pure LLM testing
python multi_coder_analysis/main.py --use-tot --regex-mode off --input data/test.csv
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Tree-of-Thought reasoning methodology
- Contributors and maintainers
- Open source community

---

For more detailed documentation, see the [docs/](docs/) directory.
For support, please open an issue on GitHub. 