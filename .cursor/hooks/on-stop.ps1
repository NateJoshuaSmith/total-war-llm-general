# Cursor "stop" hook: runs when a Cursor agent run ends.
# Writes .cursor/agent-done.json so Claude Code knows exactly when Cursor finished.
# Must never fail loudly: Cursor waits on this script.

$ErrorActionPreference = 'SilentlyContinue'

$raw = [Console]::In.ReadToEnd()
$evt = $null
if ($raw) { $evt = $raw | ConvertFrom-Json }

$marker = [ordered]@{
    status          = if ($evt) { $evt.status } else { 'unknown' }
    conversation_id = if ($evt) { $evt.conversation_id } else { $null }
    branch          = (git rev-parse --abbrev-ref HEAD 2>$null)
    head            = (git rev-parse HEAD 2>$null)
    dirty           = [bool](git status --porcelain 2>$null)
    finished_at     = (Get-Date).ToUniversalTime().ToString('o')
}

$marker | ConvertTo-Json | Set-Content -Path '.cursor/agent-done.json' -Encoding utf8

# Empty output: no follow-up message for Cursor.
'{}'
