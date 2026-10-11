param([string]$Executable)
$ErrorActionPreference = 'Stop'

function Confirm-BlenderExecutable([string]$Candidate) {
    if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
        throw "Blender executable does not exist: $Candidate"
    }
    $resolvedExecutable = (Resolve-Path -LiteralPath $Candidate).Path
    $versionOutput = & $resolvedExecutable --version 2>&1
    if ($LASTEXITCODE -ne 0 -or (($versionOutput -join "`n") -notmatch '^Blender \d')) {
        throw "Executable did not identify itself as Blender: $resolvedExecutable"
    }
    return $resolvedExecutable
}

if ($Executable) { Confirm-BlenderExecutable $Executable; exit 0 }
if ($env:BLENDER_EXECUTABLE) { Confirm-BlenderExecutable $env:BLENDER_EXECUTABLE; exit 0 }
$pathCommand = Get-Command blender.exe -ErrorAction SilentlyContinue
if ($pathCommand) { Confirm-BlenderExecutable $pathCommand.Source; exit 0 }

$codexRuntimeHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$portableRuntimeRoot = Join-Path $codexRuntimeHome 'plugins\runtimes\character-studio'
$standardRuntimeRoots = @($portableRuntimeRoot)
if ($env:ProgramFiles) { $standardRuntimeRoots += (Join-Path $env:ProgramFiles 'Blender Foundation') }
if ($env:LOCALAPPDATA) { $standardRuntimeRoots += (Join-Path $env:LOCALAPPDATA 'Programs\Blender Foundation') }
foreach ($runtimeRoot in $standardRuntimeRoots) {
    if (-not (Test-Path -LiteralPath $runtimeRoot -PathType Container)) { continue }
    $runtimeCandidates = Get-ChildItem -LiteralPath $runtimeRoot -Filter blender.exe -File -Recurse |
        Sort-Object LastWriteTime -Descending
    foreach ($runtimeCandidate in $runtimeCandidates) {
        Confirm-BlenderExecutable $runtimeCandidate.FullName
        exit 0
    }
}
throw 'Blender was not found. Set BLENDER_EXECUTABLE to an installed or portable Blender executable.'
