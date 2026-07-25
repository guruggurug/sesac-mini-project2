param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$portableNode = Join-Path $projectRoot ".tools\node-v24.18.0-win-x64"

if (Test-Path -LiteralPath (Join-Path $portableNode "node.exe")) {
    $env:Path = "$portableNode;$env:Path"
}

$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    throw "Node.js 24 LTS와 npm 11 이상이 필요합니다."
}

Push-Location $projectRoot
try {
    if ($Install) {
        & $npmCommand.Source ci
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    & $npmCommand.Source run css:build
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
