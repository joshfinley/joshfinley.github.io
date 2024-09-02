+++
title = 'Internals of Poylmorphic Engines'
date = 2020-12-02 00:05:28 
version = "v2"
+++

> This file documents the workings of polymorphic engines in malware, primarily focusing on historical examples implemented in x86 assembly. While modern malware favors detection reduction techniques in memory, viruses from the 1990s and early 2000s had only one main oponent -- static detections. The result of this evolutionary pressure was the development of polymorphic and metamorphic techniques, which are used to mutate the virus's byte sequence, breaking any static detections. Despite the proliferation of in-memory detection techniques, polymorphic malware retains its edge as a useful evasion even now.

## Introduction 

To understand the concept of poylmorphic code (not to be confused with the programming concept of polymorhpism), we must understand the demands and constraints of the code that it was developed for: viruses.

The goal of viral code is simple - popagate. This code mimics an organism in that it uses resources available in the environment to reproduce. An extremely simple virus might just outright replace other programs on the host machine with itself, causing destructive damage to infected machines. Instead of the original program, the viral. More commonly, viral code would exploit methods to run the original program it infected like normal, before executing the viral payload.

Antivirus tools cropped up to contend with this threat. Given the technical and technological constraints of the time, these tools would simply scan files for byte patterns of known malware, and if a match was found, delete the infected file. 

Virus developers worked around this threat by first developing code to encrypt their paloads at rest and decrypt them at runtime. They would swap out these routines with new ones as variants became detected. In this way, the precious viral infection code did not need to be replaced as signatures were released for antivirus tools. Instead, the encryption and execution routine would be replaced as needed. This type of virus was dubbed *oligomorphic*.

Shortly after, or perhaps concurrently with the first oligomorphic viruses, virus writers were already improving their tradecraft. Since the encoding stubs would quickly become detected, the next solution would be to generate a new stub automatically. This could be done for every release of the virus (creation time polymorhpishm) or on each infection and execution (execution time polymorphism). Creative programming techniques could be used to generate a new varianet of the encryption and execution code rather than require manual development. Authors of these viruses and virus development toolchains would leverage understanding of the target machine instruction set to permutate the machine code of the virus decryption and loading routines.

A few took this to the extreme, permutating the entire virus body payload on each infection, requiring no encryption (called metamorphic viruses).

This article looks at runtime polymorphism. In the simplest terms, a polymorphic virus of this sort is one that will create a new descryption routine for each infection. The control flow will resemble the following:

1. Infected host is executed
2. Hijacked control flow runs decryption routine implanted by main virus code
3. Decryption routine decrypts main virus payload and passes it control
4. Main virus payload searches for new victims
5. Main virus payload generates new decryption routine
6. Main virus payload writes encrypted copy of itself and decryption routine to new victims
7. Main virus routine overwrites control flow in victims to launch viral code.

## Defining Polymorphic Engines

Reviewing different works on polymorphic viruses will reveal a myriad of strategies virus authors would use to fool defense products. These authors were truly creative in their exploration of ways to write their viruses and make them survive in hardened environments.

According to one 1998 work from *The Black Baron*, a polymorphic engine can be distilled into three components {{< citation id="blackbaron1998" url="https://web.archive.org/web/20210227235004/https://vx-underground.org/archive/VxHeaven/lib/vbb01.html" content="The Black Baron. (1998). A general description of the methods behind a polymorph engine. VX Underground archived version." />}}:

1. Random number generator
2. Junk code generator
3. Decryptor generator

Focusing on the last of the three first -- the decryptor generator --
According to {{< citation id="blackbaron1998" />}} the algorithm is as follows:

1. Select a random set of registers
2. Choose a compressed pre-coded decryptor 
3. Enter a loop where junk code is added to the real decryptor
   (potentially unnecessary {{< citation id="vts01" url="https://vx-underground.org/archive/VxHeaven/lib/vts01.html" content="The Slammer. (n.d.). Polymorphic Engines. VX Underground (Archived version)." />}})

Compared to this sort of hacker definition, academic formalizations of polymorphic engines also exist {{< citation id="jacob2008" content="Jacob, Fillion, and Debar. Functional polymorphic engines: formalisation, implementation and use cases. Journal of Computer Virology and Hacking Techniques" />}}. These formalizations attempt to understand polymorphic malware in a scientific context.

Commercial defitions for polymorphic viruses in general have also been submitted over the years, like this Example from *Symantec*:

{{< blockquote source="Symantec. Understanding and Managing Polymorphic Viruses. VxHeven archived version." >}}
In retaliation, virus authors developed the polymorphic virus. Like an encrypted virus, a polymorphic virus includes a scrambled virus body and a decryption routine that first gains control of the computer, then decrypts the virus body. 

