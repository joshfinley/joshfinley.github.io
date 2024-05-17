+++

title = "Notes - UEFI Development and Bootkits"
date = 2022-05-22 00:05:28 

+++

## Foundational Resources

- [VisualUefi](https://github.com/ionescu007/VisualUefi) from Alex Ionescu
- [DreamBoot](https://github.com/quarkslab/dreamboot/tree/master/QuarksUBootkit) bootkit
- [UEFI-Bootkit](https://github.com/ajkhoury/UEFI-Bootkit) 
- [MoonBounce](https://securelist.com/moonbounce-the-dark-side-of-uefi-firmware/105468/) bootkit
- [MoonBounce Technical Writeup](https://media.kasperskycontenthub.com/wp-content/uploads/sites/43/2022/01/19115831/MoonBounce_technical-details_eng.pdf)
- [Hook ExitBootServices](https://wikileaks.org/ciav7p1/cms/page_36896783.html)
- [NCC Group - Deploying Rootkits from EFI](https://research.nccgroup.com/wp-content/uploads/2020/07/BH-VEGAS-07-Heasman.pdf)
- [EDK II Module Writers Guide](https://edk2-docs.gitbook.io/edk-ii-module-writer-s-guide/8_dxe_drivers_non-uefi_drivers/810_dxe_smm_driver)

## Setting Up a Development Environment

While the EDK is a massive project with a difficult and complex set up process, Alex Ionescu has released a repository with everything one needs to get set up quickly in Visual Studio. Link: [VisualUefi](https://github.com/ionescu007/VisualUefi)).

```
git clone https://github.com/ionescu007/VisualUefi.git
git submodules init
git submodule update --init --recursive
# then build in EDK II solution
``` 

## Moonbounce Synposis (UEFI Component)

Notes from kaspersky writeup linked above.

### DriverMapping Shellcode Hook

1. Restore function prologue bytes of `AllocatePool`
2. Call `AllocatePool` and write `Driver Mapping Shellcode` to the buffer
3. Restore original arguments and pass to `AllocatePool`

### Main Algorithm

1. Load driver during `DXE` phase
2. Hook first five bytes `AllocatePool` to allocate and assign buffer for/with `Driver Mapping Shellcod`
3. Hook `ExitBootServices` to hook `OslArchTransferToKernel`
4. Allow execution up to `OslArchTransferToKernel` hook
5. Locate `ntoskrnl.exe` by reading  `IDENTRY64` interrupt service routine `IdtBase` (Interrupt Descriptor Table) field from `KPCR`. This handler is in the `ntosrknl` address space and can be used to search backward in memory for the DOS MZ header, and then resolve the addresses of its export `ExRegisterCallback`, `ExAllocatePool`, and `MmMapIoSpace`
6. Hook `ExAllocatePool` to call a shellcode buffer copied into `ntoskrnl.exe`'s relocation directory
7. Allow execution to first call of `ExAllocatePool` hook, which calls `MmMapIoSpace` to allocate space for mapping driver mapping shellcode contained by the buffer created in step to by the `AllocatePool` hook and execute this shellcode

### Driver Loader

passed:
- Pointer to buffer with original `ExAllocatePool` bytes
- Base of `ntoskrnl.exe`
- Pointer to `ExAllocatePool`

algorithm:
1. unhooks `ExAllocatePool`
2. resolves `RtlInitAnsiString`, `RtlAnsiStringToUnicodeString`, and `MmGetSystemRoutineAddress`
3. Allocates pool space for the driver
4. Maps and copies headers and sections
5. Performs relocations
6. Resolves imports
7. Passes control to driver

### Remainder of Attack Chain

From there, the driver registers a callback to `PsSetLoadImageNotifyRoutine` to faciliate injection of usermode malware into the a Windows service.

## Synopsis of ExitBootServices

From Vault7

- `ExitBootServices` is the point where UEFI boot services phase ends and control is transferred to the operating system
  - Terminates boot services
  - Reclaims boot service memory
- `ExitBootServices` pointer is found in `EFI_BOOT_SERVICES` table
- UEFI driver can simply store this pointer and replace it with the hook
- Must call `GetMemoryMap` before calling real `ExitBootServices`

Exmaple code:

```
extern EFI_BOOT_SERVICES *gBS;
EFI_EXIT_BOOT_SERVICES     gOrigExitBootServices;

EFI_STATUS
EFIAPI
ExitBootServicesHook(IN EFI_HANDLE ImageHandle, IN UINTN MapKey){

	/* <hook related fun> */
	/* Do fun hook-related stuff here */
	/* </hook-related fun> */

	/* Fix the pointer in the boot services table */
	/* If you don't do this, sometimes your hook method will be called repeatedly, which you don't want */
    gBS->ExitBootServices = gOrigExitBootServices;

    /* Get the memory map */
    UINTN MemoryMapSize;
    EFI_MEMORY_DESCRIPTOR *MemoryMap;
    UINTN LocalMapKey;
    UINTN DescriptorSize;
    UINT32 DescriptorVersion;
    MemoryMap = NULL;
    MemoryMapSize = 0;
    
	
    do {  
        Status = gBS->GetMemoryMap(&MemoryMapSize, MemoryMap, &LocalMapKey, &DescriptorSize,&DescriptorVersion);
        if (Status == EFI_BUFFER_TOO_SMALL){
            MemoryMap = AllocatePool(MemoryMapSize + 1);
            Status = gBS->GetMemoryMap(&MemoryMapSize, MemoryMap, &LocalMapKey, &DescriptorSize,&DescriptorVersion);      
        } else {
            /* Status is likely success - let the while() statement check success */
        }
        DbgPrint(L"This time through the memory map loop, status = %r\n",Status);
    
    } while (Status != EFI_SUCCESS);

    return gOrigExitBootServices(ImageHandle,LocalMapKey);

}
EFI_STATUS
EFIAPI
HookDriverMain(IN EFI_HANDLE ImageHandle, IN EFI_SYSTEM_TABLE *SystemTable){

    /* Store off the original pointer and replace it with your own */
    gOrigExitBootServices = gBS->ExitBootServices;
    gBS->ExitBootServices = ExitBootServicesHook;

	/* It's hooked! Return EFI_SUCCESS so your driver stays in memory */
    return EFI_SUCCESS;
}
```

## NCC Group - Deploying Rootkits from EFI

- First phase of EFI framework 
  - Handling platform restart, creating temporary memory store, act as root-of-trust, pass control to PEI (pre EFI)
- Pre EFI
  - Low basic low-level hardware related modules
  - Invokes DXE phase
- Other ways to subvery loading of the Operating System - DreamBoot hooks/shims a boot service, but other possibilities include:
  - Modifying ACPI tables
  - Loading and SMM driver (x86-64) (god mode)
    - SMM drivers remain available after `ExitBootServices`
    - SMM stands for `System Management Mode` aka ring -2
    - SMM is a "key to defending the (Windows) hypervisor" - [microsoft](https://www.microsoft.com/security/blog/2020/11/12/system-management-mode-deep-dive-how-smm-isolation-hardens-the-platform/)
    - Hardware breakpoints not useable in SMM
    - SMM locked at end of DXE?
    - See [this blog post](http://blog.cr4.sh/2015/07/building-reliable-smm-backdoor-for-uefi.html) for more
    
  - Hooking other boot/runtime services
    - ATA Passthrough

## More on SMM

- SMM phase is supported by DXE drivers implementing UEFI protocols (`EFI_SMM_ACCESS2_PROTOCL`, `EFI_SMM_CONTROL2_PROTOCOL`, `EFI_SMM_BASE2_PROTOCOL`, `EFI_SMM_COMMUNICATION_PROTOCOL`, etc.)
- Of note `EFI_SMM_CPU_IO2_PROTOCOL` 'provides CPU I/O and memory access for SMM Code. `EFI_SMM_PCI_ROOT_BRIDGE_IO_PROTOCOL` 'provides basic memory, I/O, PCI configuration and DMA interfaces that are used to abstract accesses to PCI controllers...'. In System Management System Table

### SMM Related Resources

#### Tools 
- [UEFITool](https://github.com/LongSoft/UEFITool) - extracting, modifying UEFI firmware images

- [HostileEducation UDOO Bolt](https://www.hostile.education/utk-web/UDOO-BOLT-C4000000.108.utk)

#### Malware

- [DeityBounce](https://resources.infosecinstitute.com/topic/nsa-bios-backdoor-god-mode-malware-deitybounce/) - amazing SMM 

#### Vulnerabilities

- [SMM Callout Vulnerability](https://www.tomshardware.com/news/amd-apus-affected-by-smm-callout-privilege-escalation-security-vulnerability)

#### Blog Posts

- [Walmart Laptop SMM Analysis](https://nstarke.github.io/2021/11/24/onn-laptop-smi-analysis.html)
- [SMM Bug Hunting](https://www.sentinelone.com/labs/zen-and-the-art-of-smm-bug-hunting-finding-mitigating-and-detecting-uefi-vulnerabilities/)
- [Phrack - A Real SMM Rootkit](http://phrack.org/issues/66/11.html)

#### Papers and Technical Documentation

- [White Paper - A Tour Beyond BIOS Secure SMM Communication in the EFI Developer Kit II](https://raw.githubusercontent.com/tianocore-docs/Docs/master/White_Papers/A_Tour_Beyond_BIOS_Secure_SMM_Communication.pdf)

## Source for Driver Manual Mapper from EFI

https://github.com/btbd/umap/blob/master/boot/main.c

- Hooks Windows Loader
  - Hooks ImgArchStartBootApplication
  - Hooks BlImgAllocateImageBuffer
  - OslFwpKernelSetupPhase1


## Key Defenses and Detection Vectors

### `EFI_BOOT_SERVICES` Hooks

### Unsigned EFI Allocated Kernel Drivers

### Malicious SMM Drivers

SMM Isolation is a three part policy for protecting SMM and is OEM dependent. The chip is resonsible for reporting compliance to the isolation policy to the OS. On AMD, a UEFI driver `SMM Sup