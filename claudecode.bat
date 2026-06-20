@echo off
setlocal

REM =========================
REM Kiro + Claude Sonnet
REM =========================

REM API ключ OmniRoute / Kiro gateway
set "ANTHROPIC_API_KEY=sk-379b8f0e2c2697bc-93dd38-c2639cd5"

REM gateway
set "ANTHROPIC_BASE_URL=http://localhost:20128/v1"

REM 🔥 МОДЕЛЬ (вот здесь всё решается)
set "ANTHROPIC_MODEL=kr/claude-haiku-4.5"

REM отключение экспериментальных фич
set "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1"

echo Starting Kiro with Claude Sonnet 4.6...

claude

endlocal
pause