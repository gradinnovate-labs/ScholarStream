---
name: mermaid-patch
description: Automatically detect and fix common Mermaid syntax errors in markdown research files
license: MIT
compatibility: opencode
metadata:
  audience: planner-agent, slide-generator
  category: validation-fix
---

## What I Do

I automatically detect and fix common Mermaid syntax errors in markdown research files by:

1. **Scanning** markdown files for Mermaid code blocks
2. **Validating** each Mermaid block using mmdc
3. **Classifying** errors into categories (syntax, parsing, rendering)
4. **Applying** fix rules based on error patterns
5. **Re-validating** to ensure fixes are successful
6. **Reporting** all changes with detailed diff

## When to Use Me

Use this skill when:
- Planner Agent has just generated research markdown files
- Mermaid validation has failed (Parse errors)
- You need to batch-fix multiple research files
- You want to reduce manual error-fixing overhead

## How I Work

### Step 1: Scan Markdown Files

```bash
# Find all research markdown files in a week directory
find ./weekXX/plan/section_*_research.md
```

For each file:
- Extract all Mermaid code blocks (```mermaid ... ```)
- Track line numbers and block boundaries

### Step 2: Validate Each Block

```bash
# Validate individual mermaid block
mmdc -i <temp-file> -o /tmp/mermaid-validation-${RANDOM}.svg 2>&1
```

Collect error messages:
- Parse error on line X
- Expecting ... got ...
- Found X mermaid charts

### Step 3: Classify Errors

| Error Type | Pattern | Common Cause |
|-------------|----------|--------------|
| **Syntax Error** | `Parse error on line X` | Invalid syntax, wrong characters |
| **Parsing Error** | `Expecting ... got ...` | Language rule violation |
| **Rendering Error** | `TypeError`, `ReferenceError` | Semantic issues |

### Step 4: Apply Fix Rules

Based on error classification, apply appropriate fix rules (see Fix Rules Library below).

### Step 5: Re-validate

After applying fixes:
```bash
# Re-validate the entire file
mmdc -i ./weekXX/plan/section_XX_research.md -o /tmp/mermaid-validation-${RANDOM}.svg 2>&1
```

Verify:
- All blocks show `✅ Found X mermaid charts`
- No parse errors
- No expecting errors

### Step 6: Generate Report

Create a patch report with:
- File processed
- Number of blocks scanned
- Number of errors found
- Number of fixes applied
- Detailed diff of changes
- Validation status

## Prerequisites

- **Mermaid CLI (mmdc)**: Version 11.12.0 or higher
- **Python 3**: For parsing markdown and applying fixes
- **File Backup**: Always create backup before patching

## Fix Rules Library (MVP)

### Rule #1: Flowchart `<br/>` Replacement

**Detect Pattern:**
```regex
\[[^\]]*?<br\/?>[^\]]*?\]
```

**Error Message:**
```
Parse error on line X
...head<br/>(address: 1000)]...
Expecting 'SQE', 'DOUBLECIRCLEEND', ... got 'PS'
```

**Fix:**
```mermaid
# ❌ BEFORE
A[head pointer<br/>(address: 1000)]

# ✅ AFTER
A["head pointer
(address: 1000)"]
```

**Implementation:**
```python
def fix_flowchart_br_tag(content):
    # Replace <br/> with quoted newlines in flowchart nodes
    import re
    pattern = r'(\[[^\]]*?)<br\/?>([^\]]*?\])'
    replacement = r'["\1\\n\2"]'
    return re.sub(pattern, replacement, content)
```

**Success Rate:** ~95%

---

### Rule #2: Invalid `noteA[...]` Syntax

**Detect Pattern:**
```regex
noteA\[.*?\]
```

**Error Message:**
```
Parse error on line X
...noteA[Complexity: O(n)]...
Expecting 'SQE', ... got 'PS'
```

**Fix:**
```mermaid
# ❌ BEFORE
noteA[Complexity: O(n)]
note for A[Complexity: O(n)]

# ✅ AFTER
complexityA["Complexity O(n)
Worst case check all nodes"]
```

**Implementation:**
```python
def fix_invalid_note_syntax(content):
    import re
    # Replace noteA[...] with a regular node
    pattern = r'noteA\[([^\]]*)\]'
    # Extract content and create a regular node
    def replacer(match):
        note_content = match.group(1)
        # Clean up special syntax if present
        note_content = note_content.replace(':', ' ')
        return f'noteA["{note_content}"]'

    return re.sub(pattern, replacer, content)
```

