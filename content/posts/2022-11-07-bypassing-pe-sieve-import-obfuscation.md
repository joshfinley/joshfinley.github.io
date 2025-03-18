+++
title = 'Dynamic Import Obfuscation: Evading Memory Analysis'
date = 2024-05-01 11:30:42
draft = false
+++

> This article explores a technique for obfuscating dynamic imports in Windows assembly code to evade memory analysis tools. By encoding function pointers and API hashes at rest, we can make automated memory scanning tools less effective at identifying dynamically resolved APIs. While the technique has legitimate uses for software protection, understanding these methods is also valuable for those analyzing potentially suspicious code. The implementation demonstrates both assembly-level techniques and shows how similar results can be achieved in C++ with modern language features.

## Introduction

Dynamic API resolution is a common technique used in Windows programming. Rather than linking to external functions at compile time, the code resolves function addresses at runtime by loading the appropriate DLL and looking up the functions by name or ordinal. This approach offers flexibility and can help reduce binary size by only loading what's needed.

However, this technique has become a signature of certain types of software. Memory analysis tools like Hasherezade's pe-sieve can easily identify and recover dynamic Import Address Tables (IATs) because they have a recognizable pattern in memory, making them almost as easy to detect as traditional statically linked imports.

Thinking about this problem a few months ago, I wondered: how difficult would it be to evade these analysis techniques? It turns out, not very difficult at all.

## The Problem with Plain Dynamic Imports

When a program uses dynamic imports, it typically:

1. Loads a DLL with `LoadLibrary`
2. Resolves function addresses with `GetProcAddress`
3. Stores these addresses in a table or variables for later use

These stored addresses are essentially pointers to the actual functions inside the loaded modules. Memory analysis tools can scan process memory looking for values that match the address ranges of loaded modules, allowing them to reconstruct what APIs the program is using.

Here's what this looks like when pe-sieve scans a process:

```
# pe-sieve64.exe /imp 1 /pid xxx
57038,7ffffd65f0b0,kernel32.GetModuleHandleA #639
57040,7ffffd65aec0,kernel32.GetProcAddress #697
57048,7ffffd6604f0,kernel32.LoadLibraryA #969
57050,7ffffd6a0ef0,kernel32.CopyFileA #172
57058,7ffffd65fee0,kernel32.LoadLibraryW #972
```

The tool immediately identifies dynamically imported functions, making this technique less effective for hiding what your code actually does.

## A Simple Solution: Encoding Pointers at Rest

The solution I implemented is straightforward: never store function pointers in their raw form. Instead, encode them using a consistent algorithm that can be quickly reversed when the function needs to be called.

In my implementation, I've used a simple XOR encoding with a random mask that's determined at assembly time. The key insights are:

1. Function pointers are meaningless until used to make a call
2. We can transform these pointers in any reversible way
3. The transformation can be quick to apply and reverse

By doing this, scanning tools no longer see valid pointers to module address ranges—they just see seemingly random data.

## Implementation in Assembly

Let's look at the assembly implementation to understand the approach better. First, we define our data structures:

```asm
dynimp_entry struct                         ; dynamic import table entry        
    address qword ?                         ; our encoded function pointer      
dynimp_entry ends                           
                                           
dynimp struct                               ; our dynamic import table          
    entries qword ?                         ; pointer to entries                
    len     dword ?                         ; number of entries                 
dynimp ends                                
```

The core of the technique is in the `mask_ptr` function, which both encodes and decodes function pointers:

```asm
mask_ptr proc fastcall value:qword          
    push    rbx                             
    mov     ebx, random_mask                ; rbx is the mask                   
    mov     rax, rcx                        ; rax is the address                
    xor     ecx, ecx                        ; rcx is the counter                
_loop:                                      
    cmp     ecx, 8                          ; eight is sufficient               
    je      _done                           
    xor     rax, rbx                        
    inc     ecx                             
    shl     rbx, cl                         ; shift the mask over by the rcx    
    jmp     _loop                           ; next operation                    
_done:                                      
    pop     rbx                             
    ret                                     ; return the enc/dec address        
mask_ptr endp                               
```

