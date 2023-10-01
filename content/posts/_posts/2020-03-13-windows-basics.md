+++
layout: post
title:  "Memorizing Basic Windows Details"
date:   2020-03-13 00:05:28 -0500
description: Notes on fundamental windows concepts for reference and memorization
series: windows_internals
titleImage:
    file: 'title.png'
+++

As I've been working my Pavel Yosifovich's _Kernel Programming for Windows_, I've found that theres a few basic details of the Windows operating system that I have yet to commit to muscle-memory. This page is just some simple notes from the book to maybe help with retention. Items marked with a (?) are those that I feel the need to learn more about.

## Virtual Memory

- default 32 bit address space for processes is 2 GB 
- specifying the `LARGEADDRESSAWARE` flag in the PE header allows the address space size to be increased to a max of 3 GB. Binary must have been linked with LARGEADDRESSAWARE linker flag. This brings me back to the days of modding _Fallout: New Vegas_ which was wonderful but limited severely by 32 bit memory requirements. There was a popular mod which I think did exactly this and was able to extend the AS to 4 GB.

## Page States

- Free
- Committed
- Reserved

## System Memory

- Operating system resides in upper address range
    - 32 bit: 0x80000000-0xFFFFFFF
    - 32 bit w/ increase v_address_space setting: 0xC0000000-0XFFFFFFFF
    - 64 bit Win8/2012: upper 8TB
    - 64 bit Win8.1/2012 R2 and later: upper 128 TB

## Threads

- Processes expose resources like virtual memory and kernel object handles to threads
- threads own:
    - current access mode
    - execution context
    - one or two stacks (?)(why two? answered below)
    - Thread Local Storage array (?)
    - Base priority / dynamic priority
    - Processor affinity (?)
- thread stacks:
    - 32 bit: default 12 KB
    - 64 bit: default 24 KB
    - user mode threads have two stacks. 
        - the first is the kernel stack and cant be paged out
        - the second one resides in the user address space range and has a default max of 1 MB.
            - can be paged out
- user mode thread stack:
    - starts with a small amount of memory committed, the remaining being reserved
    - the next page after the initially commited memory is marked with a special protection `PAGE_GAURD` and is called the Gaurd Page (?)(marked where?)
    - once the gaurd page is written to, an exception is thrown to be handled by the memory manager, who removes the gaurd and commits the memory

## System Services \ System Calls

- `ntdll.dll` is also known as the `Native API`. Didn't know that.
- transition to kernel mode: 64 bit = syscall, 32 bit = sysenter
- following the transition, the dispatcher routine indexes into the SSDT to jump to the actual system call

## Architecture

- executive hold the various managers: Object Manager, Memory Manager, I/O Manager, PnP Manager, Power Manager, Configuration Manager.
- executive is the larger upper layer of ntoskrnl.exe, and the kernel itself is the lower layer.
- kernel layer implements thread scheduling, interrupt, and exception dispatching
- kernel layer implements kernel primitives (?)(what are some other 'primitives')
- `win32k.sys` is responsible for much of the graphics capabilities of the operating system (?)(was it always in the kernel?)
- `HAL` provides abstractions to make dealing with physical devices easier
- System Processes include `smss.exe, lsass.exe, winlogon.exe, services.exe`
- `csrss.exe` is a helper to the kernel for managing processes. One instance runs per session. Manager the windows subsystem
- VBS (virtualization based security) puts the actual machine in a Hyper-V virtual machine. Whoa.

## Handles and Objects

- Objects, managed by the Object Manager, count their references and will not be allowed to be destroyed until all references are released
- Instances of these are data structures
- Objects reside in system space
- User mode must access these indirectly through `handles`.
- Handles are indexes into tables maintained by processes.
- the indexes point logically to the kernel object in system space
- drivers turn handles into pointers using `ObReferenceObjectByHandle` function
- `0` is never a valid handle
- handles are in increments of `4`.
- resource leaks are prevented by calling `ObDereferenceObject`
- the WinObj sysinternals program interfaces with the Object Manager
- each object points to an object type
- `Create` functions called with a name will either actually create the object or open an existing one if the name exists. This can be checked for by using `GetLastError`and seeing if it returns `ERROR_ALREADY_EXISTS`
- names for objects are prepended with various strings
- object names are session-relative. to share across sessions, it can be created in session 0 by prepending the object name with `Global\`
- every process has a private handle table to kernel objects
- access masks define what operations are allowed to be performed on a handle. Access handles with the proper access mask
- to get the true number of references to an object, use kd's `trueref` command. E.g. `trueref <objaddr>`

## Additional Reading

- https://en.wikipedia.org/wiki/Object_Manager_(Windows)
- https://docs.microsoft.com/en-us/windows/win32/secauthz/access-rights-and-access-masks