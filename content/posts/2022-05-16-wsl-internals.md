+++

title = "Notes - Windows Subsystem for Linux Internals"
date = 2022-05-16 00:05:28 

+++

# WSL Version 1

The WSL system is implemented in three major components:

- LxssManager service
- lxss.sys driver
- lxcore.sys driver

![LxssManager Service Properties](/lxssmanager-props.png)

The drivers are termed 'pico provider' drivers, and processes invoked using WSL are 'pico' processes

## Pico Processes

The Windows Pico Process concept is explained [here](/archives/87f65010a51e9805856c0552287e894484002a5c06264fc6a4f1715a6662a03c_pico-process-overview.html). The gist is that Windows Pico processes are distinct from regular processes. They are either supported by provider drivers rather than the Windows kernel, or just empty processes. This leaves many of the implementation details of the process management (such as virtual memory) up to the provider driver.

Minimal process - empty user mode process. Like [memfuck](https://winternl.com/memfuck/) without having to unload everything and no management.

Pico process - Process managed by provider driver for management rather than directly by Windows Kernel.

### System Calls from Pico Processes

Pico processes with provider drivers are unique in that system calls are dispatched to the driver rather than making it to regular system call handlers. 
This leads me to several questions, with my attempts at answering them below:

- what is the provider driver responsible for? e.g. a system call with valid parameters for an ordinary native API is issued. What happens?
- are Pico Provider drivers `syscall tables` protected by patchguard?
- how does the registration process work?
- at what stage of the System Call dispatching process does the check occur?
- what facilities exist for third party drivers (i.e. not ntoskrnl related and not lxss/lxcore) to register callbacks for handlers registed by Pico Providers?


### Pico Process System Calls - What Must the Provider Implement?

As stated in the WSL blog on an [Overview Pico Processes](/archives/87f65010a51e9805856c0552287e894484002a5c06264fc6a4f1715a6662a03c_pico-process-overview.html), the provider is responsible for all Pico process interfaces with the kernel. It seems that anything needed from the kernel must be explicitly provided by the provider.

### Pico Process System Calls - Protected by Patch Guard?

[According to Alex Ionescu](/archives/50105ffdbddfc7677c760e08af91325b0814fbaa4988da52afb559508a314710_WSL-BlueHat-Final.pdf.bin), yes, Pico Providers register their handlers with PatchGuard.


### Pico Provider Registration - Registration Process

Pico Provider regisration is very locked down. In addition to only supporting one Pico Provider at a time, Windows requires Pico Providers to be loaded before any other third-party drivers. As "core" drivers, they must be signed by a Microsoft Signer Certificate and Windows Componenet EKU. 

It does not seem that Microsoft provides any documentation for writing other Pico Providers. In addition, there seems to be only one notable (to my knowledge) example of a custom Pico Provider driver.

### Pico Process System Calls - Dispatching to Pico Providers

Answering the question of where pico process system call is dispatched to its provider driver in the dispatching lifecycle involves delving into the Windows kernel. Upon syscall, the instruction pointer is set to an existing value in the LSTAR MSR, which itself is set upon boot. This is the address of the function `nt!KiSystemCallShadow`(`nt!KisystemCall` on spectre-unmitigated versions). 

![LSTAR pointer as seen in WinDBG](/widbg-lstar-syscall.png)

Next in the workflow is `nt!KiSystemServiceUser`.  Here, `nt!_KPCR` (`gs:00h`), `nt!_KPCRB` (`gs:180h`), and `nt!_KTHREAD` (`gs:188h`) are leveraged to determine the correct course of action. Early in the flow of `nt!KiSystemServiceUser`, a byte comparison against `nt!_KTHREAD+0x03` (technically `nt!_DISPATCHER_HEADER+0x03`) is performed. The first field in `nt!_KTHREAD` is `nt!_DISPATCHER_HEADER`, a data structure with a plethora of uses and versions in use across the Windows kernel. In the context of a thread object, the byte at offset `nt!_DISPATCHER_HEADER+0x03` is read interpreted as a bit field with the name `DebugActive` which has flags to distinguish the current thread context as a minimal process or a pico process. 

During `nt!KiSystemServiceUser`, if `KTHREAD.Header.DebugActive.Minimal` or `KTHREAD.Header.DebugActive.AltSyscall` are set, `PSAltSystemCallDispatch` will be called, which itself will call either `PsAltSystemCallHandlers` or `PsRegisterAltSystemCallHandler`, depending on whether the `Minimal` or `AltSyscall` are set, respectively.

```
typedef struct _DEBUG_FIELDS {
    BOOLEAN ActiveDR7 : 1;
    BOOLEAN Instrumented : 1;
    BOOLEAN Minimal : 1;
    BOOLEAN Reserved4 : 2;
    BOOLEAN AltSyscall : 1;
    BOOLEAN UmsScheduled : 1;
    BOOLEAN UmsPrimary : 1;
} DEBUG_FIELDS;

KiSystemServiceUser(...)
{
    KTHREAD CurrentThread = KeGetCurrentThread();
    ...
    if (CurrentThread.DebugActive)
    {
        if (CurrentThread.DebugActive.ActiveDR7 || CurrentThread.DebugActive.Instrumented)
        {
            KiSaveDebugRegisterState(...);
        }

        if (CurrentThread.DebugActive.Minimal && CurrentThread.AltSyscall)
        {
            if (PsAltSystemCallDispatch(...) == TRUE)
            {
                ...
            }
        }
    }
    ...
}

PUNK PsAltSystemCallDyspatch(...)
{
    FARPROC _PsAltSystemCallRoutine;
    KTHREAD CurrentThread = KeGetCurrentThread();

    if (CurrentThread->Header.DebugActive.Minimal)
    {
        _PsAltSystemCallRoutine = PsAltSystemCallHandlers;
    } else if (CurrentThread->Header.DebugActive.AltSyscall)
    {
        _PsAltSystemCallRoutine = PsRegisterAltSystemCallHandler;
    } else {
        KeBugCheckEx(...);
    }

    return _PsALtSystemCallRoutine(...);
}
```

The function pointed to by the pointer stored in the global variable `PsAltSystemCallHandlers` is a wrapper around `PsPicoSystemCallDispatch`:

```
PUNK PsAltSystemCallHandlers(...)
{
    PsPicoSystemCallDispatch(...);
    return 0;
}

```

From there, the gobal `PspPicoProviderRoutines` array transfers control to the provider, which is just `lxcore` as only one Pico Provider can be registered at a time.

### Hooking / Monitoring Pico Provider Dispatch Tables

It appears that despite devoting good effort to ensuring KPP protection of Pico Providers, facilities for monitoring events and instrumentinng providers with callbacks are absent.

## LxssManager

`LxssManager` is the external interface through which interactions with `lxcore` occur. The `LxssManager` process is a PPL process.

## WSL Version 2 and Virtual Machine Platform

It seems to be common knowledge among WSL users that WSL2 offers a full Linux kernel. Keen users may also have noticed that it is implemented using true virtualization. Interestingly, virtualization was not preferred for the original implementation due to overhead, but it seems by now that Microsoft has come up with a workable solution for this, enabling WSL2 to run as fast or faster as its predecessor.

The Linux Kernel leveraged by WSL2 is open-source. Yet the details behind the virtualization technology it uses are sparse. Microsoft appears to have been quietly making updates to its virtualization technology in for use in coming releases of Windows, with the most noteable use case (other than WSL2) being a subsystem for Android. There are numerous sources repeating the something like the phrase 'lightweight utility virtual machine' to describe the virtual machine used by these new subsystems, but no one among the public seems to know what this actually means. 

### Hyper-V Architecture

Hyper-V organizes VMs as 'partitions'. Each partition can interact with either a `VMBus` or the hypervisor through the `hypercall` API. Hypercalls seem to be similar to `vm_enter` and `vm_exit` in Intel VT/AMD-V or syscalls in a regular ring 3 -> ring 0 model. 

### Questions

To make things even more confusing, there now seems to be change in Microsoft's own terminology for the foundational virtual machine technology, with MSDN documentation claiming that the architecture is still just 'Hyper-V', while numerous online Q&A's on the distinction between Hyper-V (HV), Virtual Machine Platform (VMP), Windows Hypervisor Platform (WHP), and claim that Hyper-V is now just the user interface layer through which the Virtual Machine Platform is accessed. Others claim that the HV is the actual hypervisor implementation and that VMP and WHP are development platforms based on HV:

- https://www.google.com/search?client=firefox-b-1-d&q=Virtual+Machine+Platform
- https://superuser.com/questions/1556521/virtual-machine-platform-in-win-10-2004-is-hyper-v

This leads me to the following questions:

- Is the 'host' Windows instance virtualized when Hyper-V and VMP are enabled?
  - If yes, what interfaces exist for us to interact with the hypervisor (virtualization service provider?)
  - How can we make `hypercall`s to learn more about the environment
- Regarding the WSL2 'light weight' VM:
  - Own partition?
  - How can we interact with it from Windows user mode? Is LxssManager still the COM provider (looks like no)?


### Hypervisor Implementation

Depending on the architecture, the hypervisor itself will be loaded using one of the following:
- intel: hvix64.exe
- amd: hvax64.exe
- arm: hvaa64.exe

The hypervisor is intentionally kept minimal, with all management components confined to the root partition, with interfaces in user mode (WMI, VMM service, VM worker processes).

#### Data Structures

- `VM_VP` for each virtual processer 
- `TH_THREAD` for each virtual processor
- `TH_PROCESS` represent the partition process
- `VM_PARITION` represents actual partition

#### Startup Sequence

From Windows Internals:

- UEFI components load HvLoader module
- HvLoader loads the hypervisor binery (e.g. `hvix64.exe`)
- `KiSystemStartup` called (entry point of hypervisor), initializes `KPRCB`
- `BmpInitBootProcessor` called. 
  - Queries CPU and sets up:
  - Memory manager
  - VMX virtualization abstraction layer (VAL)
  - Synthetic Interrupt Controller (SynIC)
  - IOMMU
  - Address manager
- Root partition created

TBC

### Finding the WSL VM

Back to WSL - the move to a virtualized implementation indicates that the limitation of one subsystem in the Pico Provider model has been surmounted using Microsoft virtualization technology. It will be interesting to see if Pico Processes and Pico Providers are leveraged for other uses in the future, or if they will become vestigial organs of the Operating Systems only supported for the sake of WSL1? It appears to be the latter, for now.

WSL2 rquires two other Windows features to be enabled: Hyper-V and Virtual Machine Platform. WSL2 is said to use a lightweight virtual machine, but its not clear what this actually means. Even with running instances of WSL2, the `Get-VM` cmdlet does not return any related VMs, yet we know one exists, but it must not be managed by Hyper-V but rather the Windows hypervisor itself.

TBC

### Issuing Hypercalls

Hypercalls must occur from Ring 0 on x64. In order to explore them, a driver will be required. TBC



## Areas to Explore in the Future

Fuzzing (Microsoft appears to be doing this already):
- WSL1 system call fuzzing 
- WSL1 ELF parser fuzzing
- Hyper-V internals


## Other References

- [A syscall journey in the Windows kernel](/archives/577910001db3e9a7672a2466569c506939865ebe7ee4b6e8057fc51e49f9fcde_.html)
- [DISPATCHER_HEADER - Geoff Chappell, Software Analyst](https://www.geoffchappell.com/studies/windows/km/ntoskrnl/inc/ntos/ntosdef_x/dispatcher_header/index.htm)
- [WinAltSyscallHandler](https://github.com/0xcpu/WinAltSyscallHandler/blob/master/README.md)
- [DebugActive - Geoff Chappell, Software Analyst](https://www.geoffchappell.com/studies/windows/km/ntoskrnl/inc/ntos/ntosdef_x/dispatcher_header/debugactive.htm)
- [Gaining visibility into Linux binaries on Windows: Defend and Understand WSL](/archives/50105ffdbddfc7677c760e08af91325b0814fbaa4988da52afb559508a314710_WSL-BlueHat-Final.pdf.bin)
- [Pico toolbox](https://github.com/thinkcz/pico-toolbox)
- [WSL2-Linux-Kernel](https://github.com/microsoft/WSL2-Linux-Kernel)
- [Hyper-V arhchiecture](/archives/6b5cca628a052b5d9525639338b1940ad587cbf6ec80ebf4d7a3e3e88d5e059e_hyper-v-architecture.html)
- [Enabling Linux Root Partition](https://lkml.iu.edu/hypermail/linux/kernel/2102.2/00124.html)
- [Developing WSL distributions in Visual Studio](https://devblogs.microsoft.com/commandline/build-and-debug-c-with-wsl-2-distributions-and-visual-studio-2022/)
- [Windows Sandbox blog](https://techcommunity.microsoft.com/t5/windows-kernel-internals-blog/windows-sandbox/ba-p/301849)
- [Blog explaining HV](https://www.acronis.com/en-us/blog/posts/hyper-v-authoritative-guide/)
- [Hypercall Fuzzing](https://github.com/FSecureLABS/ViridianFuzzer)
- [Microsoft Hypervisor Top Level Functional Specification](/archives/858642504c86ed80b141862048b6d1327c0fe5237b666e4cbe41fb351faee92c_Hypervisor%20Top%20Level%20Functional%20Specification%20v6.0b.pdf.bin)
- [http://hvinternals.blogspot.com/2021/]
- [list of HV resources](https://forum.exetools.com/showthread.php?p=123103)