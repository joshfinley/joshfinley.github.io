+++
title = "ETW Research Scripts"
date = 2025-03-30 00:05:28
draft = false
+++

Another brief post sharing some quick-hack PowerShell scripts I've created while researching ETW on Windows 11 and following along in Matt Hand's [*Evading EDR*](https://nostarch.com/evading-edr).

## The Scripts

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
    $foundGuids = @{}
    
    # Process file in chunks
    $stream = [System.IO.File]::OpenRead($filePath)
    $buffer = New-Object byte[] 4MB
    $totalBytesRead = 0
    
    try {
        $overlap = 36  # GUID can be up to 36 chars, need to keep this overlap between chunks
        $carryover = ""
        
        while ($true) {
            $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
            if ($bytesRead -eq 0) { break }
            
            # Convert bytes to ASCII replacing non-printable chars with spaces
            $text = -join ($buffer[0..($bytesRead-1)] | ForEach-Object {
                if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { ' ' }
            })
            
            # Combine with carryover from previous chunk
            $textToSearch = $carryover + $text
            
            # Find GUIDs
            $matches = [regex]::Matches($textToSearch, $regex)
            foreach ($match in $matches) {
                $matchOffset = $totalBytesRead - $carryover.Length + $match.Index
                # Only add if we haven't seen this GUID before
                if (-not $foundGuids.ContainsKey($match.Value)) {
                    $foundGuids[$match.Value] = $matchOffset
                }
            }
            
            # Save overlap for next chunk
            $carryover = $text.Substring([Math]::Max(0, $text.Length - $overlap))
            $totalBytesRead += $bytesRead
            
            # Force garbage collection periodically
            [System.GC]::Collect()
        }
    }
    finally {
        $stream.Close()
        $stream.Dispose()
    }
    
    # Return results as objects
    $results = @()
    foreach ($guid in $foundGuids.Keys | Sort-Object) {
        $results += [PSCustomObject]@{
            GUID = $guid
            Offset = $foundGuids[$guid]
        }
    }
    
    return $results
}

function Is-ETWProviderGUID($guid) {
    # Cache ETW provider GUIDs to avoid repeated lookups
    if (-not (Test-Path variable:global:ETWProviderCache)) {
        $global:ETWProviderCache = @{}
        
        # Pre-populate cache with all ETW providers - do this only once
        Write-Host "Caching ETW providers..." -ForegroundColor Yellow
        $providers = logman query providers
        foreach ($provider in $providers) {
            if ($provider -match '(?:\{|\()([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})(?:\}|\))') {
                $global:ETWProviderCache[$Matches[1].ToLower()] = $true
            }
        }
    }
    
    $cleanedGuid = $guid.Trim('{}()').ToLower()
    return $global:ETWProviderCache.ContainsKey($cleanedGuid)
}

# Main script
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
    
    # Process each file individually and clean up after
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
            Write-Host "
            Write-Host "$guid " -ForegroundColor $defaultColor -NoNewline
            Write-Host "at offset $offsetHex" -ForegroundColor $defaultColor
        }
    }
    
    # Force cleanup after each file
    Remove-Variable guidResults -ErrorAction SilentlyContinue
    [System.GC]::Collect()
}

# Clean up the cache at the end
Remove-Variable -Name ETWProviderCache -Scope Global -ErrorAction SilentlyContinue
```

An example run through System32 shows some successful matches:
```
...
Scanning: C:\Windows\System32\windowsperformancerecordercontrol.dll
  [ETW] {36b6f488-aad7-48c2-afe3-d4ec2c8b46fa} at offset 0x00133A87
  [ETW] 0a002690-3839-4e3a-b3b6-96d8df868d99 at offset 0x0010B2FD
  [ETW] 0CC157B3-CF07-4FC2-91EE-31AC92E05FE1 at offset 0x000FFC97
  [ETW] 245f975d-909d-49ed-b8f9-9a75691d6b6b at offset 0x0010BC4D
  [ETW] 315a8872-923e-4ea2-9889-33cd4754bf64 at offset 0x00105CB4
  [ETW] 36b6f488-aad7-48c2-afe3-d4ec2c8b46fa at offset 0x000FE24B
  [ETW] 486A5C7C-11CC-46C5-9DE7-43DFE0BB57C1 at offset 0x0010C7D5
  [ETW] 48D445A8-2F64-4D49-B093-A5774D8DC531 at offset 0x00101902
  [ETW] 4bd2826e-54a1-4ba9-bf63-92b73ea1ac4a at offset 0x00108FE4
  [ETW] 531a35ab-63ce-4bcf-aa98-f88c7a89e455 at offset 0x0010BA6B
  [ETW] 5412704e-b2e1-4624-8ffd-55777b8f7373 at offset 0x0010551B
  [ETW] 57277741-3638-4A4B-BDBA-0AC6E45DA56C at offset 0x000FE80C
  [ETW] 59819d0a-adaf-46b2-8d7c-990bc39c7c15 at offset 0x00105727
  [ETW] 5c8bb950-959e-4309-8908-67961a1205d5 at offset 0x00108D24
  [ETW] 7426a56b-e2d5-4b30-bdef-b31815c1a74a at offset 0x0010593F
  [ETW] 751ef305-6c6e-4fed-b847-02ef79d26aef at offset 0x0010B38C
  [ETW] 7E7D3382-023C-43cb-95D2-6F0CA6D70381 at offset 0x0010B1A7
  ... And many more
