# Contributing to Gemma 4 Offline SWE Agent

Thank you for your interest in contributing to the **Gemma 4 Offline SWE Agent**! This project is developed for air-gapped, competition, and enterprise environments with strict security, performance, and reproducibility constraints.

---

## 🔒 Foundational Principles & Hard Constraints

Every modification and contribution MUST strictly adhere to these 4 non-negotiable architectural tenets:

1. **Air-Gapped & Offline Discipline**:
   - Zero outbound or inbound network calls (`requests`, `urllib`, `socket`, `aiohttp`, etc.).
   - No external APIs, cloud services, or authentication tokens.
   - All code, prompt logic, and evaluations must execute 100% locally.

2. **Google ADK Schema Compliance**:
   - Root agent configuration (`agent.yaml`) must conform to the competition agent schema.
   - Exactly 9 registered tools: `run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`, `search_similar_code`, `get_code_neighbors`, `get_code_subgraph`.
   - Never add forbidden keys (`sub_agents`, `adapters`, `lora`, `agent_fn`, `agent_class`).

3. **Lean Submission Footprint (<100 KB)**:
   - `submission.zip` must package only verified agent configurations, system prompts, and sampling configs.
   - Developer tools, test harnesses, benchmark data, and cache files must NEVER leak into the submission archive.

4. **Security & Host Containment**:
   - All file operations must pass through `PathJail` (strictly bounded within the workspace or approved scratch paths).
   - Shell commands must be sanitized via `CommandSanitizer`.
   - All proposed diffs must pass the `PatchSecurityAuditor` SAST static analysis.

---

## 🛠️ Development Setup

### Local Setup
```bash
# 1. Clone repository
git clone https://github.com/Tao-coder502/Gemma4-Offline-SWE-Agent.git
cd Gemma4-Offline-SWE-Agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install core and development dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### Docker Container Setup
```bash
# Build container image
docker build -t gemma4-agent .

# Run test suite inside container
docker run --rm gemma4-agent pytest tests/
```

---

## 🧪 Testing & Verification Protocol

Before submitting a Pull Request, you MUST execute the following validation steps:

```bash
# 1. Run full unit and integration test suite (11+ checks):
pytest tests/ -v

# 2. Run clean-room submission compliance audit (81 checks):
python tools/verify_clean_submission.py

# 3. Verify the one-click live demonstration:
python demo.py

# 4. (Optional) Run the benchmark evaluation harness:
python evaluate.py --summary
```

---

## 📋 Pull Request Checklist

Please ensure your PR meets all criteria:
- [ ] Code is formatted cleanly and has no syntax errors (`python -m py_compile ...`).
- [ ] All unit and integration tests pass (`pytest tests/`).
- [ ] Clean-room compliance verifier passes 100% with zero warnings or failures (`python tools/verify_clean_submission.py`).
- [ ] No hardcoded tokens, API keys, passwords, or absolute system paths are introduced.
- [ ] Any new tools or features include corresponding tests in `tests/`.
- [ ] Documentation (`README.md` or `docs/`) is updated accordingly.
