+++
title = 'Stealth GetProcAddress'
date = 2023-10-17T11:09:58-05:00
draft = true
+++

Use of Microsoft provided system APIs in the form of User32, Kernel32, Ntdll, etc. are inevitable in malware development. For accessing system resources, we always have to at least make a system call. Most of the time, we don't want to implement any additional logic ourselves. It was as recent as 2015 that `AddVectoredExceptionHandler`'s internals ere documented, and it wasn't even by cybersecurity professionals, but rather game hackers
{{< citation >}}
 https://www.unknowncheats.me/forum/c-and-c-/160827-internals-addvectoredexceptionhandler.html
{{< /citation >}}.

`GetProcAddress`, however, has been popular in malware for ages {{< citation >}}https://modexp.wordpress.com/2019/06/24/inmem-exec-dll/{{< /citation >}}. Sadly for malware developers, this convenient API became harder to access due to randomized image bases, and then (much) later, API hooks in antimalware products.

Thus was born the need for position independence in Windows malware, which lead malware writers to the process environment block (PEB). In this way `GetProcAddress` is re-implemented from scratch using information about loaded modules available from the GS segment register. The process is straightforward: Process data structures & links in th PEB to walk the export tables of loaded modules. Since the PEB is at a constant offset of the GS segment, this works pretty much anywhere.

