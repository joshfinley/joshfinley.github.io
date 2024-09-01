+++
title = 'Using Memory Artifacts for Position Independent Code'
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

## Thread Initialization Artifacts

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



Although known since at least 2006, a somewhat forgotten component of ntdll called `ntdll!LdrpHashTable` conveniently exists which can be used as an alternative to the ordinary PEB originating method to get the addresses of loaded modules, and works in essentially the same way {{< citation >}}http://www.ivanlef0u.tuxfamily.org/?p=365{{< /citation >}}. As it is just a linked list of `LDR_DATA_TABLE_ENTRY`, traversing it is the same an ordinary walk of the PEB loader data linked list. If we can identify the location of `ntdll!LdrpHashTable` we can skip the PEB check altogether, avoidng a possible detection on `gs` read instructions.

Of course static offsets are a dangerous game, but we can employ a few heuristics to check whether a nearby chunk of data might be what were looking for. First, the array of `LIST_ENTRY` that the table is comprised of will always be `32` entries in length. Second, the table should always contain valid pointers, even if a given entry is "empty", so to speak. Instead of real forward and back links, an "empty" entry will point to itself. Both of these properties can be safely checked without dereferencing any pointers or accessing non-readable memory.

## Notes

- http://redplait.blogspot.com/2013/08/how-to-find-ntdllldrphashtable.html
- http://www.ivanlef0u.tuxfamily.org/?p=365
