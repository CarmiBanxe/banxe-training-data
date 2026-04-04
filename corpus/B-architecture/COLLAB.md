# COLLAB.md v3.0 — Single-Terminal Synergy

**Pattern:** Claude Code + Qoder CLI automatic collaboration via MCP  
**Repository:** `~/developer/` (and all downstream projects)  
**Version:** 3.0 | 2026-04-03

---

## User Principle (The Only Rule You Need)

```bash
cd ~/project          # Any project directory
claude
```

**That is all.**

No manual `qodercli` commands. No separate terminals. No coordination overhead.

---

## What Happens Under The Hood

```
YOU → CLAUDE (designs/reviews) → QODER via MCP (implements) → CLAUDE (verifies) → YOU
```

### Automatic flow

1. **You start Claude** in project directory
2. **Claude reads** project instructions (AGENTS.md, CLAUDE.md, etc.)
3. **Claude delegates** execution to Qoder via MCP automatically
4. **Qoder executes** within repository boundaries
5. **Claude reviews** results and presents unified outcome

### You see

- Clean result presentation
- What was analyzed
- What was changed
- What was verified
- What risks remain

### You don't see

- MCP protocol details
- Qoder invocation commands
- Internal agent coordination
- Context loading complexity

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   USER TERMINAL                      │
│                                                      │
│  cd ~/project                                        │
│  claude                                              │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │        Claude Code (coordinator)             │   │
│  │  • Reads project context                     │   │
│  │  • Designs architecture                      │   │
│  │  • Reviews output                            │   │
│  │  • Presents results                          │   │
│  └──────────────────────────────────────────────┘   │
│                        ↓ MCP call                    │
│  ┌──────────────────────────────────────────────┐   │
│  │        Qoder CLI mcp-server (executor)       │   │
│  │  • Loaded automatically from settings.json   │   │
│  │  • Reads .qoder/config.yml                   │   │
│  │  • Executes commands                         │   │
│  │  • Edits files                               │   │
│  │  • Runs tests                                │   │
│  └──────────────────────────────────────────────┘   │
│                        ↓                             │
│  Repository (isolated scope)                        │
└─────────────────────────────────────────────────────┘
```

---

## Configuration (Pre-Integrated)

### Global MCP setup (~/.claude/settings.json)

```json
{
  "skipDangerousModePermissionPrompt": true,
  "mcpServers": {
    "qoder": {
      "type": "stdio",
      "command": "qodercli",
      "args": ["mcp-server"]
    }
  }
}
```

**Why stdio:** Lowest latency, no network overhead, direct process communication.

### Project Qoder config ({project}/.qoder/config.yml)

```yaml
# WSL optimizations
wsl:
  watchPolling: true
  watchInterval: 1000
  maxConcurrentOperations: 2

# Auto-load context
mcp:
  loadContext: true
  contextPaths:
    - "AGENTS.md"
    - ".qoder/context.md"
    - "CLAUDE.md"
    - "docs/COLLAB.md"
```

---

## Instruction Hierarchy

Agents follow instructions in this priority order:

1. **Explicit user instruction** (highest authority)
2. **Repository-level contracts**:
   - `CLAUDE.md` — project context
   - `.qoder/context.md` — Qoder execution contract
   - `AGENTS.md` — agent instructions
   - `COLLAB.md` — this file
   - `COMPLIANCE_ARCH.md` — compliance invariants
3. **Global defaults**: `~/.claude/CLAUDE.md`

**Rule:** Closer to working directory = higher priority.

---

## Project Isolation (Canon)

### Hard invariant

**One terminal = one project = one repository.**

Agents must NEVER:
- Read files outside current git root
- Mix configs/secrets/context across repositories
- Reuse artifacts from another project implicitly

**Violation is a critical error, not a style issue.**

### Cross-project work

If you explicitly request cross-project work:

```
"Copy the sanctions_check.py module from vibe-coding to guiyon"
```

Then agents must:
1. Confirm both repository names
2. Work sequentially (one at a time)
3. Maintain strict separation during each operation

---

## When Collaboration is Visible

Normally collaboration is invisible. It becomes visible only when:

### Debugging failures

```
Qoder failed to execute: pytest src/compliance/test_phase15.py
Exit code: 1
Stderr: ModuleNotFoundError: No module named 'clickhouse_driver'

Possible causes:
1. Virtualenv not activated
2. Dependency missing from requirements.txt
3. Test path incorrect

Recommendation: Run manually to diagnose:
  cd /home/mmber/vibe-coding
  source venv/bin/activate
  pytest src/compliance/test_phase15.py -v
```

### Review disagreements

```
Qoder suggests: Change minMatch from 0.80 to 0.90
Analysis: This violates COMPLIANCE_ARCH.md invariant #3

Invariant #3 states:
  "Watchman minMatch: 0.80 (Jaro-Winkler)"

Change requires:
- MLRO approval
- Regression test on known cases
- Documentation update

