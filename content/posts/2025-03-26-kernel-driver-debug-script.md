+++
title = "Kernel Driver Debug Helper"
date = 2025-03-29 00:05:28
draft = false
+++

Brief post.

Just sharing here a script I've been using to assist in Windows 11 kernel driver testing.

The script provides quick and easy deployment of kernel drivers to accessible Hyper-V virtual machines.

Requirements:
- Hyper-V
- Available Windows VM with enabled guest integrations

Features:
- Automated copy and start of driver on target VM 
- Default inclusion of available PDB to the target and local symbols cache
- Suitable for quick experiments.

Out!

```PowerShell
# Deploy-DriverToVM.ps1
# Script to deploy debug drivers to Win11 Debug VM

param (
    [string]$VMName = "win-11-dbg",
    [string]$DriverPath = ".\x64\Debug\EtwResearchDriver\EtwResearchDriver.sys",
    [string]$VMDestPath = "C:\Drivers\EtwResearchDriver\",
    [string]$symbolPath = "C:\Symbols",
    [switch]$InstallDriver = $true,
    [System.Management.Automation.PSCredential]$Credential = $null
)

# Verify the driver file exists
if (-not (Test-Path $DriverPath)) {
    Write-Error "Driver file not found at: $DriverPath"
    exit 1
}

# Find corresponding PDB file
$driverFileName = Split-Path $DriverPath -Leaf
$driverBaseName = [System.IO.Path]::GetFileNameWithoutExtension($driverFileName)
$pdbPath = Join-Path (Split-Path $DriverPath -Parent | Split-Path -Parent) "$driverBaseName.pdb"

$hasPdb = Test-Path $pdbPath
if ($hasPdb) {
    Write-Host "Found matching PDB file: $pdbPath"
} else {
    Write-Host "No matching PDB file found at: $pdbPath" -ForegroundColor Yellow
}

# Copy the PDB to local symbol directory
if (-not (Test-Path $symbolPath)) {
    Write-Error "Local symbol cache does not exist at C:\Symbols"
} elseif ($hasPdb) {
    Write-Host "Copying $pdbPath to $symbolPath"
    Copy-Item $pdbPath $symbolPath
}

# Check if VM exists
$vm = Get-VM -Name $VMName -ErrorAction SilentlyContinue
if (-not $vm) {
    Write-Error "VM '$VMName' not found. Please check the VM name."
    exit 1
}

# Check if VM is running
if ($vm.State -ne "Running") {
    Write-Host "Starting VM '$VMName'..."
    Start-VM -Name $VMName
    
    # Wait for VM to boot up
    Write-Host "Waiting for VM to boot up..."
    Start-Sleep -Seconds 30
}

# Get credentials if not provided
if (-not $Credential) {
    $Credential = Get-Credential -Message "Enter credentials for VM access"
}

# Create destination directory on VM if it doesn't exist
Write-Host "Creating destination directory on VM..."
Invoke-Command -VMName $VMName -Credential $Credential -ScriptBlock {
    param($destPath)
    if (-not (Test-Path $destPath)) {
        New-Item -Path $destPath -ItemType Directory -Force | Out-Null
    }
} -ArgumentList $VMDestPath

# Stop the driver service if it's already running
Write-Host "Checking for existing driver service..."
Invoke-Command -VMName $VMName -Credential $Credential -ScriptBlock {
    param($driverBaseName)
    $service = Get-Service -Name $driverBaseName -ErrorAction SilentlyContinue
    
    if ($service) {
        Write-Host "Stopping existing driver service..."
        Stop-Service -Name $driverBaseName -Force
        Start-Sleep -Seconds 2  # Give time for driver to fully unload
    }
} -ArgumentList $driverBaseName

# Copy driver file to VM
Write-Host "Copying driver to VM..."
try {
    Copy-VMFile -VMName $VMName -SourcePath $DriverPath -DestinationPath "$VMDestPath\$driverFileName" -CreateFullPath -FileSource Host -Force
}
catch {
    Write-Error "Failed to copy driver file: $_"
    exit 1
}

# Copy PDB file to VM if it exists
if ($hasPdb) {
    $pdbFileName = Split-Path $pdbPath -Leaf
    Write-Host "Copying PDB file to VM..."
    Copy-VMFile -VMName $VMName -SourcePath $pdbPath -DestinationPath "$VMDestPath\$pdbFileName" -CreateFullPath -FileSource Host -Force
    
    # Copy PDB to the symbols path as well (if not already in a symbol path)
    Invoke-Command -VMName $VMName -Credential $Credential -ScriptBlock {
        param($destPath, $pdbFileName)
        
        # Create symbol folder if it doesn't exist
        $symbolPath = "C:\Symbols"
        if (-not (Test-Path $symbolPath)) {
            New-Item -Path $symbolPath -ItemType Directory -Force | Out-Null
        }
        
        # Only copy if not already in the symbols directory
        if (-not ($destPath -like "*\Symbols\*")) {
            $sourcePdb = Join-Path $destPath $pdbFileName
            $destPdb = Join-Path $symbolPath $pdbFileName
            Copy-Item -Path $sourcePdb -Destination $destPdb -Force
            Write-Host "PDB also copied to symbol path: $symbolPath"
        }
    } -ArgumentList $VMDestPath, $pdbFileName
}

# Install/start driver if specified
if ($InstallDriver) {
    Write-Host "Installing/starting driver on VM..."
    Invoke-Command -VMName $VMName -Credential $Credential -ScriptBlock {
        param($destPath, $driverFileName, $driverBaseName)
        
        $driverFullPath = Join-Path $destPath $driverFileName
        $service = Get-Service -Name $driverBaseName -ErrorAction SilentlyContinue
        
        if ($service) {
            # Update existing service
            Write-Host "Updating existing driver service..."
            & sc.exe config $driverBaseName binPath= $driverFullPath
        } else {
            # Create new service
            Write-Host "Creating new driver service..."
            & sc.exe create $driverBaseName type= kernel binPath= $driverFullPath start= demand
        }
        
        # Start the driver
        Write-Host "Starting driver service..."
        & sc.exe start $driverBaseName
        
        # Verify installation
        $newService = Get-Service -Name $driverBaseName -ErrorAction SilentlyContinue
        if ($newService) {
            Write-Host "Driver service status: $($newService.Status)"
        } else {
            Write-Error "Failed to install driver service."
        }
    } -ArgumentList $VMDestPath, $driverFileName, $driverBaseName
}

Write-Host "Deployment complete!"
```