However, a polymorphic virus adds to these two components a third — a mutation engine that generates randomized decryption routines that change each time a virus infects a new program.
In a polymorphic virus, the mutation engine and virus body are both encrypted. When a user runs a
program infected with a polymorphic virus, the decryption routine first gains control of the computer, then decrypts both the virus body and the mutation engine. Next, the decryption routine transfers control of the computer to the virus, which locates a new program to infect
{{< /blockquote >}}

From these sources can arrive at a very general description of a polymorphic virus:

> An infectious program which spreads in an encrypted state and is also able to generate new permutations of its decryption code, as a technique to evade antivirus.

A polymorphic virus of this sort would thus appear as the following components, when attached to a host:

1. Host file, control flow hijacked to execute decryptor
2. Decryptor
3. (Encrypted) Infection code
4. (Encrypted) Decryptor generation code

```
        +-----------------------------------------------------+
        |                    Host File                        |
        |  +-----------------------------------------------+  |
        |  |  Control Flow Hijack --> [Decryptor]          |  |
        |  +-----------------------------------------------+  |
        |  |                                               |  |
        |  |  +-----------------------------------------+  |  |
        |  |  |                Decryptor                |  |  |
        |  |  +-----------------------------------------+  |  |
        |  |  |                                         |  |  |
        |  |  |  +---------------------------------+    |  |  |
        |  |  |  | (Encrypted) Infection Code      |    |  |  |
        |  |  |  +---------------------------------+    |  |  |
        |  |  |                                         |  |  |
        |  |  |  +---------------------------------+    |  |  |
        |  |  |  | (Encrypted) Decryptor Generation|    |  |  |
        |  |  |  | Code                            |    |  |  |
        |  |  |  +---------------------------------+    |  |  |
        |  |  +-----------------------------------------+  |  |
        |  +-----------------------------------------------+  |
        +-----------------------------------------------------+
```

If we accept this as a concise definition of a polymorphic virus, then the polymorphic engine (i.e., code generator, mutator, etc.) itself is the code responsible for generating unique decryptors. Then, the engine itself is a code generation mechanism, specially crafted to generate decryptors which are valid for the encrypted viral payload, and are capable of executing it.

## Encryption Primitives                       

Before the poly engine comes the encryption primitives. 

In {{< citation id="vmn04" url="https://vx-underground.org/archive/VxHeaven/lib/vmn04.html" content="MidNyte. (n.d.). Polymorphic Encryption Algorithms Part I. VX Underground (Archived version)." />}}, {{< citation id="vmn05" url="https://vx-underground.org/archive/VxHeaven/lib/vmn05.html" content="MidNyte. (n.d.). Polymorphic Encryption Algorithms Part II. VX Underground (Archived version)." />}}, and {{< citation id="vmn06" url="https://vx-underground.org/archive/VxHeaven/lib/vmn06.html" content="MidNyte. (n.d.). Polymorphic Encryption Algorithms Part III. VX Underground (Archived version)." />}}, the author 'MidNyte' discusses the fundamentals of 
encryption/enciphering in the context of the virus or poly engine.
In Part I, four x86 assembly techniques are presented. In Part II, they then present
four methods of 'armouring' the encryption. These articles seem
to have everything necessary to understand the basics of ciphers as applied to polymorphic malware.

The four ciphers presented in {{< citation id="vmn04" />}} are the following:
    - substitution
    - sliding key
    - long key
    - transposition

In {{< citation id="vmn05" />}}, the following armoring techniques are presented:
    - variable length transposition
    - boundary scrambling
    - integrity-dependent decryption
    - date-dependent decryption

While they're important, I'm going to avoid discussing the latter four techniques for the time being.

## Polymorphism Techniques

The code polymorphism mechanisms used in polymorphic engines are fourfold:

1. Permutation of the bytes of individual instruction opcodes
2. Permutation of the positions of instructions
3. Permutation of used registers
4. Insertion of garbage instructions

Different viruses may choose any combination of these techniques. For example, many polymorphic viruses opt not to include garbage instruction generation {{< footnote >}}
Garbage code generation is still code generation. At that, the quality of the garbage matters {{< citation id="vts01" />}}. It is even suggested that it is more worthwhile to use stronger and more complicated encryption than to add junk code at all {{< citation id="vts01" />}}.

One contesting idea regarding this however is the benefits of the sheer simplicity of XOR, ADD, and SUB ciphers. For example, in {{< citation id="solarwinds" url="https://vxug.fakedoma.in/samples/Exotic/UNC2452/SolarWinds%20Breach/" content="SolarWinds Breach Analysis" />}} one of the most advanced cyber attacks in history, a sliding XOR cipher was employed to success. {{< /footnote >}}.

