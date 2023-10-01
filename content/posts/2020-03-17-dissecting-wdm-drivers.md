+++

title = "Dissecting a Simple WDM Driver"
date = 2020-03-16 00:05:28 -0500

+++

Chapter 4 of _Kernel Programming for Windows_ walks through the process of developing a driver "from start to finish". This post is for quick notes on the dissection of this example driver, taken for learning purposes. 

#### Source Code

The full source code for the project can be found on GitHub: [https://github.com/joshfinley/PriorityBooster](https://github.com/joshfinley/PriorityBooster)

| Table of Contents |
| ----------------- |
| 1. DriverEntry    |
| 2. DriverObject   |
| 3. DeviceObject   |
| 4. IRP            |
| 5. DeviceControl  |

## 1. DriverEntry

Stack trace at driver entry:

```
2: kd> k
 # Child-SP          RetAddr           Call Site
00 ffffbe84`b6db7898 fffff800`3b235020 PriorityBooster!DriverEntry [C:\Users\finle\source\repos\PriorityBooster\PriorityBooster\Source.cpp @ 12] 
01 ffffbe84`b6db78a0 fffff800`3e510c06 PriorityBooster!GsDriverEntry+0x20 [minkernel\tools\gs_support\kmodefastfail\gs_driverentry.c @ 47] 
02 ffffbe84`b6db78d0 fffff800`3e51063e nt!IopLoadDriver+0x4c2
03 ffffbe84`b6db7ab0 fffff800`3debd005 nt!IopLoadUnloadDriver+0x4e
04 ffffbe84`b6db7af0 fffff800`3df2a7b5 nt!ExpWorkerThread+0x105
05 ffffbe84`b6db7b90 fffff800`3dfc8b5a nt!PspSystemThreadStartup+0x55
06 ffffbe84`b6db7be0 00000000`00000000 nt!KiStartSystemThread+0x2a
```

### GsDriverEntry
We can see that prior to the projects `DriverEntry` function being called, `GsDriverEntry` is invoked:

```
2: kd> x PriorityBooster!GsDriverEntry
fffff800`3b235000 PriorityBooster!GsDriverEntry (struct _DRIVER_OBJECT *, struct _UNICODE_STRING *)
```

And dissasembling this function shows:

```
2: kd> uf fffff800`3b235000
PriorityBooster!GsDriverEntry [minkernel\tools\gs_support\kmodefastfail\gs_driverentry.c @ 43]:
   43 fffff800`3b235000 48895c2408      mov     qword ptr [rsp+8],rbx
   43 fffff800`3b235005 57              push    rdi
   43 fffff800`3b235006 4883ec20        sub     rsp,20h
   43 fffff800`3b23500a 488bda          mov     rbx,rdx
   43 fffff800`3b23500d 488bf9          mov     rdi,rcx
   45 fffff800`3b235010 e817000000      call    PriorityBooster!__security_init_cookie (fffff800`3b23502c)
   46 fffff800`3b235015 488bd3          mov     rdx,rbx
   46 fffff800`3b235018 488bcf          mov     rcx,rdi
   46 fffff800`3b23501b e890c1ffff      call    PriorityBooster!DriverEntry (fffff800`3b2311b0)
   47 fffff800`3b235020 488b5c2430      mov     rbx,qword ptr [rsp+30h]
   47 fffff800`3b235025 4883c420        add     rsp,20h
   47 fffff800`3b235029 5f              pop     rdi
   47 fffff800`3b23502a c3              ret