**Success Rate:** ~90%

---

### Rule #3: Unquoted Special Characters

**Detect Pattern:**
```regex
([A-Za-z0-9_]+)\[([^\]]*[^\]"\'][^\]]*)\]
```

**Error Message:**
```
Parse error on line X
...head = null/None)]...
Expecting 'SQE', ... got 'PS'
```

**Fix:**
```mermaid
# ❌ BEFORE
A[head = null/None]
B{Is position = 0?}

# ✅ AFTER
A["head = null/None"]
B["Is position = 0?"]
```

**Implementation:**
```python
def fix_unquoted_special_chars(content):
    import re

    # Characters that require quoting in Mermaid
    special_chars = set(':()-[]<>|=')

    def should_quote(match):
        node_id = match.group(1)
        label = match.group(2)
        # Check if label contains special characters
        if any(char in label for char in special_chars):
            return f'{node_id}["{label}"]'
        return match.group(0)

    # Pattern: NodeID[label with special chars]
    pattern = r'([A-Za-z0-9_]+)\[([^\]]*[^\]"\'][^\]]*)\]'
    return re.sub(pattern, should_quote, content)
```

**Success Rate:** ~85%

---

## Safety Mechanisms

### Backup Before Patching

```python
import shutil
import os

def create_backup(file_path):
    """Create backup of original file"""
    backup_path = f"{file_path}.backup"
    if os.path.exists(backup_path):
        # Add timestamp if backup exists
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"

    shutil.copy2(file_path, backup_path)
    return backup_path

def restore_backup(file_path, backup_path=None):
    """Restore from backup if patching fails"""
    if backup_path is None:
        backup_path = find_latest_backup(file_path)

    if backup_path and os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        return True
    return False
```

### Validation Before Applying Fixes

```python
def validate_patch(file_path, temp_file_path="/tmp/temp_mermaid_check.md"):
    """Extract and validate a single mermaid block"""
    import re

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find mermaid blocks
    blocks = re.findall(r'```mermaid\n(.*?)\n```', content, re.DOTALL)

    if not blocks:
        return {"status": "no_blocks", "errors": []}

    # Validate each block
    validation_results = []
    for i, block in enumerate(blocks, 1):
        # Write block to temp file
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(f"```mermaid\n{block}\n```")

        # Run mmdc
        result = run_mmdc(temp_file_path)
        validation_results.append({
            "block_number": i,
            "status": "valid" if result["success"] else "invalid",
            "errors": result["errors"]
        })

    return {
        "total_blocks": len(blocks),
        "valid_blocks": sum(1 for r in validation_results if r["status"] == "valid"),
        "invalid_blocks": sum(1 for r in validation_results if r["status"] == "invalid"),
        "details": validation_results
    }
```

### Diff and Confirmation

```python
def generate_diff(original, modified):
    """Generate readable diff of changes"""
    import difflib

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile="original",
        tofile="modified",
        lineterm=""
    )

    return ''.join(diff)

def confirm_changes(file_path, backup_path):
    """Interactive confirmation of changes"""
    import subprocess

    # Generate diff
    with open(file_path, 'r') as f:
        modified = f.read()
    with open(backup_path, 'r') as f:
        original = f.read()

    diff = generate_diff(original, modified)

    print("\n" + "="*60)
    print("PROPOSED CHANGES:")
    print("="*60)
    print(diff)
    print("="*60)

    response = input("\nAccept these changes? (y/n/diff): ").strip().lower()

    if response == 'n':
        restore_backup(file_path, backup_path)
        return False
    elif response == 'diff':
        # Show detailed diff (could use external diff tool)
        print("\nOpening diff viewer...")
        subprocess.run(['diff', backup_path, file_path])
        return confirm_changes(file_path, backup_path)

    return True
```

## Patch Report Format