The first three techniques are more than enough to generate semantically equivalent but signature unique ciphers. The following sections dive into how each works.

### Permutating Instruction Bytes

The mechanisms of a polymorphic engine rely on understanding of instruction encoding in order to generate valid decryptor code. By leveraging different encodings for functionally equivalent operations, code which serves the same semantic purpose may have a completely different byte sequence.

#### Opcodes

For example, most instructions in  x86_64 have different encodings for different addressing modes. Take the XOR instruction for example {{< citation id="x86asm" url="http://ref.x86asm.net/coder64.html" content="x86 Opcode and Instruction Reference" />}}:

     hex      bin       mode operand 1   mode operand 2
     0x30     110000    r/m8             r8
     0x31     110001    r/m16/32/64      r16/32/64
     0x32     110010    r8               r/m8
     0x33     110011    r16/32/64        r/m16/32/64
     0x34     110100    AL               imm8
     0x35     110101    rAX              imm16/32      
 
The commonality between all six instructions is that they begin with the first two bits set and the third unset. What differs between them is the last three bits, each indicating a different addressing mode. Suppose an example of a virus decryptor in the form of a XOR cipher. By leveraging different encodings, for one single instruction we have six different bytes. If antivirus is dependent on a specific byte being present in that position and we choose a different encoding, it will fail to detect the virus.

However, we need find permutations for most or all instructions in the decryptor. In {{< citation id="blackbaron1998" />}}, the author mentions building a 'skeleton instruction table'. What is meant by this is that most instructions will have relatively close values, and thus similar bit sequences. For example, if we examine an opcode table for x86_64,{< citation id="x86asm" />}} we can see that the instructions ADD, OR, ADC, SBB, AND, SUB, XOR, and CMP share close opcode values for each addressing mode. Thus a skeleton instruction table would simply hold the first variation, which we can OR as needed. To make things easier, these groups of different opcodes for each operation are aligned nicely (0x00-0x08, 0x1-=0x0d). Other opcodes aren't as neatly organized (e.g. PUSH, POP). Regardless, just by using {{< citation id="x86asm" />}} we can simply pick out a subset of the instruction set which applies to most simple ciphers:

```
    hex      opcode    permutation method      permutations
    0x00     ADD       Increment               6
    0x08     OR        Increment               6
    0x10     ADC       Increment               6
    0x18     SBB       Increment               6
    0x20     AND       Increment               6
    0x28     SUB       Increment               6
    0x30     XOR       Increment               6
    0x38     CMP       Increment               6
    0xe9     JMP       Increment               2
    0x0f80   JO        Increment               32
```

These 10 base instructions can thus produce 82 permutations only based on the opcode. In implementation the code signature would be even more changed due to semantic differences in conditional jump instructions and adjustments that may need to made based on the mode for each computation operation.

#### Modifiers

If we look at the encoding of real instructions from an assembled encryption loop, we can quickly see that theres much more going on than the just addressing mode variations between each instruction:

```
    a) 48 C7 C3 9A 02 00 00    // mov rbx, 29Ah  
    b) 48 29 D9                // sub rcx, rbx 
```

Why do both instructions begin with `0x48`? What does the third byte do, and how does the processor know how many bytes should be moved in `a`?

If we take the following instruction as an example, we can decode the meanings of the bytes bit positions:

-----------------------------------------------------------------------
```
                     __REX.W  
                    /   ____MOV r/m16/32/64
                   /  /  ______________Mod-Reg-R/M Byte
                  /  /  /  ,______,____________________Immediate
              a) 48 C7 C3 9A 02 00 00 
              b) 48 29 d9

     instruction         
              a) mov rbx, 29Ah              
              b) sub rcx, rbx           
         
     binary                         
                                    ______0x29a_____
     a)                            /                \
       01001000 11000111 11000011 [10011010 00000010] 00000000 000000000  
       \_____/  \_____/       \/   \__________________________________/
         |          |         |                     |    
 rex prefix      MOV           register             quad word  

     b)         
                 01001000         01010110        11001011
                 \__/wrxb         \_____/           \/ \/
          fixed___/  \_/            |               |   \             
                      |         sub immediate       rcx   rbx
         64-bit operand ('W' bit set)    
```
-----------------------------------------------------------------------

This means that in addition to the various instructions themselves, we have other opcodes which give information to the processor about the interpretation. Under x86_64, we see a REX byte prefixing some 64 bit mode operations. For instructions with variable operand encodings, we have the MOD RM byte, which holds data about operand interpretation. This means that every instruction opcode will have even more possible encodings for these surrounding bytes, offering fertile ground for even more permutations{{< footnote>}}
A note on visualizing instruction encodings with Python:
```
     # One off
     ... data = "48 C7 C3 9A 02 00 00"
     ... bytes = bytearray.fromhex((data))
     ... [print(bin(bytes[i]), end=" ") for i in range(len(bytes))]
     ...
     # As a function
     ... def bin_from_bytes(data):
     ...   bytes = bytearray.fromhex(data)
     ...   [print(bin(bytes[i]), end=" ") for i in range(len(bytes))]
```
{{< /footnote >}}.


