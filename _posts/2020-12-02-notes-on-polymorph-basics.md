```asm
;  <polytest.asm>   -   polytest source
;
;  This file tests polymorphic code generation.
;
;  Distilling the poly engine into three components according to [1]:
;  the first component of the engine is a random number generator. 
;  Easy enough. The second is a junk code generator. Slightly harder.
;  The last component is a decryptor generator. Enough said.
;
;  Focusing on the last of the three first - the decryptor generator -
;  According to [1] the algorithm is as follows:
;       1. Select random set of registers
;       2. Choose a compressed pre-coded decryptor (aha!)
;       3. Enter a loop where junk code is added to the real decryptor
;
;  This is also the part that confuses me though... Before even adding
;  junk code, how is the pre-coded decryptor made compatible with the
;  random selection of registers? From what I understand from [1], it
;  appears that the polymorphic vxer will take advantage of patterns
;  in opcodes related to registers/addressing modes. This is not a 
;  trivial detail but in my experience most other sources see to gloss
;  over it. I could be wrong. I think it works something like this:
;
;  Each basic instruction in (for example) x86 64-bit mode has
;  different bits set for different addressing modes. Take XOR
;  for example [5]:
;
;       hex      bin       mode operand 1   mode operand 2
;       0x30     110000    r/m8             r8
;       0x31     110001    r/m16/32/64      r16/32/64
;       0x32     110010    r8               r/m8
;       0x33     110011    r16/32/64        r/m16/32/64
;       0x34     110100    AL               imm8
;       0x35     110101    rAX              imm16/32
;   
;  The commonality between all six instructions is they begin with
;  the first two bits set and the third unset. What differs between
;  them is the last three bits, each apparently indicating a different
;  addressing mode.
;
;  In [1], the author mentions building a 'skeleton instruction table'.
;  Cursory internet searches don't turn up anything like this. Down in
;  the deep I'm sure there's some somewhere... But either way, for my 
;  purposes, I need to create one. To start off with some quick wins, it
;  is readily apparent from [5] that ADD, OR, ADC, SBB, AND, SUB, XOR,
;  and CMP share close opcode values for each addressing mode, (off by 1).
;  But to build a skeleton table, we need only pick out the first
;  examples of these. To make things easier, these groups of different 
;  opcodes for each operation are aligned nicely (0x00-0x08, 0x1-=0x0d)
;  Other opcodes aren't as neatly organized (e.g. PUSH, POP). Regardless,
;  just by using [5] we can simply pick out the skeleton instructions 
;  we need:
;
;       hex      opcode
;       0x00     ADD    
;       0x08     OR
;       0x10     ADC
;       0x18     SBB
;       0x20     AND
;       0x28     SUB
;       0x30     XOR
;       0x38     CMP
;       0x88     MOV (standard variations)
;
;  This is only a sample of opcodes with predictible patterns for 
;  opcode extensions in the 'ModR/M' byte. Using these 'skeleton' 
;  opcodes, one can feasibly imagine being given a register - such
;  as those randomly chosen for the decryptor - and operating on it
;  freely with the knowledge of the opcode extension patterns in hand.
;
;  References:
;   [1] https://vx-underground.org/archive/VxHeaven/lib/vbb01.html
;   [2] https://vx-underground.org/archive/VxHeaven/lib/vda01.html
;   [3] https://paul.bone.id.au/blog/2018/09/05/x86-addressing/
;   [4] https://www.agner.org/optimize/instruction_tables.pdf
;   [5] http://ref.x86asm.net/coder64.html
;   [6] https://vx-underground.org/archive/VxHeaven/lib/vmn04.html
;   [7] https://harrisonwl.github.io/assets/courses/malware/spring2017/slides/FinalWeeks/EncryptedOligomorphic.pdf
;
;  Not directly related but cool:
;   [i] https://github.com/Battelle/sandsifter


option win64:3      ; init shadow space, reserve stack at PROC level

_DATA$00 SEGMENT PAGE 'DATA'

_DATA$00 ENDS

_TEXT$00 SEGMENT ALIGN(10h) 'CODE' READ WRITE EXECUTE

    Main PROC	
        call    simple_substitution_cipher
        call    simple_substitution_cipher
        ret
    Main ENDP

;-----------------------------------------------------------------------------
;  Encryption Primitives
;-----------------------------------------------------------------------------
    
;  Simple substition encryptor [6]
;
simple_substitution_cipher:
    simple_substitution_cipher_setup:
        ;  Calculate payload body size in words
        mov     rbx, offset payload_code
        mov     rcx, offset payload_code_ends
        sub     rcx, rbx
        shr     cx, 1

        mov     rsi, rbx                                ;  source = start of encrypted code
        mov     rdi, rsi                                ;  destination = same as the source
        mov     rbx, 029Ah                              ;  rbx = key
        xor     rax, rax

    simple_substitution_cipher_loop_begin:
        lodsw                                           ;  MOV's word from [si] to ax, and increases si by 2
        xor     ax, bx                                  ;  The actual decryption
        stosw                                           ;  MOV's word from ax to [di], and increases di by 2
                                                        ;  Notice the segment must be marked RWX to modify the code
        loop    simple_substitution_cipher_loop_begin   ;  DEC's cx, and jumps to start_loop if CX > 0
    simple_substitution_cipher_done:
        ret

;-----------------------------------------------------------------------------
;  Payload Code
;-----------------------------------------------------------------------------

payload_code:
    xor     rax, rax
    inc     rax 
    shl     rax, 2
    nop
    nop
    xor     rax, rax
    ret

payload_code_ends:

_TEXT$00 ENDS

END
```
