+++

title = "MASM64 Peb Walking and Export Resolution"
date = 2020-09-04 00:05:29 

+++

Using the PEB as a position-independent means of finding exports is not new. As early as the late 90's, malware authors have been accessing and using the PEB for a variety of purposes [1]. Using it to resolve exports from ntdll.dll, kernel32.dll, etc. has also been documented elsewhere repeatedly [2]. Still, most of the existing examples are in 32-bit assembly, and there are fewer examples in 64-bit. But the world has mostly moved on to 64-bit. Am0nsec [3] demonstrates the most readable and comprehensive approach I have yet found for MASM64, but it is designed specifically for populating tables of function addresses and syscall numbers (the 'Hells Gate' tecnique). This article simply descibes a general adaptation of part of [3] - almost all of the code is the exact same, but parts have been changed to make a general-purpose function for iterating over a module's exports to find a target function's address.

# GetExport prototype

We can declare the prototype for this function to be:

```c
// Given the djb2 hash of the target function name and its parent module base addres, resolve its virtual address
__fastcall uint64_ptr GetExport(long djb2_hash, long lpModuleBase);
```

## Finding export directory iterables

Inside the procedure body, first we need to resolve the following address:

- `IMAGE_EXPORT_DIRECTORY.AddressOfNames`
- `IMAGE_EXPORT_DIRECTORY.AddressOfFunctions`
- `IMAGE_EXPORT_DIRECTORY.AddressOfNameOrdinals`

The HellsGate implementation does all of this for us very nicely:

```asm
; in proc GetExport
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

```

## Search loop

This is where things differ slightly. Instead of identifying predetermined syscall functions and their respective syscall values, we loop over the export table and look for our target (passed in `ecx`). If we find a function name whose DJB2 hash matches the target, all we have to do is fixup its virtual address and return it in `rax`.

```
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
```

```
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
```

## DJB2 modifications

This implentation requries a slight modification to the djb2 hashing implementation. We need it to take a target hash and a source string and determine if the latter's hash is equivalent to the former. This can be done as such:

```
;-----------------------------------------------------------------------------
; djb2_compare(rcx=target_hash, rsi=source_string);
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
```

## Conclusion

The sum of these parts is a general-purpose function for finding functions from a module's export directory, without string reliance. Of course, credit for nearly all of these implementation details goes to am0nsec.

## References

[1] https://modexp.wordpress.com/2017/01/15/shellcode-resolving-api-addresses/

[2] https://idafchev.github.io/exploit/2017/09/26/writing_windows_shellcode.html

[3] https://github.com/am0nsec/vx/blob/master/Injector.Win64.HellsGate/HELLSGATE.ASM