```

We can see that this stub function `GsDriverEntry`:
- accepts the same parameters as DriverEntry
- initializes the security cookie
- calls the user-created `DriverEntry` function.


Quickly, lets look at `__security_init_cookie`:
```
PriorityBooster!__security_init_cookie [minkernel\tools\gs_support\kmodefastfail\gs_support.c @ 37]:
fffff800`3b23502c 488b05cddfffff  mov     rax,qword ptr [PriorityBooster!__security_cookie (fffff800`3b233000)]
fffff800`3b235033 4885c0          test    rax,rax
fffff800`3b235036 741a            je      PriorityBooster!__security_init_cookie+0x26 (fffff800`3b235052)
fffff800`3b235038 48b932a2df2d992b0000 mov rcx,2B992DDFA232h
fffff800`3b235042 483bc1          cmp     rax,rcx
fffff800`3b235045 740b            je      PriorityBooster!__security_init_cookie+0x26 (fffff800`3b235052)
fffff800`3b235047 48f7d0          not     rax
fffff800`3b23504a 488905b7dfffff  mov     qword ptr [PriorityBooster!__security_cookie_complement (fffff800`3b233008)],rax
```
And the corresponding source can be found [here](https://gist.github.com/joshfinley/7e01480ab70ade5f7d296cc4e37684e1)

### nt!IopLoadDriver

`IopLoadDriver` is an undocumented function in the family of Windows I/O Manager support functions.
- A listing of these functions can be found here: [https://gist.github.com/joshfinley/8a6a0cb09af32507f3c6157c16f8e30b](https://gist.github.com/joshfinley/8a6a0cb09af32507f3c6157c16f8e30b). 
- A listing of these prefixes can be found here: [https://gist.github.com/joshfinley/bc54df3c092e224ad08140cfd619fa2d](https://gist.github.com/joshfinley/bc54df3c092e224ad08140cfd619fa2d). 
- Finally, the fully dissasembly of `nt!IopLoadDriver` can be found here: [https://gist.github.com/joshfinley/da2fd8039de1e97190f5ce2c9bd07bc4](https://gist.github.com/joshfinley/da2fd8039de1e97190f5ce2c9bd07bc4)

`IopLoadDriver` is used to call the driver entry function, as seen in the stack trace at the beginning of this post. It is used for `SERVICE_DEMAND` driver entry. The corresponding function for boot loading drivers is `nt!IopInitializeBuiltInDriver` (see [https://reverseengineering.stackexchange.com/a/2638](https://reverseengineering.stackexchange.com/a/2638)).

From _Windows Internals_:
> When the I/O manager kernel subsystem loads device drivers that HKLM\SYSTEM\Current-ControlSet\Services specifies, the I/O manager executes the function IopLoadDriver.

The function defintion for `IopLoadDriver` looks something like this:
``` c++
NTSTATUS
IopLoadDriver(
    IN  HANDLE      KeyHandle,
    IN  BOOLEAN     CheckForSafeBoot,
    IN  BOOLEAN     IsFilter,
    OUT NTSTATUS   *DriverEntryStatus
    )
```

- see [https://github.com/joshfinley/ntoskrnl/blob/master/Io/iomgr/internal.c](https://github.com/joshfinley/ntoskrnl/blob/master/Io/iomgr/internal.c) (forked from the [Windows Research Kernel](https://github.com/Zer0Mem0ry/ntoskrnl/))

In this case, the call to `IopLoadDriver` comes from `IopLoadUnloadDriver`. Here's the source code from the React OS function: [https://doxygen.reactos.org/d9/d9f/ntoskrnl_2io_2iomgr_2driver_8c_source.html](https://doxygen.reactos.org/d9/d9f/ntoskrnl_2io_2iomgr_2driver_8c_source.html).


## 2. DriverObject

`DriverObject` is defined in `wdm.h` as follows:

``` c++
typedef struct _DRIVER_OBJECT {
  CSHORT             Type;
  CSHORT             Size;
  PDEVICE_OBJECT     DeviceObject;          // pointer to device objects created by the driver
  ULONG              Flags;                 
  PVOID              DriverStart;           
  ULONG              DriverSize;            
  PVOID              DriverSection;         
  PDRIVER_EXTENSION  DriverExtension;       // pointer to driver extension
  UNICODE_STRING     DriverName;             
  PUNICODE_STRING    HardwareDatabase;      // pointer to the \Registry\Machine\Hardware path to the configuration information in the registry
  PFAST_IO_DISPATCH  FastIoDispatch;        
  PDRIVER_INITIALIZE DriverInit;            // entry point for DriverEntry, setup by I/O manager
  PDRIVER_STARTIO    DriverStartIo;         
  PDRIVER_UNLOAD     DriverUnload;          // entry point for DriverUnload set by DriverEntry
  PDRIVER_DISPATCH   MajorFunction[IRP_MJ_MAXIMUM_FUNCTION + 1];    // dispatch table consisting of an array of entry points for the drivers DispatchXxx routines
} DRIVER_OBJECT, *PDRIVER_OBJECT;
```

Examination of some of these types:

```
2: kd> dt _DRIVER_OBJECT
PriorityBooser!_DRIVER_OBJECT
   +0x000 Type             : Int2B
   +0x002 Size             : Int2B
   +0x008 DeviceObject     : Ptr64 _DEVICE_OBJECT
   +0x010 Flags            : Uint4B
   +0x018 DriverStart      : Ptr64 Void
   +0x020 DriverSize       : Uint4B
   +0x028 DriverSection    : Ptr64 Void
   +0x030 DriverExtension  : Ptr64 _DRIVER_EXTENSION
   +0x038 DriverName       : _UNICODE_STRING
   +0x048 HardwareDatabase : Ptr64 _UNICODE_STRING
   +0x050 FastIoDispatch   : Ptr64 _FAST_IO_DISPATCH
   +0x058 DriverInit       : Ptr64     long 
   +0x060 DriverStartIo    : Ptr64     void 
   +0x068 DriverUnload     : Ptr64     void 
   +0x070 MajorFunction    : [28] Ptr64     long 
