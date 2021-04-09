---
layout: post
title:  "GDB Cheatsheet"
date:   2021-04-08 00:05:28 -0500
description: So I don't have to google the same things again and again
titleImage:
    file: 'title.png'
---
## References

- https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/d--da--db--dc--dd--dd--df--dp--dq--du--dw--dw--dyb--dyd--display-memor
- https://leanpub.com/windowskernelprogramming


## Commands

| Command                | Action                                                     |
| ---------------------- | ---------------------------------------------------------- |
| `layout asm`           | Show disassembly                                           |
| `start`                | Break on main and run                                      |
| `tui reg general`      | Display general purpose regs                               |
| `ctrl+p`               | Previous command in tui mode                               |
| `ctrl+n`               | Next command in tui mode                                   |
| `set disassembly-flavor intel` | Dodge the awfulness that is ATT syntax             |

## Peda Commands
  * `aslr` -- Show/set ASLR setting of GDB
  * `checksec` -- Check for various security options of binary
  * `dumpargs` -- Display arguments passed to a function when stopped at a call instruction
  * `dumprop` -- Dump all ROP gadgets in specific memory range
  * `elfheader` -- Get headers information from debugged ELF file
  * `elfsymbol` -- Get non-debugging symbol information from an ELF file
  * `lookup` -- Search for all addresses/references to addresses which belong to a memory range
  * `patch` -- Patch memory start at an address with string/hexstring/int
  * `pattern` -- Generate, search, or write a cyclic pattern to memory
  * `procinfo` -- Display various info from /proc/pid/
  * `pshow` -- Show various PEDA options and other settings
  * `pset` -- Set various PEDA options and other settings
  * `readelf` -- Get headers information from an ELF file
  * `ropgadget` -- Get common ROP gadgets of binary or library
  * `ropsearch` -- Search for ROP gadgets in memory
  * `searchmem|find` -- Search for a pattern in memory; support regex search
  * `shellcode` -- Generate or download common shellcodes.
  * `skeleton` -- Generate python exploit code template
  * `vmmap` -- Get virtual mapping address ranges of section(s) in debugged process
  * `xormem` -- XOR a memory region with a key