Considering this behavior is somewhat (to what extent, I'm unsure) unusual, a `PAGE_GUARD` flag can be placed on protected export address tables and an exception handler placed to handle such accesses {{< citation >}}https://github.com/connormcgarr/EATGuard{{< /citation >}}. Antimalware products can protect such handlers in various ways {{< citation >}}https://pdf.sciencedirectassets.com/280203/1-s2.0-S1877050919X00149/1-s2.0-S1877050919316229/main.pdf?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEKH%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJGMEQCIGEtQ9cIPbUqZgbMFwqtfSUDlvVQsEejRP7vpULb%2B2xZAiBnhg1mu3gEkeIV4pYOJ3LKLZ01rwfcQJ6T2O%2FNZWnLtSq7BQiq%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAUaDDA1OTAwMzU0Njg2NSIMsRTdWDGETEaUef%2BRKo8FK8LR9YS7L0qg9iYW%2FkmQ3%2FA03uRCVbQTRj7tlO4LrwI8bMsW4CMwpNNr8kHLB4OjsnqrGEBAjxmj3jyEyUq8v%2Bbsg%2Fdw1%2FOFATVJ41ujapbTSyzZKZxP5GuRK3jy1UE1fuKoe9OiiGX3M8nwqs%2BtO%2BLa2BINh0gFQY9ZpFsxesLfdv9tJPJxEJqcngmty9RzDI91vlGilT3sRe2%2FhUjp6FzwAwFo3WFyPuD7hpqpbGKcuc%2B0ACsfhYah3YtB55s%2FpUYm5sKKSCF7WyrnV4xw4IwsqH%2B%2BN%2BTZ9hj5C8ePIyDuPh0iizXSIV5kl2f3cvtNETeFtIgDpOzOKvKE%2Bj8lT9s9fiqMnFNqZoq6hJral%2FZONwi8T3CCwAACvgEp0C9dk7rkI8xQtsmdNDhUz2vSdCweoylYtQDGBa0IpFfPmAlyiVphJDCu6nGBr8CWq3C4JtCe7SG41S1OkzMclg80ZOM804xoy4jhkSM86z4qwT6L1QQR%2BGFt6rJ6znQ1c4wVaICX9NDlCQzNifkKFXTV6p5FaEGwUbmI0I%2BAFxuCxOcVTp2zxgNkvEfITicZ1irMbOcXAlzj9trDz0bX1h6hymeG66Oddt1xp7Qu1rzcxxzC4NE8twwAhfArLzEncSbf4MwDsucwE9Tks1JY7iQbhNUszEKGBDWjtwN5QiTZerexbucGBR4bG7weLyRyq5QC2s7KI6IWbXPD2oBrjBcqhiwltMqbb5FdkDBELHeev1ZcCfNxGe2wXCR5z03ApQ4SbfCaW%2BO68f1CA80kxwWcqBggbAzQ4TltAkRdY2pOBVJqTIqIDBW3Q1OTELUa07JJIuXupTVKh1JxzdEZ1os%2F14ha0nOesH8wqtdM9gltFzDI8aK2BjqyAam1%2BfiWeqmBKQq0NYHXZBLPh1Jd3R%2FlDrOaYhQ%2Fq6GlwSLKUb%2BHOAYW42ORrSEU%2BzJxLyaDbkl%2BDK2XYo0HJL6edBU6IFVuwpHvHxXb5piEPAOi%2BEE4qE%2F7VgC%2Fp85W0FqjO%2B4pVhspKJACqE%2B7yOBdYsgFtqFl4NQiXT6ZpIGo3nyXGbzWvMMHitp755K037f8%2B3peRpT%2FWG6WVPtwS3XTv%2BLThcVaM%2FbcUFunjWZZcLQ%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240823T165925Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAQ3PHCVTYQLG6KLRF%2F20240823%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=ff215720097cf85083d68b246738edf41b2793c093b506fd0d175f756b38cf86&hash=7a4dffd5159fbc4351dd5798f88060d755ead3466f2cb7e95c010e0cde3cb89a&host=68042c943591013ac2b2430a89b270f6af2c76d8dfd086a07176afe7c76c2c61&pii=S1877050919316229&tid=spdf-c53667a6-9377-4a91-95c1-2944deb5406d&sid=85ac55012acab044f8289bc4157596480394gxrqa&type=client&tsoh=d3d3LnNjaWVuY2VkaXJlY3QuY29t&ua=0f135a0355000f51510d&rr=8b7ca72c4d954df7&cc=us{{< /citation >}}{{< citation >}}https://securityintelligence.com/x-force/using-veh-for-defense-evasion-process-injection/{{< /citation>}}.

This leaves us with a quandry. In position independent code, we really neet to resolve DLL exports somehow. Hardcoded syscalls are painfull, error prone, and overall a bad option. How can we manage to find the exports we need without triggering a guard page?

### Thread Initialization Artifacts

On threat initialization, we have some artifacts to work with.

1. Stack artifacts in the form of `kernel32.BaseThreadInitThunk` and `ntdll.RtlUserThreadStart`.
2. Register artifacts for threads created on `executableName.OptionalHeader.AddressOfEntrypoint`, we will have in some cases the values of `rip` or `AddressOfEntrypoint`, reflecting  location in the current executable module.
3. Register artifacts for threads created with `CreateThread`.
4. Stack artifacts (same as 1) for `CreateRemoteThreadEx`.
5. Register artifacts for threads created with `CreateRemoteThreadEx`:

{{< figure 
  src="/stealth-get-proc-address/main_artifacts.png" 
  caption="Main program address of entrypoint in a debugger, displaying some readable addresses in the current module and thread initilization routines on the stack" 
>}}

As an example for `CreateRemoteThreadEx`, we can observe in a debugger on a Windows 10 20019 19045.4780 system the following artifacts from thread cration and execution:

- `rax`: Base address of the memory region allocated for the thread.
- `rdx`: Same as `rax`.
- `rsp`: `kernel32.BaseThreadInitThunk+14`.
- `rsp + 0x30`: `ntdll.RtlUserThreadStart+21`.

For any thread, we also still have access to the PEB, and if we don't wish to resolve functions the "normal" way, there are addresses we can reference inside this structure (ignoring loader data table entries):

- `peb->lpImageBaseAddress`: Base address of main program executable
- `peb->pFastPebLoack`: On typical image, this will be an address inside `ntdll.data`.
- `peb->lpTlsBitmmap`: On typical image, this will be an address inside `ntdll.data`.
- `peb->lpProcessStarterHelper`: On typical image, this will be an address inside `ntdll.data`.

While the EAT might be marked with `PAGE_GUARD`, the `.text` almost certainly is not. Unfurtonately, the *forbidden* gaurded page is between `.data` and the `.text` section, so direct memory traversal will be an issue if we pursue syscalls starting from the `.data` section. At this point we have some options:

- Resolve NTDLL base from the PEB
- Hunt for references in `.data` to `.text`
- If we are in a newly created thread, use the stack to find an address inside `ntdllRtlUserThreadStart` and thus `ntdll.text`
- If we must use the PEB, we can get an address inside `ntdll.data` and hunt for a reference to `ntdll.text`.

### Egg Hunting Syscalls

A brief survey of NTDLL versions from the Windows Binary Index features of `ntdll.dll` that may help us orient ourselves from `RtlUserThreadStart` {{< citation >}}https://winbindex.m417z.com/{{< /citation >}}.

```

    Directory: C:\Users\base\Desktop\workspace\re\ntdll


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----         8/24/2024   1:38 PM           3679 distance.py
-a----         8/24/2024  12:51 PM        1825456 ntdll-x64-win10-1507-kb5041782.blob
-a----         8/24/2024  12:53 PM        1999064 ntdll-x64-win10-1809-kb5031361.blob
-a----         7/30/2024   9:59 AM        2029080 ntdll-x64-win10-2009-kb5042097.blob
-a----         8/24/2024  12:52 PM        2133576 ntdll-x64-win11-21h2-kb5039213.blob

File: ntdll-x64-win10-1507-kb5041782.blob
    NtAcceptConnectPort VA: 0x7FFC87C037B0
    RtlUserThreadStart VA: 0x7FFC87B79F30
    Difference: 0x89880
    NtAcceptConnectPort comes AFTER

File: ntdll-x64-win10-1809-kb5031361.blob
    NtAcceptConnectPort VA: 0x7FFC87C0FC20
    RtlUserThreadStart VA: 0x7FFC87BCA4C0
    Difference: 0x45760
    NtAcceptConnectPort comes AFTER

File: ntdll-x64-win10-2009-kb5042097.blob
    NtAcceptConnectPort VA: 0x7FFC87C0D590
    RtlUserThreadStart VA: 0x7FFC87BBCC70
    Difference: 0x50920
    NtAcceptConnectPort comes AFTER

File: ntdll-x64-win11-21h2-kb5039213.blob
    NtAcceptConnectPort VA: 0x7FFC87C14130
    RtlUserThreadStart VA: 0x7FFC87B74830
    Difference: 0x9F900
    NtAcceptConnectPort comes AFTER

Average distance between VAs: 0x6FC80
Average distance of NtAcceptConnectPort from image base: 0x9D2A4
```

In the four surveyed cases, `NtAcceptConnectPort` (which should be one of the first system call handlers in the code body) is *after* `RtlUserThreadStart` by an average of `0x6fc80`, and a maximum distance of `0x9F900`. This data gives us a clear direction and boundary for search.

Although `NtAcceptConnectPort` will usually appear as the first `Nt` API export in NTDLL, the first Syscall function body will usually be `NtAccessCheck`. The syscall values will then follow which order the handler appears in the wrapper. MDSec tends to get credit for this discovery, but I believe the first actual documentation of this in the cybersecurity space was somewhere on the [Modexp](https://modexp.wordpress.com/) blog.

An initial thought might be to just signature match syscall stubs as our "egg" and iterate to the first instance, and arrive at an ordered list of syscalls. While this will give us a list of valid syscalls, we still have no information about which syscalls those are, making egg hunting of this sort pointless.

However, `RtlUserThreadStart` can lead us to where we want to go. This function has outgoing calls leading to `NtProtectVirtualMemory`, which can be used to release the `PAGE_GUARD` flag on the EAT. The call chain is as follows: 

```
->RtlUserThreadStart
  ->RtlExitUserThread
    ->LdrShutdownThread
      ->RtlpFlsDataCleanup
        ->RtlFreeHeap
          ->RtlpFreeHeapInternal
            ->NtProtectVirtualMemory
```

We can scan calls through this chain to arrive at the destination. However, the more calls and the larger the function, the less likely this is to work.

```C
    PVOID pRtlExitUserThread = ScanForCallInstruction((PBYTE)pRtlUserThreadStart, 0x50, 3);
    PVOID pLdrShutdownThreadCall = ScanForCallInstruction((PBYTE)pRtlExitUserThread, 0x50, 2);
    PVOID RtlpFlsDataCleanup = ScanForCallInstruction((PBYTE)pLdrShutdownThreadCall, 0x50, 1);
    PVOID pRtlFreeHeap = ScanForCallInstruction((PBYTE)RtlpFlsDataCleanup, 0x200, 7);
    PVOID pRtlpFreeHeapInternal = ScanForCallInstruction((PBYTE)pRtlFreeHeap, 0x200, 5);
    PVOID pNtProtectVirtualMemory= ScanForCallInstruction(((PBYTE)pRtlpFreeHeapInternal), 0x200, ...);
```

Unfortunately, `pRtlpFreeHeapInternal` is a mess of a run-on function. The likelihood of following this call chain correctly to `NtProtectVirtualMemory` outside of a lab is very low. The best case wrong answer is finding the wrong function. The worst case is misinterpring an `e8` byte in an operand as a `CALL` and following its target to an invalid memory location, creashing the program. My initial idea was to check if any of these functions were in the CFG bitmap, but it turns out none of them are.

Regardless, the objectives that we want to achieve are twofold:

1. Do not crash the program
2. Find the right address `NtProtectVirtualMemory`

To this end we can employ some heuristic checks. The most important thing is to avoid a crash. If we fail to find our target, we want to be able to exit gracefully. Some options we have are:

1. Check the 32-bit relative offset we think is a target function, making sure it is not zero or in an unreasonable range.
2. Make sure the potential call target is in the `.text` section. For NTDLL, `.text` is the first section, meaning we can easily hunt for it starting from the call site. Note that if the guard page extends to section headers, we have to skip this check.
3. Check if the bytes before and after the potential call are likely to be valid instructions. `nop` and `int3` are some good candidates to check against.


With these checks, we can predict with high certainty that a memory access at the target will not trigger a crash. This is good, because we can then check if the instructions at the call looks valid by searching for common prolog bytes.

These checks will go a long way to make sure we don't trigger a crash. Putting these together, we can scan reliably down any call tree until we find `NtProtectVirtualMemory`.

However, we must note two more things:

1. This method is not generic and still depends on the position of the `e8` call in the code.
2. We are expecting an anti-malware hardened environment, meaning `NtProtectVirtualMemory` may be hooked.

Lets suppose we arrive at `NtProtectVirtualMemory`. The AM product has placed a hook there, meaning our very strange and (now) non-unwindable call stack will access that hook if we attempt to execute it. However, we have a high certainty this hook location is `NtProtectVirtualMemory`.

Conveniently, NTDLL NT API system call functions are neatly organized, and the likelihood that the functions surrounding our target are very unlikely to also be hooked. For example, if we find a hook we can simply traverse backwards to the next system call handler, and discover the previous system call number and then increment it to get the correct result. Heuristics to reduce error here also exist here, as we can be fairly certain the system calls surrounding `NtProtectVirtualMemory` are not hooked on most versions (but `NtProtectVirtualMemory` itself is), an that its system call number is likely to fall around `0x50` (it has been this value since Windows 10 1507).

From here, we are free to ROP our way to a guardless EAT, and continue our activities in more interesting ways.

### Now Make It Generic

Actually, given the fact we can reliably predict whether a system call is `NtProtectVirtualMemory`, we could just hard code it -- but wheres the fun there? Instead, we can put together the efforts so far and just write a generic function to go and find it for us. While system call numbers can and will change, if we study (like we have) patterns in hooking, historic values, and valid function identification, we can easily arrive at a small, generic function of this sort.




## Moving Beyond NTDLL

Although known since at least 2006, a somewhat forgotten component of ntdll called `ntdll!LdrpHashTable` conveniently exists which can be used as an alternative to the ordinary PEB structures to get the addresses of loaded modules, and works in essentially the same way {{< citation >}}http://www.ivanlef0u.tuxfamily.org/?p=365{{< /citation >}}. Conveniently, the address of this global variable is located in proximity to `ntdll!FastPebLock` on some versions of Windows (plus `0x60` in my case).

As it is just a linked list of `LDR_DATA_TABLE_ENTRY`, traversing it is the same as the normal method:

```C
#include <windows.h>
#include <stdio.h>
#include "nt.h"

INT __stdcall main() {
    // Access the PEB
    _PPEB peb = (_PPEB)__readgsqword(0x60);

    // Access the FastPebLock from the PEB
    PVOID pFastPebLock = peb->pFastPebLock;

    // Calculate the address of LdrpHashTable from pFastPebLock
    PLIST_ENTRY pLdrpHashTable = (PLIST_ENTRY)((PBYTE)pFastPebLock + 0x60);

    // Define the number of entries in the hash table
    const int hashTableSize = 32;

    // Traverse the hash table
    for (int i = 0; i < hashTableSize; i++) {
        // Calculate the address of the current LIST_ENTRY
        PLIST_ENTRY currentEntry = pLdrpHashTable + i;

        printf("Entry %d <- %p:\n", i, (PVOID)currentEntry);

        // Traverse the list at this hash table index
        PLIST_ENTRY entry = currentEntry->Flink;
        while (entry != currentEntry) {
            PLDR_DATA_TABLE_ENTRY ldrEntry = CONTAINING_RECORD(
                entry, LDR_DATA_TABLE_ENTRY, HashTableEntry);

            // Print the module information
            printf("  Module Base: %p\n", ldrEntry->DllBase);
            printf("  Module EntryPoint: %p\n", ldrEntry->EntryPoint);
            printf("  Module Size: 0x%x\n", ldrEntry->SizeOfImage);
            printf("  Full DLL Name: %wZ\n", &ldrEntry->FullDllName);
            printf("  Base DLL Name: %wZ\n", &ldrEntry->BaseDllName);
            printf("  Flags: 0x%x\n", ldrEntry->Flags);
            printf("  Load Count: %d\n", ldrEntry->LoadCount);
            printf("  Time Date Stamp: 0x%x\n", ldrEntry->TimeDateStamp);

            // Move to the next entry in the list
            entry = entry->Flink;
        }

        // Check if the entry is self-referential (empty list)
        if (currentEntry->Flink == currentEntry 
            && currentEntry->Blink == currentEntry) 
        {
            printf("  (Empty List)\n");
        }
    }

    return 0;
}
```

Of course static offsets are a dangerous game, but we can employ a few heuristics to check whether a nearby chunk of data might be what were looking for. First, the array of `LIST_ENTRY` that the table is comprised of will always be `32` entries in length. Second, the table should always contain valid pointers, even if a given entry is "empty", so to speak. Instead of real forward and back links, an "empty" entry will point to itself. Both of these properties can be safely checked without dereferencing any pointers or accessing non-readable memory, as the `FastPebLock` global is unlikely to be anywhere near a problematic boundary.

## Notes

- http://redplait.blogspot.com/2013/08/how-to-find-ntdllldrphashtable.html
- http://www.ivanlef0u.tuxfamily.org/?p=365