```

```
2: kd> dt PDEVICE_OBJECT
PriorityBooster!PDEVICE_OBJECT
Ptr64    +0x000 Type             : Int2B
   +0x002 Size             : Uint2B
   +0x004 ReferenceCount   : Int4B
   +0x008 DriverObject     : Ptr64 _DRIVER_OBJECT
   +0x010 NextDevice       : Ptr64 _DEVICE_OBJECT
   +0x018 AttachedDevice   : Ptr64 _DEVICE_OBJECT
   +0x020 CurrentIrp       : Ptr64 _IRP
   +0x028 Timer            : Ptr64 _IO_TIMER
   +0x030 Flags            : Uint4B
   +0x034 Characteristics  : Uint4B
   +0x038 Vpb              : Ptr64 _VPB
   +0x040 DeviceExtension  : Ptr64 Void
   +0x048 DeviceType       : Uint4B
   +0x04c StackSize        : Char
   +0x050 Queue            : <anonymous-tag>
   +0x098 AlignmentRequirement : Uint4B
   +0x0a0 DeviceQueue      : _KDEVICE_QUEUE
   +0x0c8 Dpc              : _KDPC
   +0x108 ActiveThreadCount : Uint4B
   +0x110 SecurityDescriptor : Ptr64 Void
   +0x118 DeviceLock       : _KEVENT
   +0x130 SectorSize       : Uint2B
   +0x132 Spare1           : Uint2B
   +0x138 DeviceObjectExtension : Ptr64 _DEVOBJ_EXTENSION
   +0x140 Reserved         : Ptr64 Void

2: kd> dt PDRIVER_EXTENSION
PriorityBooster!PDRIVER_EXTENSION
Ptr64    +0x000 DriverObject     : Ptr64 _DRIVER_OBJECT
   +0x008 AddDevice        : Ptr64     long 
   +0x010 Count            : Uint4B
   +0x018 ServiceKeyName   : _UNICODE_STRING

2: kd> dt PFAST_IO_DISPATCH
PriorityBooster!PFAST_IO_DISPATCH
Ptr64    +0x000 SizeOfFastIoDispatch : Uint4B
   +0x008 FastIoCheckIfPossible : Ptr64     unsigned char 
   +0x010 FastIoRead       : Ptr64     unsigned char 
   +0x018 FastIoWrite      : Ptr64     unsigned char 
   +0x020 FastIoQueryBasicInfo : Ptr64     unsigned char 
   +0x028 FastIoQueryStandardInfo : Ptr64     unsigned char 
   +0x030 FastIoLock       : Ptr64     unsigned char 
   +0x038 FastIoUnlockSingle : Ptr64     unsigned char 
   +0x040 FastIoUnlockAll  : Ptr64     unsigned char 
   +0x048 FastIoUnlockAllByKey : Ptr64     unsigned char 
   +0x050 FastIoDeviceControl : Ptr64     unsigned char 
   +0x058 AcquireFileForNtCreateSection : Ptr64     void 
   +0x060 ReleaseFileForNtCreateSection : Ptr64     void 
   +0x068 FastIoDetachDevice : Ptr64     void 
   +0x070 FastIoQueryNetworkOpenInfo : Ptr64     unsigned char 
   +0x078 AcquireForModWrite : Ptr64     long 
   +0x080 MdlRead          : Ptr64     unsigned char 
   +0x088 MdlReadComplete  : Ptr64     unsigned char 
   +0x090 PrepareMdlWrite  : Ptr64     unsigned char 
   +0x098 MdlWriteComplete : Ptr64     unsigned char 
   +0x0a0 FastIoReadCompressed : Ptr64     unsigned char 
   +0x0a8 FastIoWriteCompressed : Ptr64     unsigned char 
   +0x0b0 MdlReadCompleteCompressed : Ptr64     unsigned char 
   +0x0b8 MdlWriteCompleteCompressed : Ptr64     unsigned char 
   +0x0c0 FastIoQueryOpen  : Ptr64     unsigned char 
   +0x0c8 ReleaseForModWrite : Ptr64     long 
   +0x0d0 AcquireForCcFlush : Ptr64     long 
   +0x0d8 ReleaseForCcFlush : Ptr64     long 

