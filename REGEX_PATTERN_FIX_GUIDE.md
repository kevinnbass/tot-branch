# Regex Pattern Fix Guide

This guide addresses the specific regex errors found in the original patterns and provides concrete fixes.

## 🐛 **Identified Regex Errors**

Based on pattern testing, these errors were detected:

### 1. **"look-behind requires fixed-width pattern"**
- **Rule**: `IntensifierRiskAdjV2`
- **Location**: Hop Q1
- **Issue**: Variable-width lookbehind patterns

### 2. **"global flags not at the start of the expression"**
- **Rules**: `HighPotencyVerbMetaphor` (Q2), `MinimiserScaleContrast` (Q6)
- **Issue**: Inline flags `(?i)` placed incorrectly within the pattern

## 🔧 **How to Fix Each Error Type**

### **Fix 1: Variable-Width Lookbehind**

**Problem**: Lookbehind assertions `(?<=...)` and `(?<!...)` must be fixed-width in Python regex.

**Common Causes**:
```regex
(?<=word|phrase)        # Different lengths: "word"(4) vs "phrase"(6)
(?<=\w+)               # Variable quantifier: + means 1 or more
(?<=.*)                # Variable quantifier: * means 0 or more
```

**Solutions**:

**Option A**: Convert to lookahead (if possible)
```regex
# Instead of: (?<=prefix)pattern
# Use: prefix(?=pattern)
```

**Option B**: Use word boundaries
```regex
# Instead of: (?<=\s)word
# Use: \bword\b
```

**Option C**: Make lookbehind fixed-width
```regex
# Instead of: (?<=word|phrase)
# Use: (?<=word\s\s)|(?<=phrase)  # Pad to same length
```

**Option D**: Remove lookbehind entirely
```regex
# Instead of: (?<=prefix)pattern
# Use: prefix\s*pattern  # Then extract the pattern part
```

### **Fix 2: Global Flags Position**

**Problem**: Inline flags like `(?i)` must be at the very beginning of the pattern.

**Incorrect**:
```regex
some_pattern(?i)case_insensitive_part
prefix(?i)suffix
```

**Correct**:
```regex
(?i)some_pattern_case_insensitive_part
(?i)prefix.*suffix
```

**Alternative**: Use re.IGNORECASE flag in Python instead of inline flags
```python
re.search(pattern, text, re.IGNORECASE)
```

## 🛠️ **Step-by-Step Fix Process**

### **Step 1: Identify Problematic Patterns**

Run the pattern tester to find errors:
```bash
python scripts/annotation_dev_tools.py test "sample text"
```

Look for `"status": "regex_error"` entries.

### **Step 2: Locate the Pattern in hop_patterns.yml**

Find the rule by name in `multi_coder_analysis/regex/hop_patterns.yml`:
```yaml
1:
- name: IntensifierRiskAdjV2
  pattern: |-
    # Your problematic pattern here
```

### **Step 3: Apply the Appropriate Fix**

Based on the error type, apply one of the fixes above.

### **Step 4: Test the Fix**

```bash
# Test the specific pattern
python scripts/annotation_dev_tools.py test "text that should match your pattern"

# Validate the entire system
python scripts/validate_annotations.py --ci
```

## 📋 **Specific Fixes for Your Patterns**

### **IntensifierRiskAdjV2 (Q1)**

**Likely Issue**: Variable-width lookbehind

**Diagnosis Steps**:
1. Find the pattern in `hop_patterns.yml` under hop 1
2. Look for `(?<=...)` or `(?<!...)` constructs
3. Check if they contain `+`, `*`, `|` with different lengths

**Common Fix**:
```yaml
# Before (problematic):
pattern: |-
  (?<=\w+\s)(?i)\b(?:very|extremely|highly)\s+(?:dangerous|deadly|severe)\b

# After (fixed):
pattern: |-
  (?i)\b(?:very|extremely|highly)\s+(?:dangerous|deadly|severe)\b
```

### **HighPotencyVerbMetaphor (Q2)**

**Likely Issue**: Inline flag position

**Common Fix**:
```yaml
# Before (problematic):
pattern: |-
  some_pattern(?i)metaphor_part

# After (fixed):
pattern: |-
  (?i)some_pattern.*metaphor_part
```

### **MinimiserScaleContrast (Q6)**

**Same issue as Q2** - move `(?i)` to the beginning.

## 🧪 **Testing Strategy**

### **1. Unit Test Individual Patterns**

