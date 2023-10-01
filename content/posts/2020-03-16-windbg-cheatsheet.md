+++
layout = post
title = "WinDbg Cheatsheet"
date = 2020-03-16 00:05:28 -0500
description = So I don't have to google the same things again and again
series = windows_internals
titleImage =     file = 'title.png'
+++
## References

- https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/d--da--db--dc--dd--dd--df--dp--dq--du--dw--dw--dyb--dyd--display-memor
- https://leanpub.com/windowskernelprogramming


## Commands

| Command                | Action                                                     |
| ---------------------- | ---------------------------------------------------------- |
| `~`                    | Show threads for process                                   |
| `k`                    | Show stack trace of current thread                         |
| `~ns`                  | Switch thread, eg. `~0s`                                   |
| `~nk`                  | Get call stack of thread without switching, e.g. `~1k`     |
| `? <Hex>`              | Convert hex number to decimal                              |
| `? <0nDec>`            | Covnert dec number to hex                                  |
| `!teb <addr>`          | Examine TEB of a thread. Addr gets current thread          |
| `!peb`                 | View the PEB                                               |
| `dt <structure>`       | Dump the structure info, e.g. `dt ntdll!_teb`              |
| `bp <function/loc>`    | Set breakpoint at location                                 |
| `bl`                   | List breakpoints                                           |
| `r <register>`         | Display register contents, e.g. `r` displays all registers |
| `db <addr`             | display bytes of memory                                    |
| `u`                    | List the next 8 instructions to be executed                |
| `p`                    | Step over                                                  |
| `t`                    | Step into                                                  |
| `!Process 0 0`         | Display basic information for all processes on system      |
| `!Process 0 0 <exe>`   | List all process running an executable                     |
| `!process <address> !` | Get detailed info about a process                          |
| `ctrl+break`           | Stop long running WinDbg command                           |
| `sxe ld somethin.dll`  | Break on module load                                       |


## Reading Output
### Threads

| Output Item            | Meaning                                               |
| ---------------------- | ----------------------------------------------------- |
| `.` before thread data | Current thread                                        |
| `#` before thread data | Indicates that this thread caused the last breakpoing |
| `_structurename`       | Structures are prefixed with `_`                      |