2: kd> dt PDRIVER_INITIALIZE
PriorityBooster!PDRIVER_INITIALIZE
Ptr64  long (
	_DRIVER_OBJECT*, 
	_UNICODE_STRING*)

2: kd> dt PDRIVER_STARTIO
PriorityBooster!PDRIVER_STARTIO
Ptr64  void (
	_DEVICE_OBJECT*, 
	_IRP*)

2: kd> dt PDRIVER_UNLOAD
PriorityBooster!PDRIVER_UNLOAD
Ptr64  void (
	_DRIVER_OBJECT*)

2: kd> dt PDRIVER_DISPATCH
PriorityBooster!PDRIVER_DISPATCH
Ptr64  long (
	_DEVICE_OBJECT*, 
	_IRP*)
```

The most relevant structures of these to the study at hand are:
- `PDEVICE_OBJECT DeviceObject`
- `PDRIVER_DISPATCH MajorFunction`


First, lets look at `PDRIVER_DISPATCH MajorFunction`:
``` c++
// In PriorityBooster DriverEntry
	DriverObject->DriverUnload = PriorityBoosterUnload;
	DriverObject->MajorFunction[IRP_MJ_CREATE] = PriorityBoosterCreateClose;
	DriverObject->MajorFunction[IRP_MJ_CLOSE] = PriorityBoosterCreateClose;
	DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = PriorityBoosterDeviceControl;
```
```
2: kd> dt DriverObject MajorFunction
Local var @ 0xffffbe84b6db7918 Type _DRIVER_OBJECT*
0xfffff800`3de3c7bd 
   +0x070 MajorFunction : [28] 0x61b8818b`48000000     long  +61b8818b48000000
