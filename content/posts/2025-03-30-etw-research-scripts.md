+++
title = "ETW Research Scripts"
date = 2025-03-30 00:05:28
draft = false
+++

Another brief post sharing some quick-hack PowerShell scripts I've created while researching ETW on Windows 11 and following along in Matt Hand's [*Evading EDR*](https://nostarch.com/evading-edr).

The scripts are:

- [`Get-PossibleEtwRefs.ps1`](https://gist.github.com/joshfinley/2c6f9b2d0b81580b292dabadd6ccb622): A dumbed-down version of [FindETWProviderImage](https://github.com/matterpreter/FindETWProviderImage), useful for hunting potential ETW provider GUID references in files and directories.
- [`Get-EtwProviderAces.ps1`](https://gist.github.com/joshfinley/566f6a3e9d3989880a2ae9894185bc35): Attempt to obtain ACE's associated with a provider.

Both of these scripts are quick experiments but have proved useful in my testing. Improvements could be made to increase accuracy and performance. Additionally, for `Get-PossibleEtwRefs.ps1`, it would likely not be so difficult to leverage SDKs for IDA/Ghidra/Binja to compute cross-references to the identified GUIDs and see if any are near any relevant ETW functions, allowing us to easily associate the reference with Provider / Controller / Consumer code (similar to what is demonstrated manually in *Evading EDR* ch. 8), or do similar analysis.

Note: The versions here won't see any updates. I will do that on the respective GitHub gists.

### Get-PossibleEtwRefs
```PowerShell
# Get-PossibleEtwRefs.ps1
#
# Search for GUIDs in a target file or directory and check
# if it might be an ETW provider GUID using logman.
#
# Inspired by chapter 8 of "Evading EDR" by Matt Hand.
#
# Not fast but easy to deploy and use.

param (
    [string]$Path
)

function Get-GUIDsFromFile($filePath) {
    $regex = '[{(]?[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}[)}]?'
    $bytes = [System.IO.File]::ReadAllBytes($filePath)
    $ascii = -join ($bytes | ForEach-Object {
        if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { ' ' }
    })
    
    $matches = [regex]::Matches($ascii, $regex)
    $results = @()
    
    foreach ($match in $matches) {
        # Calculate the file offset by finding the byte position of the GUID
        $offset = $match.Index
        $results += [PSCustomObject]@{
            GUID = $match.Value
            Offset = $offset
        }
    }
    
    return $results | Sort-Object GUID -Unique
}

function Is-ETWProviderGUID($guid) {
    $providers = logman query providers | Select-String -Pattern $guid
    return $providers -ne $null
}

# Check if the path exists
if (-not (Test-Path $Path)) {
    Write-Error "Path not found: $Path"
    exit 1
}

$files = if ((Get-Item $Path).PSIsContainer) {
    Get-ChildItem -Path $Path -Recurse -File
} else {
    Get-Item $Path
}

# Define colors for highlighting
$etwColor = "Green"
$unknownColor = "Gray"
$defaultColor = (Get-Host).UI.RawUI.ForegroundColor

foreach ($file in $files) {
    Write-Host "`nScanning: $($file.FullName)" -ForegroundColor Cyan
    $guidResults = Get-GUIDsFromFile $file.FullName
    
    foreach ($result in $guidResults) {
        $guid = $result.GUID
        $offset = $result.Offset
        $cleaned = $guid.Trim('{}()')
        
        $offsetHex = "0x{0:X8}" -f $offset
        
        if (Is-ETWProviderGUID $cleaned) {
            Write-Host "  [ETW] " -ForegroundColor $etwColor -NoNewline
            Write-Host "$guid " -ForegroundColor $etwColor -NoNewline
            Write-Host "at offset $offsetHex" -ForegroundColor $etwColor
        } else {
            Write-Host "  [UNK] " -ForegroundColor $unknownColor -NoNewline
            Write-Host "$guid " -ForegroundColor $defaultColor -NoNewline
            Write-Host "at offset $offsetHex" -ForegroundColor $defaultColor
        }
    }
}
```

### Get-EtwProviderAces
```PowerShell
# Get-EtwProviderAces.ps1
#
# Helper script to get SDDL/ACES for ETW Providers
# Inspired by / draws from Chapter 8 of "Evading EDR" by Matt Hand
param (
    [Parameter(Mandatory = $false)]
    [string]$ProviderName,

    [Parameter(Mandatory = $false)]
    [Guid]$Guid
)

if (-not $ProviderName -and -not $Guid) {
    Write-Error "You must specify either -ProviderName or -Guid."
    exit 1
}

if ($ProviderName) {
    $providerInfo = wevtutil gp "$ProviderName" 2>$null
    if (-not $providerInfo) {
        Write-Error "Could not retrieve provider info."
        exit 1
    }

    $guidLine = $providerInfo | Where-Object { $_ -match '^GUID:' }
    if (-not $guidLine) {
        Write-Error "GUID not found in provider info."
        exit 1
    }

    $guid = $guidLine -replace '^GUID:\s*', ''
    $guid = $guid.Trim('{}').ToUpper()
} else {
    $guid = $Guid.ToString().ToUpper()
}

try {
    $sdTable = Get-ItemProperty -Path HKLM:\System\CurrentControlSet\Control\WMI\Security
    $binarySD = $sdTable.$guid
    if (-not $binarySD) {
        throw "No binary security descriptor found for GUID: {$guid}"
    }

    $sddl = ([wmiclass]"Win32_SecurityDescriptorHelper").BinarySDToSDDL($binarySD).SDDL
    $decoded = ConvertFrom-SddlString -Sddl $sddl

    if ($ProviderName) {
        Write-Output "Provider Name: $ProviderName"
    }
    Write-Output "GUID: {$guid}"
    Write-Output "SDDL: $sddl"
    Write-Output "Decoded:"
    $decoded
} catch {
    Write-Error $_
}
```

