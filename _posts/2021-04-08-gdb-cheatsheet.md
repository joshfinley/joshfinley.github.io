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

## Reading Output
### Threads

| Output Item            | Meaning                                               |
| ---------------------- | ----------------------------------------------------- |
| `.` before thread data | Current thread                                        |
| `#` before thread data | Indicates that this thread caused the last breakpoing |
| `_structurename`       | Structures are prefixed with `_`                      |