2: kd> dx -id 0,0,ffffd502ada73300 -r1 (*((PriorityBooser!long (__cdecl*(*)[28])(_DEVICE_OBJECT *,_IRP *))0xfffff8003de3c82d))
(*((PriorityBooser!long (__cdecl*(*)[28])(_DEVICE_OBJECT *,_IRP *))0xfffff8003de3c82d))                 [Type: long (__cdecl* [28])(_DEVICE_OBJECT *,_IRP *)]
    [0]              : 0x61b8818b48000000 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [1]              : 0xfeffff2081f00000 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [2]              : 0x1b80017fc85e8ff [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [3]              : 0x45c0220f44000000 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [4]              : 0x78e8c933d233c033 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [5]              : 0x537d4a058b000018 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [6]              : 0x7401a82e74c08500 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [7]              : 0x72023cc0200f442a [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [8]              : 0x651c7302fe804022 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [9]              : 0x20250c8b48 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [10]             : 0xf0000061b8918b48 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [11]             : 0x38e8fffeffff2281 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [12]             : 0x44ceb60f400017fc [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [13]             : 0x8148c38b48c1220f [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [14]             : 0xc35b5e00000088c4 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [15]             : 0xcccccccccccccccc [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [16]             : 0x8245c8948cccccc [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [17]             : 0x4155415441575655 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [18]             : 0x4950ec8348574156 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [19]             : 0xf98b48da8b48f08b [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [20]             : 0x394674db8548ed33 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [21]             : 0xc9850f00005918ab [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [22]             : 0x8b48d78b48000000 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [23]             : 0xc084000006f5e8cb [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [24]             : 0x3948000000b6850f [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [25]             : 0xa9850f00005970ab [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [26]             : 0x9c8b48c033000000 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
    [27]             : 0xc483480000009024 [Type: long (__cdecl*)(_DEVICE_OBJECT *,_IRP *)]
```

Each index, of course corresponds to an `IRP_MJ_` code

## 3. DeviceObject

Device Object is a structure that looks like this:
``` C++

typedef struct DECLSPEC_ALIGN(MEMORY_ALLOCATION_ALIGNMENT) _DEVICE_OBJECT {
    CSHORT Type;                                // Read-only. = 3
    USHORT Size;                                // Bytes size
    LONG ReferenceCount;                        // For I/O manager handle tracking
    struct _DRIVER_OBJECT *DriverObject;        // Set by IoCreateDevice
    struct _DEVICE_OBJECT *NextDevice;          // ptr to next DeviceObject created by the same driver, if there is any. List updated by I/O manager upon IoCreateDevice*
    struct _DEVICE_OBJECT *AttachedDevice;      // See MDN doc
    struct _IRP *CurrentIrp;                    // Obvious. See MDN doc for more
    PIO_TIMER Timer;                            // Time objet used by I/O manager. Not sure why.
    ULONG Flags;                                // See above:  DO_...
    ULONG Characteristics;                      // See ntioapi:  FILE_...
    __volatile PVPB Vpb;                        // ptr to volume parameter block associated with the device object (what is a VPB?)
    PVOID DeviceExtension;                      // Important! ptr to device extension. See https://docs.microsoft.com/en-us/windows-hardware/drivers/kernel/device-extensions
    DEVICE_TYPE DeviceType;                     // Set by IO create device. See https://docs.microsoft.com/en-us/windows-hardware/drivers/kernel/specifying-device-types for a list of possible types
    CCHAR StackSize;                            // Usually automatically set by I/O manager
    union {
        LIST_ENTRY ListEntry;                   // Opaque. Used by the I/O manager. It'd be fun to poke around in the IO manager to see what these are used for.
        WAIT_CONTEXT_BLOCK Wcb;
    } Queue;
    ULONG AlignmentRequirement;                 //
    KDEVICE_QUEUE DeviceQueue;
    KDPC Dpc;

    //
    //  The following field is for exclusive use by the filesystem to keep
    //  track of the number of Fsp threads currently using the device
    //

    ULONG ActiveThreadCount;                    // Opaque, apparently reservered for future use. It be fun to see if this is currently used by anyone
    PSECURITY_DESCRIPTOR SecurityDescriptor;    // Device object SECUR_TY_DESCRIPTOR. Null == default settings. Normally readonly, but can be set by ZwSetSecurityObject function
    KEVENT DeviceLock;                          // Synchronization object used by I/O manager

    USHORT SectorSize;                          // Normally set to 0, unless the device represents a volume.
    USHORT Spare1;                              // Reserved for system use. Opaque.

    struct _DEVOBJ_EXTENSION  *DeviceObjectExtension; // Pointer to device object extension for use by I/O and PNP managers
    PVOID  Reserved;

} DEVICE_OBJECT;

typedef struct _DEVICE_OBJECT *PDEVICE_OBJECT;
```

and is created by this:

``` C++
NTSTATUS IoCreateDevice(
  PDRIVER_OBJECT  DriverObject,
  ULONG           DeviceExtensionSize,
  PUNICODE_STRING DeviceName,
  DEVICE_TYPE     DeviceType,
  ULONG           DeviceCharacteristics,
  BOOLEAN         Exclusive,
  PDEVICE_OBJECT  *DeviceObject
);
```

In the WDM model, device objects are broken into three types:

1. Physical DO (PDO) - represents device on a bus to a bus driver
2. Function DO (FDO) - represents a device to a function driver
3. Filter DO (Filder DO) - repesents a device to a filter driver

One of the most important members of the `_DEVICE_OBJECT` structure is the `Device Extension`. It is driver defined and maintains the state of the driver, and stores important data, including resources allocated by the kernel and data for the drivers I/O operations.

Memory allocation for this structure and the `Device Object` itself are handled by the I/O manager. The memory resides in the nonpaged pool.

The KDPC memebr of DeviceObject is officially undocumented, but the structure definition can be found in the Windows Reserach Kernel. It looks like this:

``` c++
typedef struct _KDPC {
    UCHAR Type;
    UCHAR Importance;
    UCHAR Number;
    UCHAR Expedite;
    LIST_ENTRY DpcListEntry;
    PKDEFERRED_ROUTINE DeferredRoutine;
    PVOID DeferredContext;
    PVOID SystemArgument1;
    PVOID SystemArgument2;
    PVOID DpcData;
} KDPC, *PKDPC, *PRKDPC;
```

PriorityBooster creates the DeviceObject accordingly:

``` c++
	PDEVICE_OBJECT DeviceObject;
	NTSTATUS status = IoCreateDevice(
		DriverObject,
		0,                      // Automatically set by I/O manager
		&devName,               
		FILE_DEVICE_UNKNOWN,    // 0x00000022
		0,                      // Characteristics, to be set by I/O manager
		FALSE,                  // Not exclusive
		&DeviceObject
	);
```

## References
 [1] [https://leanpub.com/windowskernelprogramming](https://leanpub.com/windowskernelprogramming)