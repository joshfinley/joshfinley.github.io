+++
title = 'PEB-less GetModuleHandle'
date = 2023-10-17T11:09:58-05:00
draft = false
+++

## Introduction

Native Windows code is overwhelmingly position-dependant. This is the case for a multitude of reasons, including legacy support, performance, and simplicity. On the other hand, this simultaneously introduces challenges for both attack and defense. For what is now decades, Windows malware has often required some degree of position independence, especially in shellcode and first-stage payloads. Additionally, due to issues of stealth and evasion, malware must frequently work without the aid of conveniences offered by the operating system and external libraries. Examples include the typical utilities that allow dynamic dependency resolution.

This article reviews standard methods for retrieving module base addresses and introduces a new method that does not rely on API calls or the Process Environment Block (PEB){{< footnote >}}Unless otherwise noted, all testing was performed on Windows 10 19045 with the bottom-up randomization and high-entropy ASLR enabled.{{< /footnote >}}. It is introduced as *Module Discovery by Code Traversal*. This methods relies only on information available to the running code is suitable for use under certain circumstances where access to API calls or the Process Environment Block is impossible or unwanted. The method does have its own limitations, but it is fairly simple and has unique advantages and disadvantages in certain situations.

## Method Review

***GetModuleHandle***

In native Windows code, the most basic method of retrieving a module base is using the Windows API `GetModuleHandle`. When called, this function does one of two things:

1. If passed a `NULL` argument, get the current image base from a global variable referencing the Process Environment Block data structure (PEB) and accessing the offset `0x10` , correlating to `PPEB->ImageBase` (Windows 10 19045) and return the address.
2. Call a second function from `ntdll` to locate and return the image base of a separate module.

In the second case, `GetModuleHandle` will call `LdrGetDllHandle`.`LdrGetDllHandle` lives in `ntdll` and itself diverts to `LdrGetDllHandleEx`. This will kick off a series of calls that will eventually access the PEB to get the module base by name or path.

The conventional wisdom in malware writing is to be wary of carelessly using such procedures, because at any point in the call chain, defense tools may have inserted some sort of monitoring hook. Instead, malware authors very often opt to implement the process manually.

***Manual Module Resolution by PEB Traversal***

On x64 Windows, the PEB is a data structure accessible using the `gs` segment register. The structure contains a linked list of loaded modules and their associated information. It is therefore possible to manually traverse the data structure from user code to retrieve loaded module information.

1. Retrieve the Process Environment Block (PEB) from `gs:0x60`.
2. Obtain the head of the `InMemoryOrderModuleList` from the `LoaderData` of the PEB.
3. Initialize a loop starting from the first entry in the `InMemoryOrderModuleList`, iterating through the list until it loops back to the head.
4. In each iteration, compute the address of the current module's `LDR_MODULE` structure based on the list entry address.
5. Check if the `BaseDllName.Buffer` of the `LDR_MODULE` is not `NULL`:
  - If it is not `NULL`, convert the name to a character string.
  - Compare the names and return `BaseAddress` if they match
6. Move to the next list entry.

## Monitoring of Module Base Retrieval Methods

***API Hooking and Behavior Monitoring***

The most straightforward way of monitoring attempts to retrieve module base addresses would be with usermode hooks on the Windows and NT API procedures. One example of a behavioral check would involve checking if the `GetModuleHandle` call is in proximity to a `GetProcAddress` call, indicating dynamic API import.

***PEB Access Monitoring***

Through emulation or debugging, it is possible to monitor access to the PEB or TEB {{< citation >}}"https://github.com/mandiant/speakeasy"{{< /citation >}}. With these tools, access to PEB memory is straightforward to detect.

***Static Signatures***

Finally, a very simple detection for code accessing the PEB or TEB is to match suspicious code to a pattern matching a move operation with the x86_64 segment override prefix for the `gs` segment register. An example pattern would be something like:
```
65 48 8b * 25 60 00 00 00 00 ; PEB access using 0x65 segment override prefix
65 48 8b * 25 30 00 00 00 00 ; TEB access using 0x65 segment override prefix
```

## Module Discovery by Code Traversal
 
Given the assumption that the address is within a portable executable image in the current process memory, we can easily search backwards in memory for the base address of the module. If that module explicitly imports any functions from external dynamic libraries, the PE headers may be parsed to retrieve an address inside that module and then find its own module base. This can be repeated for every loaded module in the process.