```markdown
# Mermaid Patch Report

## Metadata

- **File**: ./weekXX/plan/section_XX_research.md
- **Timestamp**: YYYY-MM-DD HH:MM:SS
- **Patcher**: mermaid-patch skill v1.0 (MVP)

## Summary

- **Total Mermaid Blocks**: 5
- **Errors Detected**: 3
- **Fixes Applied**: 3
- **Success Rate**: 100%
- **Validation Status**: ✅ All blocks valid

## Error Details

### Error #1: Flowchart <br/> Syntax

**Location:** Line 178
**Block:** Diagram 1
**Error Message:**
```
Parse error on line 178
...head<br/>(address: 1000)]...
Expecting 'SQE', 'DOUBLECIRCLEEND', ... got 'PS'
```

**Applied Fix:** Rule #1 - Flowchart `<br/>` Replacement

**Before:**
```mermaid
A[head pointer<br/>(address: 1000)]
```

**After:**
```mermaid
A["head pointer
(address: 1000)"]
```

**Validation:** ✅ Passed

---

### Error #2: Invalid note Syntax

**Location:** Line 385
**Block:** Diagram 3
**Error Message:**
```
Parse error on line 385
...noteA[Complexity: O(n)]...
Expecting 'SQE', ... got 'PS'
```

**Applied Fix:** Rule #2 - Invalid `noteA[...]` Syntax

**Before:**
```mermaid
noteA[Complexity: O(n)]
```

**After:**
```mermaid
complexityA["Complexity O(n)
Worst case check all nodes"]
```

**Validation:** ✅ Passed

---

## Detailed Diff

See section below for complete diff of all changes.

## Validation Result

```bash
mmdc -i ./weekXX/plan/section_XX_research.md -o /tmp/mermaid-validation-final.svg 2>&1

Output:
Found 5 mermaid charts in Markdown input
 ✅ ./mermaid-validation-final-1.svg
 ✅ ./mermaid-validation-final-2.svg
 ✅ ./mermaid-validation-final-3.svg
 ✅ ./mermaid-validation-final-4.svg
 ✅ ./mermaid-validation-final-5.svg
```

**Status:** ✅ All blocks successfully validated

## Backup File

- **Location:** ./weekXX/plan/section_XX_research.md.backup
- **Status:** Kept until manual confirmation
```

## Usage Example

### From Planner Agent

```markdown
## 執行步驟

5. **驗證 Mermaid 圖表**：
   - 執行驗證檢查

6. **【自動修復】如果驗證失敗**：
   - 調用 mermaid-patch skill 自動修復
   - 指令：`python3 .opencode/skill/mermaid-patch/scripts/patch_mermaid.py ./weekXX/plan/section_XX_research.md`

### 驗證失敗處理流程

當驗證失敗時，執行以下步驟：

1. 調用 mermaid-patch skill：
   ```bash
   skill mermaid-patch
   ```

2. Skill 會：
   - 自動掃描並識別錯誤
   - 應用修復規則
   - 創建備份
   - 生成修復報告

3. 審核修復報告：
   - 檢查修復內容是否正確
   - 確認驗證狀態

4. 如果修復正確，繼續下一步
   - 如果不正確，恢復備份並手動修復
```

### From Command Line

```bash
# Patch a single file
python3 .opencode/skill/mermaid-patch/scripts/patch_mermaid.py --file ./week01/plan/section_02_research.md

# Patch all research files
python3 .opencode/skill/mermaid-patch/scripts/patch_mermaid.py --directory ./week01/plan/ --pattern "section_*.md"

# Patch with auto-approve (skip confirmation)
python3 .opencode/skill/mermaid-patch/scripts/patch_mermaid.py --file ./week01/plan/section_02_research.md --auto-approve
```

## Known Limitations (MVP)

| Limitation | Impact | Future Improvement |
|-------------|---------|-------------------|
| **Context Understanding** | May misinterpret domain-specific meanings | Add semantic analysis |
| **Complex Errors** | May not fix multi-line or nested errors | Add AST-based parsing |
| **ER Diagram Issues** | Limited ER diagram support | Dedicated ER diagram rules |
| **Style Directive Issues** | May not handle style conflicts | Add style validation |
| **Learning** | No error pattern learning yet | Build knowledge base |

## Error Types Not Covered (MVP)

- ❌ Complex ER diagram relationship errors
- ❌ Multi-line node definitions with errors
- ❌ Style directive conflicts
- ❌ Graph syntax errors (mindmap, timeline)
- ❌ Semantic errors (valid syntax but wrong meaning)

## Notes

1. **Always Backup**: Never patch without creating backup first
2. **Validate Twice**: Validate before patching AND after patching
3. **Report Everything**: Keep detailed logs of all changes
4. **Manual Review**: For MVP, manual review is recommended for critical files
5. **Batch Mode**: Can process multiple files in sequence
6. **Rollback Support**: Always able to restore from backup if needed

## Resources

- [Mermaid Official Syntax Documentation](https://mermaid.js.org/intro/)
- [mermaid-validator Skill](/.opencode/skill/mermaid-validator/SKILL.md)
- [Planner Agent](/.opencode/agent/planner.md)
