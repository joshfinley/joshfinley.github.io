+++
layout: post
title:  "Notes - Learning Rust"
date:   2022-05-18 00:05:28 -0500
description: Notes taken while diving into Rust for the first time
titleImage:
    file: 'prairie-sunset.png'
+++

## Introduction

There are tons of what to me feel like 'hype' languages cropping up these days. Things like crystal, nim, v, infinite permutations of javascript, zig...

Before I knew what they offered and the amount of work put into the ecosystems surrounding them, I felt the same way about Go and Rust.

Eventually, I learned Go and it is now probably my favorite language to actually write code in. Recently when I told a coworker as much, he retorted by saying Rust was better, and I of course ignored him and moved on. By this point, I've become aware of the important movements Rust is making within the world of software - even moving into the Linux kernel and being useable for writing Windows drivers.

Then I learned that Rust has amazing flexibility for linking, such as the following examples:

```
[build]
target = "x86_64-pc-windows-msvc"

rustflags = [
    # Pre Link Args
    "-Z", "pre-link-arg=/NOLOGO",
    "-Z", "pre-link-arg=/NXCOMPAT",
    "-Z", "pre-link-arg=/NODEFAULTLIB",
    "-Z", "pre-link-arg=/SUBSYSTEM:NATIVE",
    "-Z", "pre-link-arg=/DRIVER",
    "-Z", "pre-link-arg=/DYNAMICBASE",
    "-Z", "pre-link-arg=/MANIFEST:NO",

    # Post Link Args
    "-C", "link-arg=/OPT:REF,ICF",
    "-C", "link-arg=/ENTRY:driver_entry",
    "-C", "link-arg=/MERGE:.edata=.rdata",
    "-C", "link-arg=/MERGE:.rustc=.data",
    "-C", "link-arg=/INTEGRITYCHECK"
]
```

Meanwhile Go has a somewhat siloed compiler and linker code base, with tons of very useful code being buried underneath `internal` packages.

Learning about some of these other points lead me to find out whether the language supports inline assembly, something very annoyingly lacking in x64 MSVC. And apparently yes, that is supported as well. There are even examples

So definitely not just hype. The language and its ecosystem have features to improve any system programmer's life drastically beyond C, with the benefits of a more contemporary feeling language and better safety.

At this point, I felt it a fun exercise to look and explore all the features of the language that seem exciting, and assembled this list:

- linker flexibility
- C runtimes for targets supported
- inline assembly
- awesome attribute capabilities (conditional compilation and more)
- amazing metaprogramming/macro system that is much less of a pain in the ass to write than C preprocessor macros
- a more comfortable interface system (`traits`) 
- a less anoying module system than Go 
- built in support for doc comments with `cargo doc`
- and (of course) better safety).

Despite being hestitant to take on another language which may not add much to my usual repertoire of Go, C, and assembly, it seems like learning Rust would be worth the tedium of learning the syntax and features of a new language.

## Other Cool Features and Uses

#### Incredible Effort in Documenting Language and Style

- [Style Book](https://doc.rust-lang.org/1.0.0/style/README.html)
- [Embedded](https://docs.rust-embedded.org/book/static-guarantees/typestate-programming.html)
- [Main](https://doc.rust-lang.org/rust-by-example/index.html)
- [Cargo](https://doc.rust-lang.org/cargo/reference/features.html)

#### Fixed length collections (vector, String, HashMap, etc)

Almost built-in support for avoiding heap allocations with regular collections

- https://docs.rust-embedded.org/book/collections/index.html
- https://crates.io/crates/heapless 

#### Fun Function Pointer Types

From: https://kerkour.com/rust-execute-from-memory

#### Self Modifying Code

https://blog.dend.ro/self-modifying-rust/

```
use std::mem;

// we do this trick because otherwise only the reference of the buffer is in the .text section
// and not the buffer itself
const SHELLCODE_BYTES: &[u8] = include_bytes!("../shellcode.bin");
const SHELLCODE_LENGTH: usize = SHELLCODE_BYTES.len();

#[no_mangle]
#[link_section = ".text"]
static SHELLCODE: [u8; SHELLCODE_LENGTH] = *include_bytes!("../shellcode.bin");

fn main() {
    let exec_shellcode: extern "C" fn() -> ! =
        unsafe { mem::transmute(&SHELLCODE as *const _ as *const ()) };
    exec_shellcode();
}
```

## References

- [Migueal Ojeda's Work](https://ojeda.dev/?utm_source=thenewstack&utm_medium=website&utm_campaign=platform)
- [Writing a Kernel Driver with Rust](https://not-matthias.github.io/posts/kernel-driver-with-rust/)
- [Rust Embedded - Book](https://docs.rust-embedded.org/book/collections/index.html)