```c++
INT main()
{
    BOOL        OK              = FALSE;
    INT         Distance        = NULL;
    QWORD_PTR   RIP             = NULL;
    QWORD_PTR   MzLoc           = NULL;
    QWORD_PTR   SearchAddr      = NULL;
    QWORD_PTR   BaseAddr        = NULL;

    BYTE MzSig[5] = { 0x4D, 0x5A, 0x90, 0x00, 0x03 };

    // 1. Get the instruction pointer (or in this case, an approximation it)
    RIP = GetInstructionPointer();
   
    // 2. Find the DOS signature of the current module
    SearchAddr = (QWORD_PTR)FindByteSig(
        RIP, MzSig, sizeof(MzSig), 0xFFFF0, TRUE, &Distance);
    if (!SearchAddr) return ERROR_NOT_FOUND;

    // 3. Find the first Kernel32 import from IAT
    SearchAddr = FindFirstModuleImport((PBYTE)SearchAddr, HASH_K32);
    if (!SearchAddr) return ERROR_NOT_FOUND;

    // 4. Find kernel32 base from the export
    SearchAddr = (QWORD_PTR)FindByteSig(
        SearchAddr, MzSig, sizeof(MzSig), 0xFFFFF, TRUE, &Distance);
    if (!SearchAddr) return ERROR_NOT_FOUND;

    // 5. Get address inside ntdll
    SearchAddr = FindFirstModuleImport((PBYTE)SearchAddr, HASH_NTDLL);
    if (!SearchAddr) return ERROR_NOT_FOUND;

    // 6. Get ntdll base
    BaseAddr = (QWORD_PTR)FindByteSig(
        SearchAddr, MzSig, sizeof(MzSig), 0xFFFFF, TRUE, &Distance);

    return ERROR_SUCCESS;
}
```

***Advantages***

This method is *almost* as robust at enabling module discovery as standard methods such as GetModuleHandle or using the PEB. The entire list of modules that are specified in a given executable's headers may be resolved without calling any APIs or accessing the PEB.

***Disadvantages***

The main downside of this method compared to traditional means is that modules loaded at runtime will not be discoverable merely by searching through the known import directories. Additionally, this method requires knowledge of an address backed by a PE image. This means that shellcode threads will need to be provided this information. Finally, there is room for error in the pattern matching and PE format parsing.

## Proof-of-Concept: PEB-Less GetModuleHandle

The following code offers a complete demonstration of a `GetModuleHandle`-alike function which uses Method 1 to locate module base addresses from a known code location (in this case `RIP`). The code will recursively search accessible module import information for the given DLL name. At no point is the PEB accessed and no API calls are used.

