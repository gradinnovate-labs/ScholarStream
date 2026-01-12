---
name: workflow-automation
description: Automate ScholarStream course content generation workflow from topic request to final PDF
license: MIT
metadata:
  audience: course-creators
  category: automation
---

# Workflow Automation Skill

This skill provides automated workflow orchestration for generating complete course materials in ScholarStream.

## Usage

### Generate Complete Course Week

```
@workflow-automation generate week=01 topic="Markov Decision Process" hours=3 audience="beginner" direction="theory"
```

### Validate Course Week

```
@workflow-automation validate week=01
```

### Generate Summary Report

```
@workflow-automation summary week=01
```

## What I Do

I help you create complete course materials by:
1. Coordinating Planner Agent with subagents
2. Managing Blackboard state for agent communication
3. Orchestrating the complete workflow from research to slides

## When to Use Me

Use this skill when:
- You want to generate a complete week's worth of content
- You need to validate a week's structure and URLs
- You want to get a summary of progress

## How I Work

### 1. Initialize Workflow

When generating a new week, I will:
- Create the week directory structure using `directory_manager.py`
- Initialize Blackboard with week configuration
- Prepare for Planner agent invocation

### 2. Coordinate Research Phase

The workflow coordinates these steps:

**a) Initial Research Request**
```
Invoke Planner with:
- Topic, Hours, Audience, Direction, Emphasis
- Week Number from parameters
```

**b) URL Validation**
```
After Planner generates references.md:
- Use URL validator to check all URLs
- Generate validation report
- Store results in Blackboard
- Update references.md with validation status
```

**c) Subagent Delegation** (if needed)
```
Based on research needs, Planner will delegate to:
- @explore - for code analysis and patterns
- @librarian - for external documentation research
- @oracle - for architecture decisions
```

### 3. Output Coordination

```
Generate research documents in week{XX}/plan/
- Validate all URLs and record status in Blackboard
- Prepare Blackboard for slide-generator to query
- Report completion status
```

### 4. Slide Generation

```
Slide-generator reads from Blackboard:
- Week configuration (topic, audience, hours)
- Core concepts and notation table
- URL validation status

Generates week{XX}/slides/week{XX}_slides.md
Converts to PDF using Marp CLI
```

### 5. Validation and Summary

```
Validate complete week structure:
- All required files present
- URLs validated and marked
- Blackboard populated with all results

Generate summary:
- Research findings
- Validation status
- Recommendations
```

## Blackboard Integration

The workflow uses Blackboard to share state:

```
Week Config:
{
  "topic": "MDP",
  "hours": 3,
  "audience": "beginner",
  "direction": "theory",
  "emphasis": "depth"
}

Research Complete Event:
{
  "event": "research_complete",
  "week": 1,
  "sections_count": 4,
  "urls_validated": 15
}

URL Validation Results:
{
  "total": 20,
  "valid": 18,
  "invalid": 2,
  "failed_urls": ["url1", "url2"]
}
```

Slide-generator can query this data using:
```python
from .opencode.tools.blackboard import ScholarStreamBlackboard

bb = ScholarStreamBlackboard(".opencode/.blackboard.json")

# Get week config
config = bb.retrieve_knowledge("week_01_config")

# Get validation results
validation = bb.query("planner", ["week01", "url_validation"], min_confidence=0.9)

# Get core concepts
concepts = bb.query("planner", ["week01", "concept"], min_confidence=0.8)
```

## Complete Workflow Example

```bash
# Step 1: Create week structure
python .opencode/tools/directory_manager.py create 1

# Step 2: Invoke Planner (uses web search, validates URLs, stores to Blackboard)
@planner Week=1 Topic="Neural Networks" Hours=4 Audience="intermediate" Direction="implementation" Emphasis="practice"

# Step 3: Validate URLs explicitly (Planner does this, but workflow can re-validate)
python .opencode/tools/url_validator.py file week01/plan/references.md --format markdown

# Step 4: Invoke Slide Generator (reads from Blackboard)
@slide-generator 生成 week01 的簡報

# Step 5: Validate complete week
python .opencode/tools/scholarstream_manager.py validate 1

# Step 6: Generate summary
python .opencode/tools/scholarstream_manager.py report --week 1
```

