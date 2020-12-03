```asm
;  <ganymede.asm>   -   Ganymede source
;                         Copyright (c) 2020 by Lucroid.
;
;  This file references[3] to create a fully working demonstration
;  of x64 PEB walking and PE export address resolution. The code
;  could easily be adapted to be completely position independent.
;
;  The author assumes no responsibility for any damage caused by this
;  program, incidental or otherwise.  This program is intended for 
;  research purposes only.

;   References:
;    [1] https://modexp.wordpress.com/2017/01/15/shellcode-resolving-api-addresses/
;    [2] https://idafchev.github.io/exploit/2017/09/26/writing_windows_shellcode.html
;    [3] https://github.com/am0nsec/vx/blob/master/Injector.Win64.HellsGate/HELLSGATE.ASM#L92

INCLUDE ./windef.inc
INCLUDE ./ganymede.inc

_DATA$00 SEGMENT PAGE 'DATA'
    hConsoleOutput                QWORD ?
    NumberOfCharsWritten          QWORD ?
    dwStringSize                  DWORD ?
    bResult                       BYTE 0h
    lpDirectoryName               DB MAX_PATH dup(0)
    strKernel32                   DB "Kernel32.dll", 0

    VFuncTable                    VTABLE <>

    STD_OUTPUT_HANDLE             DWORD -11
_DATA$00 ENDS

_TEXT$00 SEGMENT ALIGN(10h) 'CODE'

    Ganymede PROC
        push    rbp                 ; Frame pointer
        mov     rbp, rsp            ; Stack pointer
        sub     rsp, 30h            ; Room for shadow stack

;--------------------------------------------------------------------------------------------------
; Setup Required Functions
;--------------------------------------------------------------------------------------------------
        mov     r8, gs:[60h]                                                  ; Get process environment block (PEB)
        cmp     [r8].PEB.OSMajorVersion, 0Ah                                  ; Get current process base address
        jne     _failure                                                      ; Exit if not Windows 10

        ; Get the base address of kernel32
        mov     r8, [r8].PEB.Ldr                                              ;
        mov     r8, [r8].PEB_LDR_DATA.InMemoryOrderModuleList.Flink - 10h     ; First loaded module: ganymede.exe
        mov     r8, [r8].LDR_DATA_TABLE_ENTRY.InMemoryOrderLinks.Flink - 10h  ; Second loaded module: ntdll.dll
        mov     r8, [r8].LDR_DATA_TABLE_ENTRY.InMemoryOrderLinks.Flink - 10h  ; Third Loaded module: kernel32.dll
        mov     r8, [r8].LDR_DATA_TABLE_ENTRY.DllBase                         ; Image base of the module
        mov     r9, r8                                                        ; Store for later use

        ; Load function hashes into virtual function table
        mov     VFuncTable.GetProcAddress.dwHash,   00325FA29Bh               ; DJB2 hash of GetProcAddress
        mov     VFuncTable.GetModuleHandle.dwHash,  00405AF5EAh               ; DJB2 hash of GetModuleHandle
        mov     VFuncTable.LoadLibraryA.dwHash,     00D615C977h               ; DJB2 hash of LoadLibraryA

        mov     rcx, qword ptr VFuncTable.GetProcAddress.dwHash               ; Load the DJB2 hash into param1
        mov     rdx, r9                                                       ; Load the base address into param2
        call    GetExport                                                     ; Search for the function in kernel32
        mov     VFuncTable.GetProcAddress.pAddress, rax                       ; Store the result in the virtual function table

        mov     rcx, qword ptr VFuncTable.GetModuleHandle.dwHash              ; Load the DJB2 hash into param1
        mov     rdx, r9                                                       ; Load the base address into param2
        call    GetExport                                                     ; Search for the function in kernel32 
        mov     VFuncTable.GetModuleHandle.pAddress, rax

        mov     rcx, qword ptr VFuncTable.LoadLibraryA.dwHash                 ; Load the DJB2 hash into param1
        mov     rdx, r9                                                       ; Load the base address into param2
        call    GetExport                                                     ; Search for the function in kernel32 
        mov     VFuncTable.LoadLibraryA.pAddress, rax

        lea     rcx, qword ptr strKernel32
        push    rcx
        and     rsp, not 8
        call    rax

        jmp     _prologue
;--------------------------------------------------------------------------------------------------
;  Exit & Cleanup
;--------------------------------------------------------------------------------------------------
_failure:
        xor     rax, rax
        ret
_prologue:
        xor     rax, rax
        mov     al, bResult         ;
        mov     rsp, rbp            ;
        pop     rbp                 ;
        ret                         ;
    Ganymede ENDP

;--------------------------------------------------------------------------------------------------
;  Functions
;--------------------------------------------------------------------------------------------------

    ; fastcall void * GetWinFunc(byte* FuncHash, int * BaseAddress);
    ;
    ; Description:  Given the name of a function and the base address of its
    ;               parent module, resolve its address and return in rax
    ;
    GetExport PROC
        push    r12
        push    r13
        push    r14
        push    rsi
        ; End prolog

        mov     r10d, ecx
        mov     rbx, rdx
        mov     r8, rdx
        cmp     [r8].IMAGE_DOS_HEADER.e_magic, 5A4Dh                          ; DOS Header --> MZ
        jne     _getexport_failure

        mov     ebx, [r8].IMAGE_DOS_HEADER.e_lfanew                           ; RVA of IMAGE_NT_HEADERS64
        add     r8, rbx                                                       ;
        cmp     [r8].IMAGE_NT_HEADERS64.Signature, 00004550h                  ; NT Header --> PE00
        jne     _getexport_failure

        mov     ebx, IMAGE_NT_HEADERS64.OptionalHeader                        ; RVA of IMAGE_OPTIONAL_HEADER64
        add     r8, rbx                                                       ;
        cmp     [r8].IMAGE_OPTIONAL_HEADER64.Magic, 20bh                      ; Optional header --> 0x20b
        jne     _getexport_failure

        lea     r8, [r8].IMAGE_OPTIONAL_HEADER64.DataDirectory                ; First entry of the DataDirectory array
        mov     ebx, [r8].IMAGE_DATA_DIRECTORY.VirtualAddress                 ; RVA of IMAGE_EXPORT_DIRECTORY
        mov     r8, r9                                                        ; ImageBase
        add     r8, rbx                                                       ; Module + RVA

        mov     ebx, [r8].IMAGE_EXPORT_DIRECTORY.AddressOfNames               ; Address of the function name
        mov     r12, r9                                                       ; Function name RVA
        add     r12, rbx                                                      ; ImageBase + RVA

        mov     ebx, [r8].IMAGE_EXPORT_DIRECTORY.AddressOfFunctions           ; Address of function pointers
        mov     r13, r9                                                       ;
        add     r13, rbx                                                      ;

        mov     ebx, [r8].IMAGE_EXPORT_DIRECTORY.AddressOfNameOrdinals        ; Address of function ordinals
        mov     r14, r9                                                       ;
        add     r14, rbx                                                      ;

        mov     ecx, [r8].IMAGE_EXPORT_DIRECTORY.NumberOfNames                ; Total number of named functions

        xor     rax, rax                                                      ; Set counter to 0
_function_address_search:
        mov     rbx, 4h                                                       ; sizeof(DWORD)
        imul    rbx, rax                                                      ; Get address of next entry
        cmp     eax, ecx                                                      ; Check if rax is still in the range of the export ordinals
        jg      _getexport_failure                                            ; If exceeded, the export could not be found
        mov     esi, dword ptr [rbx + r12]                                    ; Set esi to the name RVA
        add     rsi, r9                                                       ; Add it to the imagebase

        push    rax                                                           ; Store the counter
        mov     edx, r10d                                                     ; Load the target hash
        call    _djb2_compare                                                 ; Check the hashes

        mov     rdx, rax                                                      ; Store the result
        pop     rax                                                           ; Restore the counter
        inc     ax
        test    dx, dx
        jnz     _function_address_search                                      ; If the hashes match, resolve the function's address

_get_function_address:
        ;mov rcx, 2h                                                          ; sizeof(WORD)
        ;imul rcx, rax                                                        ; RCX * sizeof(WORD)
        ;mov ax, [r14 + rax]                                                  ; AX = function ordinal
        dec     rax

        imul    rax, 4                                                        ; sizeof(DWORD) * ordinal
        mov     eax, [r13 + rax]                                              ; RVA of function
        mov     rbx, r9                                                       ; RBX = ImageBase
        add     rbx, rax                                                      ; RBX = address of function

        mov     rax, rbx                                                      ; Set return value to function address
        jmp     _getexport_epilog

_getexport_failure:
        mov     rax, 1

_getexport_epilog:
        pop     rsi
        pop     r14
        pop     r13
        pop     r12
        ret

    GetExport ENDP

;-----------------------------------------------------------------------------
; djb2_compare(rcx=source_hash, rsi=target_string);
;-----------------------------------------------------------------------------
_djb2_compare:
        push    r10
        mov     rbp, rsp

        mov     r10d, 5381h                                                   ; hash = 0x5381
_djb2_loop:
        mov     r11d, r10d                                                    ; Store original hash value for later
        shl     r10d, 5                                                       ; hash << 5
        add     r10d, r11d                                                    ; (hash << 5) + hash

        xor     r11d, r11d                                                    ; Clean temporary hash value
        mov     r11b, byte ptr [rsi]                                          ; Get ASCII char
        add     r10d, r11d                                                    ; ((hash << 5) + hash) + char

        inc     rsi                                                           ; Next string char
        cmp     byte ptr [rsi], 00h                                           ; End of string

        jne     _djb2_loop
        xor     r10d, edx                                                     ; Check if hashes match
        jz      _djb2_match
        mov     rax, 1
        jmp     _djb2_epilog

_djb2_match:
        mov     rax, 0                                                        ; Set status to ERROR_SUCCESS
_djb2_epilog:
        mov     rsp, rbp
        pop     r10
        ret

_TEXT$00 ENDS

END
```