Create test cases for each fixed pattern:
```python
import re

# Test the fixed pattern
pattern = r"(?i)\b(?:very|extremely|highly)\s+(?:dangerous|deadly|severe)\b"
test_cases = [
    "The virus is extremely dangerous",  # Should match
    "Very deadly outbreak",              # Should match  
    "Highly severe symptoms",            # Should match
    "Somewhat risky situation",          # Should NOT match
]

for test in test_cases:
    match = re.search(pattern, test)
    print(f"'{test}' -> {'MATCH' if match else 'NO MATCH'}")
```

### **2. Integration Test**

```bash
# Test multiple patterns at once
python scripts/annotation_dev_tools.py test "The extremely dangerous virus ravaged the population but officials say it's now under control"

# Should show matches from multiple hops without regex errors
```

### **3. Performance Test**

```bash
# Check if fixes impact performance
python -c "
import time
import re

pattern = 'your_fixed_pattern'
text = 'your_test_text' * 1000

start = time.time()
for _ in range(1000):
    re.search(pattern, text)
end = time.time()

print(f'Time per match: {(end-start)*1000:.2f}ms')
"
```

## 🎯 **Recommended Fix Priority**

### **High Priority** (Fix Immediately)
1. **IntensifierRiskAdjV2** - Core alarmist detection
2. **HighPotencyVerbMetaphor** - Key metaphor detection

### **Medium Priority** (Fix Soon)  
3. **MinimiserScaleContrast** - Reassuring pattern detection

### **Low Priority** (Fix When Convenient)
- Any shadow/deprecated rules
- Performance optimizations for working patterns

## 🔍 **Advanced Debugging**

### **Regex Debugging Tools**

**Online Tools**:
- regex101.com - Visual regex testing
- regexpal.com - Simple pattern testing
- regexr.com - Interactive regex builder

**Python Debugging**:
```python
import re

# Enable regex debugging (Python 3.7+)
pattern = re.compile(r"your_pattern", re.DEBUG)

# Or use verbose mode for complex patterns
pattern = re.compile(r"""
    (?i)                    # Case insensitive
    \b                      # Word boundary
    (?:very|extremely)      # Intensifiers
    \s+                     # One or more spaces
    (?:dangerous|deadly)    # Risk adjectives
    \b                      # Word boundary
""", re.VERBOSE)
```

### **Pattern Optimization**

**Before Optimization**:
```regex
(?i)\b(?:very|extremely|highly|so|more|most|quite|rather|pretty|really|truly|utterly)\s+(?:dangerous|deadly|severe|lethal|harmful|toxic|hazardous|perilous|risky|unsafe)
```

**After Optimization**:
```regex
(?i)\b(?:very|extremely|highly)\s+(?:dangerous|deadly|severe)\b
```

**Benefits**:
- Faster execution
- Easier maintenance  
- Fewer false positives
- More predictable behavior

## 🚀 **Implementation Workflow**

### **1. Backup Current Patterns**
```bash
cp multi_coder_analysis/regex/hop_patterns.yml multi_coder_analysis/regex/hop_patterns.yml.backup
```

### **2. Fix One Pattern at a Time**
- Edit the YAML file
- Test the specific pattern
- Validate the entire system
- Commit the change

### **3. Document Changes**
Add comments to the YAML file:
```yaml
1:
- name: IntensifierRiskAdjV2
  # Fixed: Removed variable-width lookbehind (?<=\w+\s)
  # Changed: Moved (?i) flag to beginning
  pattern: |-
    (?i)\b(?:very|extremely|highly)\s+(?:dangerous|deadly|severe)\b
```

### **4. Update Tests**
Update any existing test cases to match the new patterns.

## ✅ **Success Criteria**

After fixing patterns, you should see:

1. **No regex errors** in pattern testing:
   ```json
   {
     "matches": [...],
     "hop_sequence": [...],
     "explanation": "Text would likely be classified as 'Alarmist' based on 2 regex matches."
   }
   ```

2. **Improved performance** (patterns execute faster)

3. **Better accuracy** (fewer false positives/negatives)

4. **Clean validation** (no regex-related warnings)

## 🎉 **Final Notes**

- **Test thoroughly** - Regex changes can have unexpected effects
- **Keep backups** - Always backup before making changes  
- **Document changes** - Comment why you made each change
- **Monitor performance** - Some fixes might impact speed
- **Validate coverage** - Ensure fixed patterns still catch intended cases

The annotation system will continue working even with broken regex patterns (it falls back to LLM-only classification), but fixing them will improve accuracy and performance. 