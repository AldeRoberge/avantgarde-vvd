# Installs the customized fonts for the current user (no admin rights needed).
$ErrorActionPreference = "Stop"

$root    = Split-Path $PSScriptRoot -Parent
$outDir  = Join-Path $root "fonts"
$fontDir = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
$regKey  = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"

New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
if (-not (Test-Path $regKey)) { New-Item -Path $regKey -Force | Out-Null }

$fonts = @(
    @{ File = "AvantGardeSlashV-Book.ttf";        Name = "AvantGarde SlashV Book (TrueType)" },
    @{ File = "AvantGardeSlashV-Demi.ttf";        Name = "AvantGarde SlashV Demi (TrueType)" },
    @{ File = "AvantGardeSlashV-DemiOblique.ttf"; Name = "AvantGarde SlashV Demi Oblique (TrueType)" }
)

Add-Type -Name Gdi -Namespace Win -MemberDefinition @"
[DllImport("gdi32.dll", CharSet=CharSet.Unicode)]
public static extern int AddFontResourceW(string lpFileName);
[DllImport("gdi32.dll", CharSet=CharSet.Unicode)]
public static extern bool RemoveFontResourceW(string lpFileName);
[DllImport("user32.dll", CharSet=CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);
"@

$stamp = Get-Date -Format "yyyyMMddHHmmss"

foreach ($f in $fonts) {
    $src = Join-Path $outDir $f.File
    if (-not (Test-Path $src)) {
        throw "Missing font file: $src  (run: python scripts/make_font.py)"
    }
    $dst = Join-Path $fontDir $f.File

    if (Test-Path $dst) { [void][Win.Gdi]::RemoveFontResourceW($dst) }

    try {
        Copy-Item -Path $src -Destination $dst -Force
    }
    catch {
        # Windows keeps installed font files locked. Rather than fail, write a
        # fresh file and point the registry entry at it; the stale file is
        # ignored once nothing references it.
        $versioned = [IO.Path]::GetFileNameWithoutExtension($f.File) + "-$stamp.ttf"
        $dst = Join-Path $fontDir $versioned
        Copy-Item -Path $src -Destination $dst -Force
        Write-Output "  (previous file locked, installed as $versioned)"
    }

    [void][Win.Gdi]::AddFontResourceW($dst)
    New-ItemProperty -Path $regKey -Name $f.Name -Value $dst -PropertyType String -Force | Out-Null

    Write-Output "installed: $($f.Name)"
}

# Tell running apps the font list changed (WM_FONTCHANGE to all top-level windows)
$res = [IntPtr]::Zero
[void][Win.Gdi]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [IntPtr]::Zero, [IntPtr]::Zero, 2, 1000, [ref]$res)

Write-Output ""
Write-Output "Done. Family name: 'AvantGarde SlashV'"