```c++
#include <Windows.h>

// Convenience types
#define QWORD                   DWORD64
#define QWORD_PTR               DWORD64 *

#define MAX_VISITED             124

extern "C" QWORD_PTR GetInstructionPointer();

// Find the first instance of a matching byte sequence with directionality
PVOID FindByteSig(PVOID SearchBase, PVOID Sig, INT EggSize, INT Bound, BOOL Rev)
{
    if (!Rev)
    {
        for (INT i = 0; i < Bound; i++)
        {
            if (!memcmp(&((PBYTE)SearchBase)[i], Sig, EggSize))
            {
                return &((PBYTE)SearchBase)[i];
            }
        }
    }
    else {
        for (INT i = 0; i < Bound; i++)
        {
            if (!memcmp(&((PBYTE)SearchBase)[-i], Sig, EggSize))
            {
                return &((PBYTE)SearchBase)[-i];
            }
        }
    }

    return NULL;
}

// Compare a module's reported name (Optional directory) to a string
BOOL CheckModNameByExportDir(PBYTE BaseAddr, PCHAR ModName)
{
    DWORD                   ExportDirRVA    = NULL;
    DWORD                   NameRVA         = NULL;
    PCHAR                   Name            = NULL;
    SIZE_T                  NameLength      = NULL;
    PIMAGE_DOS_HEADER       pDosHeader      = NULL;
    PIMAGE_NT_HEADERS       pNtHeaders      = NULL;
    PIMAGE_EXPORT_DIRECTORY pExportDir      = NULL;

    pDosHeader = (PIMAGE_DOS_HEADER)BaseAddr;
    if (pDosHeader->e_magic != IMAGE_DOS_SIGNATURE) return FALSE;

    pNtHeaders = (PIMAGE_NT_HEADERS)(BaseAddr + pDosHeader->e_lfanew);
    if (pNtHeaders->Signature != IMAGE_NT_SIGNATURE) return FALSE;

    ExportDirRVA = pNtHeaders->OptionalHeader.
        DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress;
    if (ExportDirRVA == 0) return FALSE;

    pExportDir = (PIMAGE_EXPORT_DIRECTORY)(BaseAddr + ExportDirRVA);

    NameRVA = pExportDir->Name;
    if (NameRVA == 0) {
        return FALSE; // No name
    }

    Name = (PCHAR)(BaseAddr + NameRVA);
    NameLength = strlen(Name);

    if (strcmp(ModName, Name) == 0)
    {
        return TRUE;
    }
    
    return FALSE;
}

// Given a base address, find the first import from a given DLL
QWORD_PTR FindFirstModuleImport(PBYTE MzLoc, PCHAR ModName)
{
    CHAR                        CurrentName[MAX_PATH];
    PIMAGE_DOS_HEADER           pDosHeader = NULL;
    PIMAGE_NT_HEADERS           pNtHeaders = NULL;
    PIMAGE_OPTIONAL_HEADER      pOptHeader = NULL;
    PIMAGE_IMPORT_DESCRIPTOR    pImportDesc = NULL;
    PCHAR                       pImportName = NULL;
    PIMAGE_THUNK_DATA           pThunk = NULL;
    PIMAGE_THUNK_DATA           pIATThunk = NULL;

    // Initialize locals
    pDosHeader = (PIMAGE_DOS_HEADER)MzLoc;

    // Validate DOS header
    if (pDosHeader->e_magic != IMAGE_DOS_SIGNATURE)
        return NULL;

    // Initialize NT Headers
    pNtHeaders = (PIMAGE_NT_HEADERS)(MzLoc + pDosHeader->e_lfanew);

    // Validate PE header
    if (pNtHeaders->Signature != IMAGE_NT_SIGNATURE)
        return NULL;

    // Initialize Optional Header
    pOptHeader = &pNtHeaders->OptionalHeader;

    // Initialize Import Descriptor
    pImportDesc = (PIMAGE_IMPORT_DESCRIPTOR)(
        MzLoc
        + pOptHeader->DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT]
        .VirtualAddress);

    while (pImportDesc && pImportDesc->Name)
    {
        pImportName = (PCHAR)(MzLoc + pImportDesc->Name);

        if (pImportName)
        {
            strcpy_s(CurrentName, sizeof(CurrentName), pImportName);
            for (int i = 0; CurrentName[i]; i++) {
                CurrentName[i] = (CHAR)tolower((unsigned char)CurrentName[i]);
            }
            if (strcmp(CurrentName, ModName) == 0)
            {
                // Get the OriginalFirstThunk
                pThunk = (PIMAGE_THUNK_DATA)(
                    MzLoc + pImportDesc->OriginalFirstThunk);
                // Get the corresponding entry in the IAT
                pIATThunk = (PIMAGE_THUNK_DATA)(
                    MzLoc + pImportDesc->FirstThunk);

                if (pThunk && pIATThunk) // Check if thunks are valid
                {
                    // Return the full VA of the first function
                    return (QWORD_PTR)(pIATThunk->u1.Function);
                }
            }
        }
        pImportDesc++;
    }

    return NULL;
}

// Function to check if a module has already been visited
bool IsModuleVisited(PVOID* Visited, int nVisited, PVOID ModBase) {
    for (int i = 0; i < nVisited; i++) {
        if (Visited[i] == ModBase) {
            return true;
        }
    }
    return false;
}

PVOID PeblessFindModuleRecursively(
    PBYTE   StartAddr, 
    PCHAR   ModName, 
    PVOID*  Visited, 
    PINT    nVisited) 
{
    DWORD                       ImportDirRVA            = NULL;    
    PCHAR                       pModuleName             = NULL;
    PVOID                       FirstImport             = NULL;
    PVOID                       FoundBase               = NULL;
    PIMAGE_DOS_HEADER           pDosHeader              = NULL;
    PIMAGE_NT_HEADERS           pNtHeaders              = NULL;
    PIMAGE_OPTIONAL_HEADER      pOptionalHeader         = NULL;
    PIMAGE_IMPORT_DESCRIPTOR    pImportDesc             = NULL;
    CHAR                        CurrentName[MAX_PATH] = { NULL };

    BYTE MzSig[5] = { 0x4D, 0x5A, 0x90, 0x00, 0x03 };
        

    if (IsModuleVisited(Visited, *nVisited, StartAddr)) {
        return NULL;  // Avoid infinite recursion
    }

    Visited[*nVisited] = StartAddr;
    (*nVisited)++;

    if (CheckModNameByExportDir(StartAddr, ModName)) {
        return StartAddr;
    }

    pDosHeader = (PIMAGE_DOS_HEADER)StartAddr;
    pNtHeaders = (PIMAGE_NT_HEADERS)(StartAddr + pDosHeader->e_lfanew);
    pOptionalHeader = &pNtHeaders->OptionalHeader;
    ImportDirRVA = pOptionalHeader->DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    pImportDesc = (PIMAGE_IMPORT_DESCRIPTOR)(StartAddr + ImportDirRVA);

    while (pImportDesc->Name) {
        pModuleName = (char*)(StartAddr + pImportDesc->Name);
        strcpy_s(CurrentName, sizeof(CurrentName), pModuleName);
        for (INT i = 0; CurrentName[i]; i++) {
            CurrentName[i] = (CHAR)tolower((unsigned char)CurrentName[i]);
        }

        FirstImport = FindFirstModuleImport(StartAddr, CurrentName);
        if (!FirstImport) {
            pImportDesc++;
            continue;
        }

        FoundBase = FindByteSig(
            FirstImport, MzSig, sizeof(MzSig), 0xFFFFF, TRUE);

        if (FoundBase) {
            FoundBase = PeblessFindModuleRecursively(
                (PBYTE)FoundBase, ModName, Visited, nVisited);
            if (FoundBase) {
                return FoundBase;
            }
        }

        pImportDesc++;
    }

    return NULL;
}

// Get a module base address without using the PEB
// NOTE: Does not locate libraries loaded with LoadLibrary
PVOID PeblessGetModuleHandle(PCHAR szModuleName) {
    PVOID   Visited[MAX_VISITED]    = { NULL };
    PBYTE   StartAddr       = NULL;
    INT     nVisited        = 0;
    BYTE    MzSig[5]        = { 0x4D, 0x5A, 0x90, 0x00, 0x03 };

    QWORD_PTR RIP = (QWORD_PTR)GetInstructionPointer();

    StartAddr = (PBYTE)FindByteSig(
        (PVOID)RIP, MzSig, sizeof(MzSig), 0xFFFFF, TRUE);

    if (szModuleName == NULL) return StartAddr;

    return PeblessFindModuleRecursively(
        StartAddr, szModuleName, Visited, &nVisited);
}

// Program entry point
INT main()
{
    PVOID BaseNtdll = PeblessGetModuleHandle((PCHAR)"ntdll.dll");
    if (!BaseNtdll) return ERROR_NOT_FOUND;

    PVOID BaseCurrent = PeblessGetModuleHandle(NULL);
    if (!BaseCurrent) return ERROR_NOT_FOUND;

    return 0;
}
```

## Speculation: Stack-Analysis for Module Identification

In addition to the first method, weaknesses in Windows ASLR may be exploited to predict valid system module addresses from data on the stack. New threads begin with `ntdll!RtlUserThreadStart` followed by `KERNEL32!BaseThreadInitThunk`. Therefore it should be possible to obtain base addresses if an ASLR attack is used. Statistical modeling of ASLR could be done to evaluate:

* Mean distance from user code to system module code
* Spread of module load locations
* Weaknesses in ASLR address range constraints for system DLLs

Testing design should account for peculiarities in Windows ASLR, such as module base reuse across processes with same names.

I performed an initial evaluation of the predictibility of system module address, but the results are not conclusive and therefore not worth sharing. 

## Conclusion

This article presented an analysis of the standard methods used to retrieve module base addresses in native Windows code, including the widely-used `GetModuleHandle` API and manual module resolution through the Process Environment Block (PEB). It also introduced a method—*Module Discovery by Code Traversal*—as an alternative that is robust yet does not rely on API calls or the PEB. This method offers unique advantages and disadvantages, depending on the constraints and requirements of the situation. 

