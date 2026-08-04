# Installs SlashV fonts for the current user (no admin rights needed).
# Verbose by default. Pass -Quiet for less output.
# Pass -Family AvantGarde|Adventor|All (default All).
[CmdletBinding()]
param(
    [switch]$Quiet,
    [ValidateSet("All", "AvantGarde", "Adventor")]
    [string]$Family = "All"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param(
        [string]$Level = "INFO",
        [Parameter(Mandatory = $true)][string]$Message
    )
    if ($Quiet -and $Level -eq "DEBUG") { return }
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Output ("{0}  {1,-7}  {2}" -f $ts, $Level, $Message)
}

$root = Split-Path $PSScriptRoot -Parent
$outDir = Join-Path $root "fonts"
$fontDir = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
$regKey = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"

Write-Log -Level INFO -Message "avantgarde-vvd / install_fonts.ps1"
Write-Log -Level INFO -Message ("Family filter = {0}" -f $Family)
Write-Log -Level INFO -Message ("repo root   = {0}" -f $root)
Write-Log -Level INFO -Message ("fonts dir   = {0}" -f $outDir)
Write-Log -Level INFO -Message ("install dir = {0}" -f $fontDir)

if (-not (Test-Path $outDir)) {
    Write-Log -Level ERROR -Message "fonts/ directory missing - run: python scripts/make_font.py"
    throw "Missing fonts directory"
}

$allFonts = @(
    @{ File = "AvantGardeSlashV-Book.ttf";        Name = "AvantGarde SlashV Book (TrueType)";         Group = "AvantGarde" },
    @{ File = "AvantGardeSlashV-Demi.ttf";        Name = "AvantGarde SlashV Demi (TrueType)";         Group = "AvantGarde" },
    @{ File = "AvantGardeSlashV-DemiOblique.ttf"; Name = "AvantGarde SlashV Demi Oblique (TrueType)"; Group = "AvantGarde" },
    @{ File = "AdventorSlashV-Regular.ttf";       Name = "Adventor SlashV Regular (TrueType)";        Group = "Adventor" },
    @{ File = "AdventorSlashV-Bold.ttf";          Name = "Adventor SlashV Bold (TrueType)";           Group = "Adventor" },
    @{ File = "AdventorSlashV-Italic.ttf";        Name = "Adventor SlashV Italic (TrueType)";         Group = "Adventor" },
    @{ File = "AdventorSlashV-BoldItalic.ttf";    Name = "Adventor SlashV Bold Italic (TrueType)";    Group = "Adventor" }
)

if ($Family -eq "All") {
    $fonts = $allFonts
} else {
    $fonts = @($allFonts | Where-Object { $_.Group -eq $Family })
}
Write-Log -Level INFO -Message ("will install {0} font(s)" -f $fonts.Count)

New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
if (-not (Test-Path $regKey)) {
    Write-Log -Level WARNING -Message ("creating registry key {0}" -f $regKey)
    New-Item -Path $regKey -Force | Out-Null
}

Write-Log -Level INFO -Message "loading Win32 font APIs..."
$cs = @'
using System;
using System.Runtime.InteropServices;
public static class FontInstallNative {
  [DllImport("gdi32.dll", CharSet=CharSet.Unicode)]
  public static extern int AddFontResourceW(string lpFileName);
  [DllImport("gdi32.dll", CharSet=CharSet.Unicode)]
  public static extern bool RemoveFontResourceW(string lpFileName);
  [DllImport("user32.dll", CharSet=CharSet.Auto)]
  public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);
}
'@
try {
    Add-Type -TypeDefinition $cs -ErrorAction Stop | Out-Null
    Write-Log -Level DEBUG -Message "FontInstallNative type loaded"
} catch {
    if ($_.Exception.Message -match "already exists") {
        Write-Log -Level DEBUG -Message "FontInstallNative already loaded"
    } else {
        Write-Log -Level ERROR -Message ("failed to load Win32 APIs: {0}" -f $_.Exception.Message)
        throw
    }
}

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$ok = 0
$fail = 0

foreach ($f in $fonts) {
    Write-Log -Level INFO -Message ("----- install {0} -----" -f $f.File)
    $src = Join-Path $outDir $f.File
    if (-not (Test-Path $src)) {
        Write-Log -Level ERROR -Message ("Missing: {0}  (run: python scripts/make_font.py)" -f $src)
        $fail++
        continue
    }
    $srcInfo = Get-Item $src
    Write-Log -Level INFO -Message ("source OK ({0} bytes)" -f $srcInfo.Length)

    $dst = Join-Path $fontDir $f.File
    if (Test-Path $dst) {
        try {
            $r = [FontInstallNative]::RemoveFontResourceW($dst)
            Write-Log -Level DEBUG -Message ("RemoveFontResourceW -> {0}" -f $r)
        } catch {
            Write-Log -Level WARNING -Message ("RemoveFontResourceW: {0}" -f $_.Exception.Message)
        }
    }

    $installedPath = $dst
    try {
        Copy-Item -Path $src -Destination $dst -Force
        Write-Log -Level INFO -Message "copied to standard filename"
    } catch {
        Write-Log -Level WARNING -Message ("locked ({0}) - trying versioned filename" -f $_.Exception.Message)
        $versioned = [IO.Path]::GetFileNameWithoutExtension($f.File) + "-" + $stamp + ".ttf"
        $installedPath = Join-Path $fontDir $versioned
        try {
            Copy-Item -Path $src -Destination $installedPath -Force
            Write-Log -Level INFO -Message ("installed as {0}" -f $versioned)
        } catch {
            Write-Log -Level ERROR -Message ("fallback failed: {0}" -f $_.Exception.Message)
            $fail++
            continue
        }
    }

    try {
        $added = [FontInstallNative]::AddFontResourceW($installedPath)
        Write-Log -Level INFO -Message ("AddFontResourceW -> {0}" -f $added)
    } catch {
        Write-Log -Level ERROR -Message ("AddFontResourceW: {0}" -f $_.Exception.Message)
        $fail++
        continue
    }

    try {
        New-ItemProperty -Path $regKey -Name $f.Name -Value $installedPath -PropertyType String -Force | Out-Null
        Write-Log -Level INFO -Message ("registry: {0}" -f $f.Name)
    } catch {
        Write-Log -Level ERROR -Message ("registry: {0}" -f $_.Exception.Message)
        $fail++
        continue
    }

    Write-Log -Level INFO -Message ("installed: {0}" -f $f.Name)
    $ok++
}

Write-Log -Level INFO -Message "broadcasting WM_FONTCHANGE..."
try {
    $res = [IntPtr]::Zero
    [void][FontInstallNative]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [IntPtr]::Zero, [IntPtr]::Zero, 2, 1000, [ref]$res)
} catch {
    Write-Log -Level WARNING -Message ("WM_FONTCHANGE: {0}" -f $_.Exception.Message)
}

Write-Log -Level INFO -Message "========== summary =========="
Write-Log -Level INFO -Message ("installed OK : {0}" -f $ok)
Write-Log -Level INFO -Message ("failed       : {0}" -f $fail)
Write-Log -Level INFO -Message "families     : AvantGarde SlashV, Adventor SlashV"
if ($fail -gt 0) { exit 1 }
