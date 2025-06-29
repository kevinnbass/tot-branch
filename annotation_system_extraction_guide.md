# Regex Annotation System - Extraction Guide

This document outlines how to cleanly extract the regex annotation system that governs the correspondence between regex rules and prompt segments.

## 📦 **COMPLETE ANNOTATION SYSTEM PACKAGE**

### **Core Scripts** (Move to new repo root):
```
annotation-system/
├── validate_annotations.py      # Main validation tool (272 lines)
├── annotation_dev_tools.py      # Development workflow tools (484 lines)
├── annotation_analytics.py      # Analytics and reporting (793 lines)
├── generate_coverage_report.py  # Documentation generation (464 lines)
├── fix_annotation_bugs.py       # Bug fix utilities (183 lines)
├── annotation_prompt_loader.py  # Standalone prompt parser (44 lines)
└── tests/
    └── test_annotation_system.py # Complete test suite (25 tests)
```

### **Data Files** (Coordinate between repos):
```
data/
├── regex/
│   └── hop_patterns.yml         # Regex rules with # [Q1.1] annotations
└── prompts/
    ├── hop_Q01.txt              # Prompts with row_map/regex_map metadata
    ├── hop_Q02.txt
    └── ... (all hop_Q*.txt files)
```

### **Configuration** (New repo):
```
├── requirements.txt             # PyYAML>=6.0, pytest>=7.0
├── README.md                    # Usage and integration guide
├── pyproject.toml              # Modern Python package config
└── .github/workflows/
    └── validation.yml           # CI for annotation validation
```

## 🔧 **EXTRACTION STEPS**

### **1. Files Ready for Immediate Move**:
All annotation scripts are now **self-contained** and can be moved directly:

- ✅ `scripts/validate_annotations.py`
- ✅ `scripts/annotation_dev_tools.py` 
- ✅ `scripts/annotation_analytics.py`
- ✅ `scripts/generate_coverage_report.py`
- ✅ `scripts/fix_annotation_bugs.py`
- ✅ `scripts/annotation_prompt_loader.py` (created)
- ✅ `tests/test_annotation_system.py`

### **2. Data Files Coordination**:
The annotation system requires access to:
- **Regex patterns**: `multi_coder_analysis/regex/hop_patterns.yml`
- **Prompt metadata**: `multi_coder_analysis/prompts/hop_Q*.txt` files

**Options:**
1. **Copy to new repo**: Duplicate data files in annotation repo
2. **Git submodule**: Keep data in main repo, reference as submodule
3. **API interface**: Main repo provides annotation data via API
4. **Shared package**: Create separate data package both repos depend on

### **3. Integration Interface**:
For the main codebase that still needs prompt loading:

```python
# main_codebase/utils/prompt_loader.py (keep existing)
# OR create interface:
def get_prompt_metadata(hop_id: str) -> Dict[str, Any]:
    """Interface for main codebase to get prompt metadata."""
    # Implementation depends on chosen data strategy
```

## 🎯 **RECOMMENDED EXTRACTION STRATEGY**

### **Phase 1: Immediate (Self-contained tools)**
Create new repo with:
```bash
mkdir regex-annotation-system
cd regex-annotation-system

# Copy all annotation scripts
cp ../tot_branch/scripts/validate_annotations.py .
cp ../tot_branch/scripts/annotation_*.py .
cp ../tot_branch/scripts/generate_coverage_report.py .
cp ../tot_branch/scripts/fix_annotation_bugs.py .
cp -r ../tot_branch/tests/test_annotation_system.py tests/

# Create standalone package
pip install -e .
```

### **Phase 2: Data Strategy** 
Choose one approach:

**Option A - Git Submodule (Recommended)**:
```bash
# In annotation repo
git submodule add ../tot_branch/data data
# Scripts reference: ./data/regex/hop_patterns.yml
```

**Option B - Copy Data**:
```bash
# Copy data files to annotation repo
mkdir -p data/regex data/prompts
cp ../tot_branch/multi_coder_analysis/regex/hop_patterns.yml data/regex/
cp ../tot_branch/multi_coder_analysis/prompts/hop_Q*.txt data/prompts/
```

### **Phase 3: Main Repo Cleanup**
Remove annotation-specific code from main repo:
```bash
# Remove extracted files
rm scripts/validate_annotations.py
rm scripts/annotation_*.py
rm scripts/generate_coverage_report.py
rm scripts/fix_annotation_bugs.py
rm tests/test_annotation_system.py

# Keep: multi_coder_analysis/utils/prompt_loader.py (main codebase still uses it)
```

## 🏃 **USAGE AFTER EXTRACTION**

### **Standalone Annotation System**:
```bash
# In new annotation repo
python validate_annotations.py --project-root /path/to/data
python annotation_dev_tools.py test "dangerous virus spreading"
python generate_coverage_report.py --output ./docs
python annotation_analytics.py --full-analysis
```

### **Integration with Main Codebase**:
```bash
# Option 1: Submodule approach
cd main_repo && git submodule update --remote annotation-system

# Option 2: Package approach  
pip install regex-annotation-system
python -m regex_annotation_system.validate --data-path ./data
```

## 📊 **BENEFITS OF EXTRACTION**

1. **🔄 Independent Development**: Annotation system can evolve separately
2. **🧪 Focused Testing**: 25 dedicated tests for annotation functionality  
3. **📚 Specialized Documentation**: Detailed docs for annotation workflows
4. **🔧 Tool Ecosystem**: IDE integrations, CI/CD for annotation validation
5. **👥 Contributor Focus**: Separate team can maintain annotation system
6. **📦 Reusability**: Other projects can use the annotation system

## ⚠️ **COORDINATION POINTS**

1. **Schema Changes**: Updates to `row_map`/`regex_map` format need coordination
2. **Data Sync**: Keep regex patterns and prompts synchronized if duplicated
3. **Version Compatibility**: Ensure annotation tools work with data format versions
4. **CI Integration**: Main repo CI should validate annotations before merge

---

**Ready for extraction!** All annotation scripts are now self-contained and the extraction can be performed cleanly without breaking the main codebase. 