...
```

Just based on this DLL name, it makes sense that we would see some ETW provider GUIDs inside it.

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

## Update 3/31/2025: ELAM Driver Signing Helper

I've also created a utility to automate the test-ELAM signing stage in ELAM driver development tasks. While not directly related to ETW, this script may prove useful to someone else, as it is suitable for integration with Visual Studio test signing builds.

Updates to this script can be found on [GitHub](https://gist.github.com/joshfinley/50d30bfb5e547c1f5fa891ec603e90b3).

```bat
@echo off
REM ============================================================
REM Simple ELAM Driver Signing Script
REM ============================================================
REM   To integrate with Visual Studio, update your SDK version
REM   paths below, disable default test signing, and add
REM   a post-build event to your build configurations in the
REM   driver VCXPROJ. For example, near the top, add:
REM
REM   <PropertyGroup>
REM     <SignMode>Off</SignMode>
REM   </PropertyGroup>
REM
REM   And then in your build configurations, add the post-build action:
REM
REM   <PostBuildEvent>
REM     <Command>call "$(ProjectDir)CustomDriverSigning.bat" "$(TargetPath)"</Command>
REM     <Message>Custom signing driver with makecert and signtool</Message>
REM   </PostBuildEvent>

setlocal enabledelayedexpansion
echo Starting ELAM driver signing process...

REM Set paths to tools based on your system
set MAKECERT_PATH="C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x86\MakeCert.exe"
set SIGNTOOL_PATH="C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x86\signtool.exe"

REM Set certificate details
set CERT_NAME=DevElamCert
set CERT_SUBJECT_NAME="CN=DevElamCert"
set CERT_STORE=PrivateCertStore
set CERT_FILENAME=%cd%\DevElamCert.cer

REM Parse command line arguments
set DRIVER_FILE=%1
if "%DRIVER_FILE%"=="" (
    echo Error: Please specify the driver file to sign.
    echo Usage: %0 [driver_file]
    exit /b 1
)

echo Driver file: %DRIVER_FILE%

REM Create ELAM certificate
echo Creating ELAM certificate...
%MAKECERT_PATH% -a SHA256 -r -pe -ss %CERT_STORE% -n %CERT_SUBJECT_NAME% -sr currentuser -eku 1.3.6.1.4.1.311.61.4.1,1.3.6.1.5.5.7.3.3 %CERT_FILENAME%

if errorlevel 1 (
    echo Error: Failed to create certificate.
    echo Make sure you're running this script as Administrator.
    exit /b 1
)

echo Certificate created successfully at %CERT_FILENAME%

REM Sign the driver
echo Signing ELAM driver...
%SIGNTOOL_PATH% sign /fd SHA256 /a /ph /s %CERT_STORE% /n %CERT_NAME% /td sha256 /tr http://timestamp.digicert.com %DRIVER_FILE%

if errorlevel 1 (
    echo Error: Failed to sign the driver.
    echo Trying alternative timestamp server...
    %SIGNTOOL_PATH% sign /fd SHA256 /a /ph /s %CERT_STORE% /n %CERT_NAME% /td sha256 /tr http://timestamp.sectigo.com %DRIVER_FILE%
    
    if errorlevel 1 (
        echo Error: All signing attempts failed.
        exit /b 1
    )
)

echo ELAM driver signed successfully.
echo.
echo IMPORTANT: To use this custom-signed ELAM driver:
echo 1. Enable test signing mode: bcdedit /set testsigning on
echo 2. You may need to add the certificate to your trusted root certificates
echo 3. Restart your computer
echo.

exit /b 0
```