## Parameters

- `week`: Week number (1, 2, 3...)
- `topic`: Course topic string
- `hours`: Duration in hours (default: 3)
- `audience`: Target audience
  - `beginner`: Beginners with minimal technical background
  - `intermediate`: Some experience, need practical examples
  - `advanced`: Experts, need depth and optimization
  - `decision-maker`: Managers, need trade-offs and business value
- `direction`: Teaching approach
  - `theory`: Mathematical foundations, proofs, principles
  - `implementation`: Code, frameworks, tools, best practices
  - `application`: Use cases, case studies, practical applications
- `emphasis`: Focus area
  - `depth`: Theoretical depth and rigor
  - `practice`: Hands-on implementation and exercises
  - `cases`: Real-world examples and case studies

## Expected Output

1. **Directory Structure** (automatic):
   ```
   week{XX}/
   ├── plan/
   │   ├── research_summary.md
   │   ├── section_01_research.md
   │   ├── section_02_research.md
   │   └── references.md
   ├── slides/
   │   ├── week{XX}_slides.md
   │   └── week{XX}_slides.pdf
   ├── assignments/
   ├── assets/
   └── README.md
   ```

2. **Blackboard State**: All research data stored and accessible by other agents

3. **Validation Reports**: URL validation results with clear status

4. **Summary**: Complete overview of week generation with statistics

## Workflow Steps

The automated workflow includes:

1. **Directory Setup**
   - Create week directory structure using `directory_manager.py`
   - Verify all required subdirectories exist

2. **Research & Planning**
   - Invoke `@planner` with course parameters
   - Generate research documents in `plan/` directory
   - Validate all URLs in research documents

3. **Slide Generation**
   - Invoke `@slide-generator` to create presentations
   - Convert Markdown to PDF using Marp CLI
   - Verify PDF generation success

4. **Quality Assurance**
   - Validate directory structure
   - Check URL validity
   - Generate summary report

## Parameters

- `week`: Week number (required)
- `topic`: Course topic (required)
- `hours`: Estimated duration in hours (default: 3)
- `audience`: Target audience - "beginner", "intermediate", "advanced", "decision-maker" (default: "beginner")
- `direction`: Teaching direction - "theory", "implementation", "application" (default: "theory")
- `emphasis`: Emphasis areas - "depth", "practice", "cases" (default: "depth")

## Output

The workflow generates:

```
week{XX}/
├── plan/
│   ├── research_summary.md
│   ├── section_01_research.md
│   ├── section_02_research.md
│   └── references.md
├── slides/
│   ├── week{XX}_slides.md
│   └── week{XX}_slides.pdf
└── README.md
```

## Error Handling

The workflow includes built-in error handling:

- Automatic retry for URL validation failures
- Directory creation verification
- Markdown syntax validation before PDF generation
- Detailed error logging in `.opencode/workflow_errors.log`

## Examples

### Beginner-Friendly Theory Course

```
@workflow-automation generate week=02 topic="Neural Networks" hours=4 audience="beginner" direction="theory" emphasis="depth"
```

### Advanced Implementation Course

```
@workflow-automation generate week=05 topic="Transformer Architecture" hours=6 audience="advanced" direction="implementation" emphasis="practice"
```

### Decision-Maker Overview

```
@workflow-automation generate week=08 topic="AI Ethics Considerations" hours=2 audience="decision-maker" direction="application" emphasis="cases"
```

## Behind the Scenes

This skill uses:

- `.opencode/tools/directory_manager.py` for directory operations
- `.opencode/tools/url_validator.py` for URL validation
- `.opencode/tools/blackboard.py` for state management
- `@planner` agent for research and planning
- `@slide-generator` agent for presentation generation

All progress and results are stored in the blackboard for agent coordination.