This function takes a pointer value, applies an XOR operation with a shifting mask, and returns the encoded or decoded result. The beauty of this approach is that applying the same operation twice returns the original value—perfect for encoding and decoding.

To use this, we:
1. Resolve the function address normally
2. Encode it with `mask_ptr` before storing
3. Decode it with the same function before calling

## Hiding API Hashes

Another aspect of this technique involves the hashes used to identify API functions. Traditional dynamic resolution often uses hardcoded hashes that can be identified and reverse-engineered. These hashes might even exist in databases of known API signatures.

My implementation masks these values too:

```asm
random_mask     equ static_rnd(0xffffffff)
hash_basis      equ            0xC59D1C81  xor random_mask
hash_prime      equ            0x01000193  xor random_mask
```

By XORing the hash values with a random mask determined at assembly time, we ensure that even if someone is looking for known API hash values, they won't find them in their expected form.

When we need to use these values, we simply XOR them again with the same mask:

```asm
mov     ecx, edx                        
xor     ecx, random_mask                ; decode the hash basis
```

This approach changes the actual binary constants in the compiled code without affecting the runtime behavior.

## C++ Implementation

This technique isn't limited to assembly. Modern C++ provides elegant ways to implement the same concepts using templates and constant expressions. Here's a simplified example:

```cpp
#define DYNIMP( x )      decltype( &x ) x
#define D_TYPE( x )     (decltype( &x ))
#define D_XOR_KEY       RND_XOR(0xffff)   // constexpr function call

#define D_EXEC( e, ... ) \
   ( ( decltype(e)((QWORD)(e) ^ D_XOR_KEY) )(__VA_ARGS__) )

// Usage:
D_EXEC(Api->Ntdll.Entries[idx], args...);
```

The technique uses C++'s `decltype` to determine the correct function pointer type, and then uses XOR for encoding and decoding. The `D_EXEC` macro handles decoding the pointer and making the function call in a single step.

## Advanced Obfuscation Techniques

The code sample also hints at more advanced techniques:

1. **Runtime-derived encoding keys**: Like the BlackMatter ransomware, we could generate encoding keys at runtime based on system properties, making each instance unique.

2. **Polymorphic code generation**: The assembly-time macros at the end of the file provide a framework for generating junk code and creating polymorphic variants of the same functionality.

3. **Instruction encoding variations**: By leveraging different instruction encodings that perform the same operations, we can create functionally identical but byte-different implementations.

These techniques add layers of complexity that make automated analysis even more challenging.

## Practical Implications

While this approach effectively evades memory scanning tools, it's worth considering the broader implications:

### Legitimate Uses

- **Software protection**: Preventing reverse engineering of proprietary algorithms
- **License enforcement**: Making it harder to bypass license checks
- **Self-defense mechanisms**: Protecting security software from tampering

### Defensive Considerations

For those analyzing potentially suspicious code:

1. **Look beyond simple pointer scanning**: Check for patterns of encoding/decoding before API calls
2. **Memory write tracking**: Monitor for consistent patterns of memory manipulation before function calls
3. **Behavioral analysis**: Focus on what the code does, not just what imports it uses

## Conclusion

Dynamic import obfuscation represents a simple yet effective technique for evading memory analysis tools. By never storing function pointers or API hashes in their raw form, we can make automated scanning significantly less effective.

The implementation demonstrated here is relatively straightforward, using XOR operations with a shifting mask to encode and decode values on demand. More sophisticated approaches could incorporate runtime-derived keys, polymorphic code generation, and other anti-analysis techniques.

While these methods have legitimate applications in software protection, understanding them is also valuable for security researchers and analysts. As with many security techniques, awareness of the approach is the first step toward developing effective countermeasures.

The cat-and-mouse game continues—as analysis tools improve, obfuscation techniques will evolve in response. This particular technique simply demonstrates how a small change in implementation can have a significant impact on detectability.

{{< footnote >}}The assembly code examples in this post use MASM64/UASM syntax. The techniques can be adapted to other assembly dialects or higher-level languages with appropriate modifications. The static_rnd macro used for compile-time randomization is credited to mabdelouahab@masm32.com.{{< /footnote >}}