### Permutating the Instruction Positions

In addition to opcodes and modifiers themselves, we may also add a more advanced layer of polymorphism by introducing the permutation of the positions of individual instructions. In any given cipher, some instructions can be freely before or after others, within certain bounds. Others can be moved if we introduce new code to handle the changed position, introducing even more complexity.

In one post "Lord Julus" {{< citation id="vlj04" url="https://vx-underground.org/archive/VxHeaven/lib/vlj04.html" content="Lord Julus. (n.d.). Permutation Decryptor. VX Underground (Archived version)." />}} provides a notation and description for reasoning about instruction position permutation. The following is an adaptation of the described algorithms and the permutation rules provided:

#### Cipher Algorithm Operations
-----------------------------------------------------------------------
```
decrypt proc near
    1)  mov length_register, length          get the code length       
    2)  mov pointer_register, startcode      load pointer register     
    3)  mov destination_register, startcode  load the destination reg. 
    4)  mov key_register, key                get the key               
main_loop
    5)  mov code_register, pointer_register  take an encrypted word    
    6)  call unscramble                      decrypt it (*)            
    7)  mov destination_register, code_reg.  write the decrypted word  
    8)  add key_register, key_increment      increment the key         
    9)  dec length_register                  decrement length          
    10) inc pointer_register                 increment pointer (x2)    
    11) jnz main_loop                        loop until length=0       
    12) ret                                  return pc                 
decrypt endp                                                  
```

#### Cipher Algoritm Order of Operations

1) permutable, can be placed anywhere
2) permutable, can be placed anywhere
3) permutable, can be placed anywhere
4) permutable, can be placed anywhere
5) not permutable
6) not permutable
7) permutable, can be placed anywhere after [6]
8) permutable, can be placed anywhere after [6]
9) permutable, can be placed anywhere after [6]
10) permutable, can be placed anywhere after [6]
11) not permutable
12) not permutable                                          

-----------------------------------------------------------------------

Just as in {{< citation id="vlj04" />}}, this general description of the algorithm with 
permutation rules can be used to "make a matrix of bytes". By adding notation to each semantic operation, can now describe permutations of the same algorithm that are logically equivalent but differ in signature, for example:

```
matrix a)
    permutation: [4, 1, 2, 3, 5, 6, 8, 9, 7, 10, 11, 12]
    place:       [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

matrix b)
    permutation: [3, 1, 2, 4, 5, 6, 7, 10, 8, 9, 11, 12]
    place:       [1, 2, 3, 4, 5, 6, 7, 8,  9, 10, 11, 12]
```

### Permuting Instruction Registers
 
Now that we know what logical operations must be included and have an idea of how what bit-level characteristics each instruction might have (fig 3.), the next fundamental characteristic of the polymorphic engine to understand is the random selection of registers.

Under x86_64, we have many registers to work with, but most commonly we will use the following 16:

1. RAX - Accumulator register
2. RBX - Base register
3. RCX - Counter register
4. RDX - Data register
5. RSI - Source index register
6. RDI - Destination index register
7. RBP - Base pointer register
8. RSP - Stack pointer register
9. R8 - General-purpose register
10. R9 - General-purpose register
11. R10 - General-purpose register
12. R11 - General-purpose register
13. R12 - General-purpose register
14. R13 - General-purpose register
15. R14 - General-purpose register
16. R15 - General-purpose register

To get a random register from this list, one need only to generate a random number in the range and use it as an index. From there, it must be understood how to encode instructions to use the designated register for whichever operation. In this sense, a polymorphic engine which uses register permutation will virtualize the registers it uses, providing a layer of abstraction between which registers are actually used and which are necessary.

## Conclusion

In summary, a polymorphic engine in malware is a complex mechanism designed to evade detection by traditional security measures. At its core, this engine generates unique decryption routines and cipher codes each time the malware propagates, ensuring that the malware's signature remains elusive to static signature-based scanning. By constantly permuting the decryption routine and generating new random keys for each iteration, the engine effectively obscures the true nature of the viral payload. This process not only masks the malicious code but also minimizes the likelihood that the decryptor itself will be recognized as harmful. The polymorphic engine achieves this through a dynamic reshuffling of instruction encodings and ordering, producing a virtually endless array of unique cipher variations. As a result, the malware becomes significantly harder to detect and analyze, presenting a formidable challenge for traditional antivirus solutions.