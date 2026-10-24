$ErrorActionPreference = 'Stop'
$modernRoot = $PSScriptRoot
$repositoryRoot = Split-Path $modernRoot -Parent
$portableTools = Join-Path $modernRoot '.tools\w64devkit\bin'
if (Test-Path -LiteralPath $portableTools) {
    $env:PATH = $portableTools + ';' + $env:PATH
}
$workspace = if ($args.Count -gt 0) { $args[0] } else { Join-Path $modernRoot 'examples\hello' }
$executable = Join-Path $modernRoot 'dist\DevCppModern\DevCppModern.exe'
if (Test-Path -LiteralPath $executable) {
    & $executable $workspace
} else {
    $python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        throw 'Run the installation commands in modern/README.md first.'
    }
    & $python -m devcpp.app $workspace
}
