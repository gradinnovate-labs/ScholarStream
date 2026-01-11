# How to Design an Agent

A comprehensive guide for Coding Agents on how to design, implement, and configure new OpenCode.ai agents with custom tools, skills, and permissions.

---

## Table of Contents

1. [Understanding OpenCode.ai Agent Architecture](#understanding-opencodeai-agent-architecture)
2. [Agent Design Decision Framework](#agent-design-decision-framework)
3. [Creating a New Agent](#creating-a-new-agent)
4. [Designing Custom Tools](#designing-custom-tools)
5. [Creating Agent Skills](#creating-agent-skills)
6. [Permissions and Security](#permissions-and-security)
7. [Complete Examples](#complete-examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Understanding OpenCode.ai Agent Architecture

### Core Concepts

OpenCode.ai uses a **client/server architecture**:
- **Backend**: JavaScript running on Bun runtime, exposed via HTTP server (Hono)
- **Provider-agnostic**: Supports multiple LLM providers (Anthropic, OpenAI, Gemini, etc.) via AI SDK
- **Event-driven**: Strongly-typed event bus manages all actions
- **Git-powered**: Every operation tracked via internal Git repository for undo functionality

### Agent Types

| Type | Description | Usage | Access |
|------|-------------|-------|--------|
| **Primary Agent** | Main assistant you interact with directly | Switch via Tab key during session | Full access to configured tools |
| **Subagent** | Specialized assistant for specific tasks | Invoked automatically by primary agents or via @mention | Configured tools and permissions |

### Built-in Agents (Reference)

```yaml
Primary Agents:
  - Build: Full tools enabled, default for development
  - Plan: Restricted mode, analysis-only (edit/bash → "ask")

Subagents:
  - General: Research, multi-step tasks, code searching
  - Explore: Fast codebase exploration, pattern matching
```

---

## Agent Design Decision Framework

When a user requests a new agent, follow this decision tree:

```
1. Analyze User Requirement
   ├─ What specific tasks will this agent perform?
   ├─ What tools does it need access to?
   ├─ What are the security constraints?
   └─ Should it be primary or subagent?

2. Choose Agent Type
   ├─ Primary: If user will interact directly (Tab-switchable)
   └─ Subagent: If invoked by other agents or via @mention

3. Determine Tool Access
   ├─ File operations (read, write, edit, patch, multiedit)
   ├─ Shell commands (bash)
   ├─ Search tools (grep, glob, list)
   ├─ Web tools (webfetch, websearch)
   ├─ LSP tools (diagnostics, code actions)
   ├─ Todo tools (todoread, todowrite)
   ├─ Agent orchestration (task, skill)
   └─ Custom tools / MCP servers

4. Set Permissions
   ├─ "allow": Auto-execute without approval
   ├─ "ask": Prompt user before each action
   └─ "deny": Block the action entirely

5. Select Model & Parameters
   ├─ Model: Provider/model-id (e.g., anthropic/claude-sonnet-4-20250514)
   ├─ Temperature: 0.0-1.0 (0.0-0.2 deterministic, 0.6-1.0 creative)
   ├─ Max Steps: Limit agentic iterations
   └─ Additional: Provider-specific parameters
```

---

## Creating a New Agent

### Decision: JSON vs Markdown

| Format | Use Case | Location |
|--------|----------|----------|
| **JSON** | Programmatic generation, complex nested configs | `opencode.json` |
| **Markdown** | Human-readable, self-documenting, inline prompts | `~/.config/opencode/agent/<name>.md` or `.opencode/agent/<name>.md` |

**Recommendation**: Use Markdown for most agents as it combines configuration with system prompts in one file.

### Agent Configuration Schema

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief description of what the agent does (shown in autocomplete) |

#### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mode` | `"primary" \| "subagent" \| "all"` | `"all"` | How the agent can be used |
| `model` | string | Global model or parent's model | Override model for this agent |
| `temperature` | number | Model default | Control randomness (0.0-1.0) |
| `maxSteps` | number | Unlimited | Max agentic iterations before text-only response |
| `disable` | boolean | `false` | Disable the agent |
| `hidden` | boolean | `false` | Hide from @autocomplete (subagents only) |
| `prompt` | string/file | OpenCode default | Custom system prompt |
| `tools` | object | Inherited | Enable/disable specific tools |
| `permission` | object | Inherited | Override global permissions |
| `additional` | object | None | Provider-specific parameters |

### Format 1: JSON Configuration

**Location**: `opencode.json` (global or project-specific)

```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "my-agent": {
      "description": "Specialized agent for [specific task]",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.3,
      "maxSteps": 10,
      "prompt": "{file:./prompts/my-agent.txt}",
      "tools": {
        "write": true,
        "edit": true,
        "bash": false
      },
      "permission": {
        "edit": "ask",
        "bash": "deny"
      },
      "additional": {
        "reasoningEffort": "high"
      }
    }
  }
}
```

### Format 2: Markdown Configuration

**Location**: `~/.config/opencode/agent/<name>.md` (global) or `.opencode/agent/<name>.md` (project)

**Filename** becomes the **agent name**.

```markdown
---
description: Specialized agent for [specific task]
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.3
maxSteps: 10
tools:
  write: true
  edit: true
  bash: false
permission:
  edit: ask
  bash: deny
---

# System Prompt

You are a specialized agent for [specific task].

Your responsibilities:
- [Specific capability 1]
- [Specific capability 2]
- [Specific capability 3]

When working:
1. [Step 1 of workflow]
2. [Step 2 of workflow]
3. [Step 3 of workflow]

## Constraints

- [Constraint 1]
- [Constraint 2]

## Output Format

[Specify expected output format]
```

---

## Designing Custom Tools

### Overview

Custom tools extend OpenCode with new capabilities. They are:
- Defined in TypeScript/JavaScript (using `@opencode-ai/plugin`)
- Can invoke scripts in ANY language (Python, Go, Rust, etc.)
- Auto-discovered from `.opencode/tool/` (project) or `~/.config/opencode/tool/` (global)
- **Filename** becomes the **tool name**

### Tool Structure

#### Basic Template

```typescript
// .opencode/tool/my-tool.ts
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Brief description of what this tool does",
  args: {
    paramName: tool.schema.string().describe("Parameter description"),
    // Add more args as needed
  },
  async execute(args, context) {
    // Tool implementation
    // context contains: { agent, sessionID, messageID }

    return "Tool result"
  },
})
```

#### Multiple Tools in One File

```typescript
// .opencode/tool/math.ts
import { tool } from "@opencode-ai/plugin"

export const add = tool({
  description: "Add two numbers",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args) {
    return args.a + args.b
  },
})

export const multiply = tool({
  description: "Multiply two numbers",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args) {
    return args.a * args.b
  },
})

// Creates: math_add and math_multiply tools
```

### Argument Schema (Zod)

Using `tool.schema` (which is Zod):

```typescript
args: {
  // String
  name: tool.schema.string().describe("Full name"),

  // Number
  count: tool.schema.number().describe("Item count"),

  // Boolean
  enabled: tool.schema.boolean().describe("Feature flag"),

  // Enum
  mode: tool.schema.enum(["fast", "slow"]).describe("Processing mode"),

  // Optional
  timeout: tool.schema.number().optional().describe("Timeout in seconds"),

  // Default value
  retries: tool.schema.number().default(3).describe("Retry count"),

  // Array
  tags: tool.schema.array(tool.schema.string()).describe("List of tags"),

  // Object
  options: tool.schema.object({
    verbose: tool.schema.boolean(),
    debug: tool.schema.boolean(),
  }).describe("Configuration options"),
}
```

### Invoking External Scripts

#### Python Example

```python
# .opencode/tool/process.py (Python script)
import sys
import json

# Read JSON args from stdin
args = json.loads(sys.stdin.read())

# Process
result = {
    "status": "success",
    "processed": len(args["items"]),
}

# Output JSON result
print(json.dumps(result))
```

```typescript
// .opencode/tool/process.ts (Tool definition)
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Process items using Python",
  args: {
    items: tool.schema.array(tool.schema.string()).describe("Items to process"),
  },
  async execute(args) {
    const result = await Bun.$`python3 .opencode/tool/process.py`.json(JSON.stringify(args)).json()
    return result
  },
})
```

#### Shell Command Example

```typescript
// .opencode/tool/git-status.ts
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Get git status summary",
  args: {},
  async execute() {
    const output = await Bun.$`git status --porcelain`.text()
    const lines = output.trim().split('\n')
    return {
      modified: lines.filter(l => l.startsWith(' M')).length,
      added: lines.filter(l => l.startsWith('??')).length,
      total: lines.length
    }
  },
})
```

### Context Access

```typescript
async execute(args, context) {
  const { agent, sessionID, messageID } = context

  // Access file system via context (if available)
  // Make API calls
  // Query databases
  // etc.

  return { agent, sessionID, messageID }
}
```

---

## Creating Agent Skills

### Overview

Agent Skills are **reusable behaviors** loaded on-demand via the `skill` tool. They:
- Are discovered from specific directories
- Consist of a `SKILL.md` file with YAML frontmatter
- Are loaded by name when needed
- Can include resources (scripts, templates, documentation)

### Skill Directory Structure

```
.opencode/skill/<skill-name>/SKILL.md
.opencode/skill/<skill-name>/resources/
.opencode/skill/<skill-name>/scripts/
```

### Skill Schema

#### Required Frontmatter

```yaml
---
name: skill-name          # Required: 1-64 chars, lowercase with hyphens
description: What this skill does  # Required: 1-1024 chars
license: MIT             # Optional
compatibility: opencode   # Optional
metadata:                # Optional (string-to-string map)
  audience: developers
  category: workflow
---
```

#### Name Validation

- Length: 1-64 characters
- Pattern: `^[a-z0-9]+(-[a-z0-9]+)*$`
- Must match the directory name
- Cannot start/end with `-`
- No consecutive `--`

### Skill Content Template

```markdown
---
name: my-skill
description: Brief description of what this skill does
license: MIT
compatibility: opencode
metadata:
  audience: developers
  category: workflow
---

## What I Do

[Explain what this skill accomplishes]

## When to Use Me

Use this skill when:
- [Condition 1]
- [Condition 2]

## How I Work

1. [Step 1 of the skill's workflow]
2. [Step 2]
3. [Step 3]

## Prerequisites

- [Prerequisite 1]
- [Prerequisite 2]

## Expected Output

[Describe what the skill produces]

## Notes

[Any important notes or caveats]
```

### Skill Discovery Locations

| Scope | Location |
|-------|----------|
| Project OpenCode | `.opencode/skill/<name>/SKILL.md` |
| Global OpenCode | `~/.config/opencode/skill/<name>/SKILL.md` |
| Project Claude | `.claude/skills/<name>/SKILL.md` |
| Global Claude | `~/.claude/skills/<name>/SKILL.md` |

### Loading a Skill

Agents see available skills in the `skill` tool description:

```xml
<available_skills>
  <skill>
    <name>my-skill</name>
    <description>Brief description of what this skill does</description>
  </skill>
</available_skills>
```

Load a skill:

```typescript
skill({ name: "my-skill" })
```

### Skill Permissions

Configure in `opencode.json`:

```json
{
  "permission": {
    "skill": {
      "my-skill": "allow",
      "internal-*": "deny",
      "experimental-*": "ask",
      "*": "allow"
    }
  }
}
```

Override per agent (Markdown frontmatter):

```yaml
---
permission:
  skill:
    "my-skill": "allow"
    "internal-*": "deny"
---
```

---

## Permissions and Security

### Permission Actions

| Action | Behavior |
|--------|----------|
| `"allow"` | Execute automatically without approval |
| `"ask"` | Prompt user before execution (once/always/reject options) |
| `"deny"` | Block the action entirely |

### Permission Hierarchy

```
Global Config (opencode.json)
  └─ Agent Config (JSON or Markdown frontmatter)
      └─ Runtime User Decision (when action is "ask")
```

**Agent permissions override global permissions.**

### Granular Rules (Object Syntax)

Apply different permissions based on tool input:

```json
{
  "permission": {
    "bash": {
      "*": "ask",              // Ask for all commands
      "git *": "allow",        // Allow git commands
      "npm *": "allow",        // Allow npm commands
      "rm *": "deny",          // Deny rm commands
      "docker rm *": "ask"     // Ask for docker rm (more specific wins)
    },
    "edit": {
      "*": "deny",             // Deny all edits
      "*.md": "allow",         // Allow markdown edits
      "packages/web/src/content/docs/*.mdx": "ask"  // Ask for docs
    },
    "webfetch": {
      "*": "allow",
      "https://internal-*": "deny"
    }
  }
}
```

**Rule Evaluation**: Last matching rule wins. Put catch-all `"*"` first, specific rules after.

### Wildcard Patterns

| Pattern | Matches |
|---------|---------|
| `*` | Zero or more of any character |
| `?` | Exactly one character |
| `git *` | All git commands |
| `*.env` | All .env files |
| `internal-*` | internal-docs, internal-tools, etc. |

### Available Permissions

| Permission | What It Controls | Granular Support |
|------------|------------------|------------------|
| `read` | File reads | Yes (file path) |
| `edit` | All file modifications (edit, write, patch, multiedit) | Yes (file path) |
| `glob` | File globbing | Yes (glob pattern) |
| `grep` | Content search | Yes (regex pattern) |
| `list` | Directory listing | Yes (directory path) |
| `bash` | Shell commands | Yes (parsed command) |
| `task` | Subagent invocation | Yes (agent name pattern) |
| `skill` | Skill loading | Yes (skill name) |
| `lsp` | LSP queries | No |
| `todoread` | Todo list reading | No |
| `todowrite` | Todo list writing | No |
| `webfetch` | URL fetching | Yes (URL) |
| `websearch` | Web search | Yes (query) |
| `codesearch` | Code search | Yes (query) |
| `external_directory` | Access outside project dir | No |
| `doom_loop` | Detect repetitive tool calls | No |

### Default Permissions

```json
{
  "permission": {
    "*": "allow",                    // Most tools allowed by default
    "doom_loop": "ask",              // Safety: ask if loop detected
    "external_directory": "ask",      // Safety: ask for external access
    "read": {
      "*": "allow",
      "*.env": "deny",                // Security: block .env files
      "*.env.*": "deny",
      "*.env.example": "allow"        // Allow .env.example
    }
  }
}
```

### "Ask" Behavior

When user is prompted:

| Option | Behavior |
|--------|----------|
| `once` | Approve just this request |
| `always` | Approve future requests matching suggested patterns (for current session) |
| `reject` | Deny the request |

### Agent-Specific Permissions

#### JSON

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "bash": { "*": "ask", "git status": "allow" }
  },
  "agent": {
    "my-agent": {
      "permission": {
        "bash": {
          "*": "ask",
          "git status": "allow",
          "git push": "allow"        // Override: add git push permission
        },
        "edit": "deny"
      }
    }
  }
}
```

#### Markdown

```markdown
---
description: My specialized agent
permission:
  edit: deny
  bash:
    "*": ask
    "git status": allow
    "git push": allow
  webfetch: deny
---
```

### Task Permissions (Subagent Invocation)

Control which subagents an agent can invoke:

```json
{
  "agent": {
    "orchestrator": {
      "permission": {
        "task": {
          "*": "deny",              // Deny all subagent invocation
          "orchestrator-*": "allow", // Allow orchestrator-* agents
          "code-reviewer": "ask"     // Ask for code-reviewer
        }
      }
    }
  }
}
```

**Note**: Users can always invoke any subagent via @autocomplete menu, even if task permissions would deny it.

---

## Complete Examples

### Example 1: Documentation Agent (Subagent)

**Scenario**: An agent that writes and maintains project documentation.

**Location**: `.opencode/agent/docs-writer.md`

```markdown
---
description: Writes and maintains project documentation
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.3
tools:
  write: true
  edit: true
  bash: false
permission:
  edit: ask
  bash: deny
  webfetch: allow
---

You are a technical writer specializing in clear, comprehensive documentation.

## Your Responsibilities

1. Create new documentation files when features are added
2. Update existing documentation to reflect changes
3. Ensure documentation is clear, well-structured, and user-friendly
4. Include code examples where appropriate
5. Use consistent formatting and style

## When Writing Documentation

1. **Understand the context**: Read relevant code to understand what you're documenting
2. **Identify the audience**: Is this for end users, developers, or maintainers?
3. **Structure the content**:
   - Start with a clear overview
   - Use headings to organize information
   - Include step-by-step guides for procedures
   - Add examples and code snippets
   - Include troubleshooting sections where relevant

4. **Review existing docs**: Maintain consistency with existing documentation style

## Output Format

Use Markdown with:
- ATX-style headings (# ## ###)
- Code blocks with language specifiers (\`\`\`typescript)
- Tables where appropriate
- Links to related documentation

## Constraints

- Never modify code files, only documentation
- Ask before making changes to existing documentation
- Avoid jargon unless it's standard for the audience
- Ensure all code examples are accurate and tested
```

### Example 2: Security Auditor Agent (Subagent)

**Scenario**: An agent that performs security audits and identifies vulnerabilities.

**Location**: `.opencode/agent/security-auditor.md`

```markdown
---
description: Performs security audits and identifies vulnerabilities
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
maxSteps: 20
tools:
  read: true
  glob: true
  grep: true
  write: false
  edit: false
  bash: false
permission:
  write: deny
  edit: deny
  bash: deny
---

You are a security expert specializing in code security audits.

## Your Focus Areas

When auditing code, look for:

### 1. Input Validation
- Unvalidated user input
- SQL injection vulnerabilities
- Command injection vulnerabilities
- XSS vulnerabilities
- Path traversal

### 2. Authentication & Authorization
- Missing authentication checks
- Weak password handling
- Improper session management
- Authorization bypasses
- Hardcoded credentials

### 3. Data Exposure
- Sensitive data in logs
- Debug information in production
- Unencrypted data transmission
- Exposed API keys or tokens

### 4. Dependency Issues
- Outdated vulnerable dependencies
- Known CVEs in used packages
- Unnecessary dependencies

### 5. Configuration Security
- Insecure default configurations
- Misconfigured CORS
- Exposed admin interfaces
- Weak encryption settings

## Audit Process

1. **Analyze the codebase structure** using glob and grep
2. **Review authentication flows** and session management
3. **Check input handling** throughout the application
4. **Examine data storage** and encryption practices
5. **Review dependencies** and package versions
6. **Identify configuration files** and their security settings

## Report Format

Provide findings in this structure:

```markdown
## Security Audit Report

### Critical Issues
[Critical vulnerabilities with immediate action required]

### High Severity
[Important security concerns]

### Medium Severity
[Security best practice improvements]

### Low Severity
[Minor security recommendations]

### Summary
- Total issues found: X
- Critical: X, High: X, Medium: X, Low: X
```

## Constraints

- You have read-only access
- Do not modify any files
- Focus on actionable, specific recommendations
- Provide code snippets for vulnerable code when possible
- Reference OWASP Top 10 or similar standards when applicable
```

### Example 3: Database Migration Agent (Primary)

**Scenario**: An agent for creating and applying database migrations.

**Location**: `opencode.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "migrator": {
      "description": "Creates and applies database migrations",
      "mode": "primary",
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.2,
      "maxSteps": 15,
      "tools": {
        "read": true,
        "write": true,
        "edit": true,
        "bash": true,
        "glob": true,
        "grep": true
      },
      "permission": {
        "write": {
          "*": "ask",
          "migrations/*.sql": "allow",
          "migrations/*.ts": "allow"
        },
        "edit": {
          "*": "ask",
          "migrations/*": "allow"
        },
        "bash": {
          "*": "ask",
          "npm run migrate:*": "allow",
          "npm run db:*": "allow"
        }
      }
    }
  }
}
```

### Example 4: API Testing Tool

**Scenario**: A custom tool for testing API endpoints.

**Location**: `.opencode/tool/api-test.ts`

```typescript
import { tool } from "@opencode-ai/plugin"

interface ApiTestResult {
  endpoint: string
  method: string
  statusCode: number
  responseTime: number
  body: unknown
  headers: Record<string, string>
}

export default tool({
  description: "Test an API endpoint and return the response",
  args: {
    url: tool.schema.string().url().describe("Full API endpoint URL"),
    method: tool.schema.enum(["GET", "POST", "PUT", "DELETE", "PATCH"]).default("GET").describe("HTTP method"),
    headers: tool.schema.record(tool.schema.string()).optional().describe("Request headers"),
    body: tool.schema.unknown().optional().describe("Request body for POST/PUT/PATCH"),
  },
  async execute(args): Promise<ApiTestResult> {
    const startTime = Date.now()

    try {
      const response = await fetch(args.url, {
        method: args.method,
        headers: args.headers || {},
        body: args.body ? JSON.stringify(args.body) : undefined,
      })

      const responseTime = Date.now() - startTime
      const body = await response.json().catch(() => response.text())

      return {
        endpoint: args.url,
        method: args.method,
        statusCode: response.status,
        responseTime,
        body,
        headers: Object.fromEntries(response.headers.entries()),
      }
    } catch (error) {
      const responseTime = Date.now() - startTime
      throw new Error(`API test failed after ${responseTime}ms: ${error}`)
    }
  },
})
```

### Example 5: Git Release Skill

**Scenario**: A reusable skill for creating Git releases with changelogs.

**Location**: `.opencode/skill/git-release/SKILL.md`

```markdown
---
name: git-release
description: Create consistent releases and changelogs from merged PRs
license: MIT
compatibility: opencode
metadata:
  audience: maintainers
  workflow: github
---

## What I Do

I help you create Git releases by:
1. Analyzing merged PRs since the last tag
2. Drafting release notes in a consistent format
3. Proposing a version bump (following semver)
4. Providing a copy-pasteable `gh release create` command

## When to Use Me

Use this skill when:
- You're preparing a new release
- You need to generate a changelog
- You want to ensure consistent release notes
- You're following semantic versioning

## How I Work

1. **Identify the last tag**: I'll find the most recent Git tag
2. **Analyze changes**: I'll review merged PRs and commits since that tag
3. **Categorize changes**:
   - **Breaking changes** (MAJOR version bump)
   - **New features** (MINOR version bump)
   - **Bug fixes** (PATCH version bump)
4. **Draft release notes**: I'll create a structured changelog
5. **Suggest version**: I'll recommend the appropriate version bump

## Prerequisites

- Project must use Git tags for versioning
- Git history must be accessible
- `gh` CLI should be available for creating releases

## Clarifying Questions

Before I proceed, I may ask:
- What versioning scheme do you follow (semver, calver, custom)?
- Are there any changes that should be excluded from the changelog?
- Should I focus on specific categories of changes?

## Output Format

```markdown
## Release Notes

### [VERSION] - [DATE]

#### Added
- [Feature 1]
- [Feature 2]

#### Changed
- [Change 1]

#### Deprecated
- [Deprecated item]

#### Removed
- [Removed item]

#### Fixed
- [Bug fix 1]
- [Bug fix 2]

#### Security
- [Security fix]
```

And the command:

```bash
gh release create vX.Y.Z --notes "..."
```

## Notes

- I'll only analyze merged PRs and commits
- Changes must be properly tagged/annotated for accurate categorization
- You should review the proposed changelog before creating the release
```

---

## Best Practices

### Agent Design

1. **Start with a clear description**: The `description` field is shown in autocomplete; make it actionable.

2. **Choose the right temperature**:
   - `0.0-0.2`: Code analysis, planning, testing
   - `0.3-0.5`: General development tasks
   - `0.6-1.0`: Brainstorming, exploration

3. **Set `maxSteps` for cost control**:
   - Simple tasks: 5-10 steps
   - Medium tasks: 10-20 steps
   - Complex tasks: 20-50 steps

4. **Use appropriate permissions**:
   - Default to `"ask"` for destructive actions
   - Use `"deny"` for security-sensitive operations
   - Use `"allow"` only for safe, repetitive operations

5. **Be specific with tool permissions**:
   - Don't give agents access to tools they don't need
   - Use wildcards for grouped permissions
   - Set specific exceptions after the catch-all

### Tool Design

1. **Provide clear descriptions**: Help the LLM understand when to use the tool.

2. **Validate inputs**: Use Zod schemas with `.describe()` for all parameters.

3. **Return structured data**: JSON outputs are easier for agents to process.

4. **Handle errors gracefully**: Return error messages that agents can understand and act on.

5. **Be idempotent when possible**: Tools should produce the same result for the same input.

6. **Document side effects**: Clearly state if a tool modifies state, makes network calls, etc.

### Skill Design

1. **Keep skills focused**: One skill should do one thing well.

2. **Use descriptive names**: Names should be lowercase with hyphens and describe the skill's purpose.

3. **Provide context in metadata**: Help agents understand the skill's audience, category, etc.

4. **Include prerequisites**: List any requirements the skill needs.

5. **Specify output format**: Agents should know exactly what to expect.

6. **Make them self-contained**: Skills should work independently without external dependencies.

### Permission Design

1. **Principle of least privilege**: Only grant permissions that are absolutely necessary.

2. **Default to "ask"**: When in doubt, require user approval.

3. **Use granular rules**: Take advantage of object syntax for fine-grained control.

4. **Order rules correctly**: Catch-all `"*"` first, specific rules after.

5. **Document your permissions**: Include comments explaining why certain permissions are set.

6. **Test permissions**: Verify that agents behave as expected with the configured permissions.

### Performance Considerations

1. **Limit tool context**: MCP servers can add significant context; enable only what's needed.

2. **Use smaller models for planning**: Haiku is sufficient for planning, use Sonnet/GPT-4 for implementation.

3. **Set `maxSteps` appropriately**: Prevent runaway agents from consuming excessive tokens.

4. **Lazy-load skills**: Agents load skills on-demand, reducing context overhead.

---

## Troubleshooting

### Agent Not Showing in Autocomplete

**Symptoms**: Agent doesn't appear when using @mention

**Solutions**:
1. Check that `mode` is set correctly (`primary` for Tab-switching, `subagent` or `all` for @mention)
2. Verify `hidden: false` (subagents only)
3. Check `disable: false`
4. Ensure config file is in correct location
5. Verify JSON syntax is valid (use `opencode config validate`)

### Tool Not Available

**Symptoms**: Agent can't call a custom tool

**Solutions**:
1. Verify tool file is in `.opencode/tool/` or `~/.config/opencode/tool/`
2. Check tool file has valid TypeScript/JavaScript syntax
3. Ensure `tool()` helper is imported from `@opencode-ai/plugin`
4. Verify tool is enabled in agent's `tools` config
5. Check for name collisions (filename becomes tool name)

### Skill Not Loading

**Symptoms**: Agent can't find or load a skill

**Solutions**:
1. Verify `SKILL.md` is in ALL CAPS
2. Check frontmatter includes required `name` and `description`
3. Ensure skill name matches directory name
4. Validate skill name follows naming convention (lowercase, hyphens)
5. Check permissions - skills with `deny` are hidden from agents
6. Verify skill name is unique across all locations

### Permissions Not Working

**Symptoms**: Agent performs actions it shouldn't, or is blocked incorrectly

**Solutions**:
1. Check permission rule order (last matching rule wins)
2. Verify syntax: `"allow"`, `"ask"`, or `"deny"` (strings, not booleans)
3. For granular rules, ensure patterns match the tool input format
4. Check that agent permissions override global permissions as expected
5. Validate that tools are enabled in `tools` config before checking permissions

### Agent Ignoring Permissions

**Symptoms**: Agent performs denied actions

**Solutions**:
1. Verify permissions are configured for the specific agent
2. Check that agent has the permission field set (it may be inheriting global permissions)
3. Ensure tool names match exactly (case-sensitive)
4. For task permissions, verify subagent names match the pattern
5. Review agent logs for permission evaluation

### Agent Behavior Issues

**Symptoms**: Agent doesn't follow instructions or behaves unexpectedly

**Solutions**:
1. Check temperature setting (too high may cause inconsistent behavior)
2. Review system prompt for clarity and specificity
3. Verify `maxSteps` isn't too low (agent may be forced to respond prematurely)
4. Ensure tools the agent needs are enabled
5. Check if permissions are blocking required actions
6. Consider using a more capable model if reasoning seems weak

### Performance Problems

**Symptoms**: Slow responses, high token usage

**Solutions**:
1. Check enabled MCP servers (some add significant context)
2. Reduce `maxSteps` to limit iterations
3. Use a faster model for planning, switch to capable model for implementation
4. Minimize tool outputs that return large data
5. Consider disabling unused tools to reduce tool descriptions in context

---

## Quick Reference

### Agent Configuration (Markdown)

```markdown
---
description: [Required: Brief description]
mode: primary | subagent | all
model: provider/model-id
temperature: 0.0-1.0
maxSteps: number
hidden: false | true
tools:
  toolName: true | false
permission:
  toolName: allow | ask | deny
  toolName:
    pattern: allow | ask | deny
---

[System prompt content...]
```

### Tool Template

```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Tool description",
  args: {
    param: tool.schema.type().describe("Parameter description"),
  },
  async execute(args, context) {
    // Implementation
    return result
  },
})
```

### Skill Template

```markdown
---
name: skill-name
description: Skill description
license: MIT | Apache-2.0 | ...
metadata:
  key: value
---

[Skill content...]
```

### Permission Template

```json
{
  "permission": {
    "toolName": "allow | ask | deny",
    "toolName": {
      "pattern": "allow | ask | deny",
      "*": "allow | ask | deny"
    }
  }
}
```

---

## Summary

This guide covers the complete lifecycle of designing OpenCode.ai agents:

1. **Understand the architecture**: Primary vs subagent, client/server, event-driven
2. **Choose the right type**: Mode, tools, permissions based on requirements
3. **Implement**: JSON or Markdown configuration, custom tools, skills
4. **Secure**: Apply principle of least privilege with granular permissions
5. **Test**: Verify behavior matches expectations
6. **Iterate**: Refine based on usage and feedback

When generating a new agent based on user requirements:
1. Analyze the requirements thoroughly
2. Choose agent type (primary/subagent)
3. Determine necessary tools
4. Set appropriate permissions
5. Write clear system prompt
6. Create any custom tools needed
7. Add relevant skills
8. Test and validate

Remember: **Security first, clarity second, functionality third**.
