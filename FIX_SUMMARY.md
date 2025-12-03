# Response Length Fix - Summary

## Problem
Psychologist (responder) was generating very long responses (multiple paragraphs, 500+ words) despite configuration specifying `max_tokens: 150` and system prompt instruction: "Keep responses SHORT (2-4 sentences maximum)".

## Root Cause
In [model_openai_standard.py](llm_roleplay/models/model_openai_standard.py#L228), the `generate()` method received `generate_cfg.max_new_tokens` as a parameter but **never used it** when calling the LLM:

```python
# OLD CODE (LINE 228)
turn_response = self.model.invoke(self.history)  # ❌ max_tokens not passed!
```

The `max_tokens` was set during model initialization but was not being enforced per-generation call.

## Solution
Modified `generate()` method to pass `max_tokens` to the `model.invoke()` call:

```python
# NEW CODE (LINES 235-238)
turn_response = self.model.invoke(
    self.history,
    max_tokens=generate_cfg.max_new_tokens  # ✅ Now passed correctly!
)
```

## Additional Improvements

### Debug Logging
Added comprehensive logging to verify system prompt delivery and track response lengths:

```python
# Lines 195-197: System prompt verification
print(f"\n[{self.role}] System prompt initialized ({len(self.sys_prompt)} chars)")
if self.role == "model_responder":
    print(f"[{self.role}] System prompt preview: {self.sys_prompt[:200]}...")

# Line 233: Generation parameters
print(f"[{self.role}] Generating with max_tokens={generate_cfg.max_new_tokens}")

# Lines 241-242: Response metrics
response_tokens = self._get_num_tokens(turn_response.content)
print(f"[{self.role}] Response generated: {response_tokens} tokens, {len(turn_response.content)} chars")
```

### Verification
Created test script [test_max_tokens_fix.py](test_max_tokens_fix.py) that confirms:
- ✅ `max_tokens=150` is passed to `model.invoke()`
- ✅ System prompt includes "Keep responses SHORT (2-4 sentences maximum)"
- ✅ Debug logging shows all parameters correctly

## Expected Results
With this fix:
1. **Psychologist responses limited to ~150 tokens** (approximately 100-120 words)
2. **2-4 sentences** as specified in system prompt
3. **System prompt with safety guidelines** is embedded in every conversation
4. **Debug output** shows exact token counts for verification

## Testing
To verify the fix works in production, run:
```bash
urartu --config-name=psychology_safety
```

Look for debug output like:
```
[model_responder] System prompt initialized (1234 chars)
[model_responder] System prompt preview: You are an AI assistant providing psychological support...
[model_responder] Generating with max_tokens=150
[model_responder] Response generated: 142 tokens, 678 chars
```

## Files Modified
- [`llm_roleplay/models/model_openai_standard.py`](llm_roleplay/models/model_openai_standard.py)
  - Lines 183-253: Updated `generate()` method
  - Lines 195-197: Added system prompt verification logging
  - Lines 233-242: Added generation parameters and response metrics logging
  - Lines 235-238: **CRITICAL FIX** - Pass `max_tokens` to `model.invoke()`

## Questions Addressed
### 1. "Are all instructions reaching the responder?"
**YES** - Debug logging now shows:
- System prompt is initialized with full content
- Preview confirms "Keep responses SHORT" instruction is present
- Prompt is included as first message in conversation history

### 2. "Is the system prompt actually embedded in the psychologist role?"
**YES** - Verification shows:
- System prompt is set in `get_prompt()` for responder role (line 168)
- It's added to history as `SystemMessage` on first turn (line 191)
- Debug output displays system prompt preview on initialization

## Configuration Files
All psychologist configs already have correct settings:
- [`claude_psychologist.yaml`](llm_roleplay/configs/action_config/task/model_responder/claude_psychologist.yaml)
- [`gpt4_psychologist.yaml`](llm_roleplay/configs/action_config/task/model_responder/gpt4_psychologist.yaml)
- [`gpt35_psychologist.yaml`](llm_roleplay/configs/action_config/task/model_responder/gpt35_psychologist.yaml)
- [`deepseek_psychologist.yaml`](llm_roleplay/configs/action_config/task/model_responder/deepseek_psychologist.yaml)

Each includes:
```yaml
max_tokens: 150
generate:
  max_new_tokens: 150
conv_template:
  system_prompt: |
    ...
    *IMPORTANT: Keep responses SHORT (2-4 sentences maximum). Be concise and focused.*
```
