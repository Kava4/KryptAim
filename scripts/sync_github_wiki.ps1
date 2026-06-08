# Sync local wiki/ markdown to GitHub Wiki (.wiki.git)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$WikiSrc = Join-Path $Root "wiki"
$CloneDir = Join-Path $Root ".wiki-clone"
$Remote = "https://github.com/AimSyncCore/AimSync.wiki.git"

Write-Host "AimSync GitHub Wiki sync" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $WikiSrc)) {
    throw "Missing folder: $WikiSrc"
}

$probe = git ls-remote $Remote 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Wiki repo not initialized - creating Home page..." -ForegroundColor Yellow
    python (Join-Path $Root "scripts\bootstrap_github_wiki.py")
    if ($LASTEXITCODE -ne 0) { throw "Wiki bootstrap failed" }
    Start-Sleep -Seconds 2
}

if (Test-Path $CloneDir) {
    Remove-Item -Recurse -Force $CloneDir
}

Write-Host "Cloning $Remote ..."
git clone $Remote $CloneDir
if ($LASTEXITCODE -ne 0) { throw "Wiki clone failed" }

Get-ChildItem $CloneDir -Filter "*.md" | Remove-Item -Force
Copy-Item (Join-Path $WikiSrc "*.md") $CloneDir -Exclude "WIKI-UPLOAD.md"

Push-Location $CloneDir
git add -A
$status = git status --porcelain
if ($status) {
    git commit -m "Sync wiki from repo wiki/ folder"
    git push origin HEAD
    Write-Host "Wiki updated: https://github.com/AimSyncCore/AimSync/wiki" -ForegroundColor Green
} else {
    Write-Host "Wiki already up to date." -ForegroundColor Green
}
Pop-Location