Recommendation: Keep 0.80 unless explicit business decision made.
```

---

## Compliance-Sensitive Operations

If working in `src/compliance/` (vibe-coding):

### Mandatory pre-flight

**Before ANY change:** read `COMPLIANCE_ARCH.md` fully.

### Protected invariants

Cannot be changed without explicit user approval:

1. **Canonical key:** `(jurisdiction_code, registration_number)`
2. **OFAC RSS:** dead since 31 Jan 2025 — HTML scrape only
3. **Watchman minMatch:** 0.80 (Jaro-Winkler)
4. **ClickHouse TTL:** 5 YEAR (FCA MLR 2017 requirement)
5. **Jube AGPLv3:** internal use only
6. **GUIYON (port 18794):** categorically excluded from Banxe

### Decision thresholds (read-only by default)

| Score | Decision | Action |
|-------|----------|--------|
| ≥ 70 | REJECT | Block + SAR |
| 40–69 | HOLD | Enhanced due diligence |
| < 40 | APPROVE | Pass |
| sanctions_hit = true | REJECT (always) | SAR mandatory |

**SAR auto-threshold:** composite ≥ 85 OR sanctions_hit

---

## Testing Requirements

Before marking task complete:

| Change type | Required tests |
|-------------|----------------|
| Business logic | Unit tests + integration smoke test |
| Compliance logic | Regression tests on known cases |
| API endpoints | Endpoint smoke test + schema validation |
| Infrastructure | Deploy script dry-run + health check |
| Documentation | Link check + build verification |

### Test commands (vibe-coding example)

```bash
# Phase 15 unit tests (pytest, no network)
pytest src/compliance/test_phase15.py -v

# Phase 1-13 integration (custom asyncio runner)
python3 src/compliance/test_suite.py

# General repo tests
pytest tests/ -v
```

---

## HITL Checkpoints (Human In The Loop)

| Risk level | Confidence required | Approval |
|------------|---------------------|----------|
| LOW | >90% | Auto-approve |
| MEDIUM | Any | Human required |
| HIGH | Any | Human + Compliance officer |

All decisions logged to ClickHouse for FCA audit trail.

---

## Troubleshooting

### Problem: Qoder not responding

**Symptoms:** Claude waits indefinitely, no output

**Diagnosis:**
```bash
ps aux | grep qodercli
# Should show: qodercli mcp-server
```

**Fix:**
```bash
# Kill stuck process
pkill -f "qodercli mcp-server"

# Restart Claude session
exit
cd ~/project
claude
```

### Problem: Context not loading

**Symptoms:** Qoder ignores project rules

**Check:**
```bash
cat ~/.qoder/config.yml
ls -la AGENTS.md .qoder/context.md CLAUDE.md
```

**Verify loaded:**
```bash
bash scripts/check-agent-instructions.sh
```

### Problem: WSL hangs

**Symptoms:** Filesystem watchers freeze, high CPU

**Fix:** Ensure WSL optimizations in ~/.qoder/config.yml:
```yaml
wsl:
  watchPolling: true
  maxConcurrentOperations: 2
  disableInterop: true
```

---

## Performance Tips

### For large operations

```bash
# Parallel workers (when appropriate)
# Claude will automatically use worktrees for independent tasks
```

### For slow operations

- Increase timeout in config
- Run in background with status checks
- Break into smaller chunks

---

## Security Considerations

### Never commit

- `.env` files
- Secrets or API keys
- Credentials or tokens
- Private certificates

### Use environment variables

```bash
export BANXE_API_KEY="..."
export CLICKHOUSE_PASSWORD="..."
```

### Token scoping (if using API)

```bash
export QODER_REPO_SCOPE=/home/mmber/vibe-coding
export QODER_ALLOWED_COMMANDS="edit,run_test,read_file"
```

---

## Summary Checklist

Before starting work in any project:

- [ ] Global MCP config exists (`~/.claude/settings.json`)
- [ ] Qoder configured as stdio server
- [ ] Project has AGENTS.md or CLAUDE.md
- [ ] Project has .qoder/context.md (optional but recommended)
- [ ] WSL optimizations enabled (if on WSL)
- [ ] Compliance arch read (if touching src/compliance/)

After completing work:

- [ ] Changes committed to canonical repository
- [ ] Tests pass
- [ ] Documentation updated (if needed)
- [ ] No secrets committed
- [ ] Clear commit messages

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-XX | Two-terminal workflow (deprecated) |
| 2.0 | 2026-04-02 | Manual coordination pattern |
| 3.0 | 2026-04-03 | Single-terminal automatic synergy (current) |

---

## Related Documents

- `AGENTS.md` — Executable agent instructions
- `.qoder/context.md` — Qoder execution contract
- `docs/MCP-BEST-PRACTICES.md` — MCP server configuration guide
- `src/compliance/COMPLIANCE_ARCH.md` — Compliance invariants (if applicable)
