# Installs SlashV fonts for the current user (no admin rights needed).
# Info logs by default. Pass -VerboseLogs for detail output.
# Pass -Family AvantGarde|Adventor|All (default All).
[CmdletBinding()]
param(
    [switch]$VerboseLogs,
    [ValidateSet("All", "AvantGarde", "Adventor")]
    [string]$Family = "All"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param(
        [string]$Level = "INFO",
        [Parameter(Mandatory = $true)][string]$Message
    )
    if ($Level -eq "DEBUG" -and -not $VerboseLogs) { return }

    $label = switch ($Level) {
        "DEBUG"   { "detail " }
        "INFO"    { "info   " }
        "WARNING" { "note   " }
        "ERROR"   { "problem" }
        default   { $Level.ToLower().PadRight(7) }
    }
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Output ("{0}  {1}  {2}" -f $ts, $label, $Message)
}

$root = Split-Path $PSScriptRoot -Parent
$outDir = Join-Path $root "fonts"
$fontDir = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
$regKey = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"

Write-Log -Level INFO -Message "Welcome - installing SlashV fonts for your Windows user account."
Write-Log -Level INFO -Message ("Family filter: {0}" -f $Family)
Write-Log -Level INFO -Message ("Project folder: {0}" -f $root)
Write-Log -Level INFO -Message ("Looking for built fonts in: {0}" -f $outDir)
Write-Log -Level INFO -Message ("They will be installed to: {0}" -f $fontDir)

if (-not (Test-Path $outDir)) {
    Write-Log -Level ERROR -Message "I can't find the fonts/ folder. Build first with build.bat (or: python scripts/make_font.py)."
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
Write-Log -Level INFO -Message ("Planning to install {0} font file(s)." -f $fonts.Count)

New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
if (-not (Test-Path $regKey)) {
    Write-Log -Level WARNING -Message ("Creating the Windows fonts registry key: {0}" -f $regKey)
    New-Item -Path $regKey -Force | Out-Null
}

Write-Log -Level INFO -Message "Loading Windows font helper functions..."
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
    Write-Log -Level DEBUG -Message "Windows helpers are ready."
} catch {
    if ($_.Exception.Message -match "already exists") {
        Write-Log -Level DEBUG -Message "Windows helpers were already loaded - reusing them."
    } else {
        Write-Log -Level ERROR -Message ("Couldn't load Windows font helpers: {0}" -f $_.Exception.Message)
        throw
    }
}

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$ok = 0
$fail = 0

foreach ($f in $fonts) {
    Write-Log -Level INFO -Message ("-- Installing {0} --" -f $f.File)
    $src = Join-Path $outDir $f.File
    if (-not (Test-Path $src)) {
        Write-Log -Level ERROR -Message ("Missing {0}. Build fonts first (build.bat), then try again." -f $src)
        $fail++
        continue
    }
    $srcInfo = Get-Item $src
    Write-Log -Level INFO -Message ("Found it ({0} bytes)." -f $srcInfo.Length)

    $dst = Join-Path $fontDir $f.File
    if (Test-Path $dst) {
        try {
            $r = [FontInstallNative]::RemoveFontResourceW($dst)
            Write-Log -Level DEBUG -Message ("Freed the previous install (Windows returned {0})." -f $r)
        } catch {
            Write-Log -Level WARNING -Message ("Couldn't unload the old file (may be in use): {0}" -f $_.Exception.Message)
        }
    }

    $installedPath = $dst
    try {
        Copy-Item -Path $src -Destination $dst -Force
        Write-Log -Level INFO -Message "Copied into your Windows fonts folder."
    } catch {
        Write-Log -Level WARNING -Message ("The usual filename is locked ({0}). Trying a versioned name instead..." -f $_.Exception.Message)
        $versioned = [IO.Path]::GetFileNameWithoutExtension($f.File) + "-" + $stamp + ".ttf"
        $installedPath = Join-Path $fontDir $versioned
        try {
            Copy-Item -Path $src -Destination $installedPath -Force
            Write-Log -Level INFO -Message ("Installed under the alternate name {0}." -f $versioned)
        } catch {
            Write-Log -Level ERROR -Message ("Still couldn't copy the file: {0}" -f $_.Exception.Message)
            $fail++
            continue
        }
    }

    try {
        $added = [FontInstallNative]::AddFontResourceW($installedPath)
        if ($added -gt 0) {
            Write-Log -Level INFO -Message ("Registered with Windows (added {0})." -f $added)
        } else {
            Write-Log -Level WARNING -Message "Windows reported 0 fonts added - registry is updated, but you may need to restart apps (or sign out) to see it."
        }
    } catch {
        Write-Log -Level ERROR -Message ("Couldn't register the font with Windows: {0}" -f $_.Exception.Message)
        $fail++
        continue
    }

    try {
        New-ItemProperty -Path $regKey -Name $f.Name -Value $installedPath -PropertyType String -Force | Out-Null
        Write-Log -Level INFO -Message ("Registry entry written as '{0}'." -f $f.Name)
    } catch {
        Write-Log -Level ERROR -Message ("Couldn't update the registry: {0}" -f $_.Exception.Message)
        $fail++
        continue
    }

    Write-Log -Level INFO -Message ("Done - '{0}' is installed." -f $f.Name)
    $ok++
}

Write-Log -Level INFO -Message "Letting open programs know the font list changed..."
try {
    $res = [IntPtr]::Zero
    [void][FontInstallNative]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [IntPtr]::Zero, [IntPtr]::Zero, 2, 1000, [ref]$res)
} catch {
    Write-Log -Level WARNING -Message ("Couldn't broadcast the font change (not fatal): {0}" -f $_.Exception.Message)
}

Write-Log -Level INFO -Message "-- Summary --"
Write-Log -Level INFO -Message ("Installed successfully: {0}" -f $ok)
Write-Log -Level INFO -Message ("Could not install:      {0}" -f $fail)
Write-Log -Level INFO -Message "Families: AvantGarde SlashV, Adventor SlashV"
if ($fail -eq 0) {
    Write-Log -Level INFO -Message "Tip: restart Word / Illustrator / Figma if they were already open."
} else {
    Write-Log -Level ERROR -Message "Some fonts didn't install. Scroll up for the details, then try again."
}
if ($fail -gt 0) { exit 1 }
