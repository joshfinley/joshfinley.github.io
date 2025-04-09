+++
title = "Brief Post: Ghidra Workaround for Program Diffing on Unaligned Address Ranges"
date = 2025-04-09 00:05:28
draft = false
+++

Brief post.

While working in Ghidra recently, I noticed that there is a good amount of shared code between the AMD and Intel provider executables for the Windows Hypervisor (`hvax64.exe`, `hvix64.exe`). Accordingly, I wanted to compare disassembly on certain functions, but noticed that the built-in Program Differences tool in Ghidra does not support custom address mappings (or if it exists, its buried in menus). This means that if two programs expect different memory locations in memory, the Program Differences tool will not produce immediately useful results. Additionally, I did not see an obvious way to do highly specific function or block level diffing.

A quick google search didn't reveal any cheat-sheet-like guides on how to resolve this without going to an external tool, so I'm writing here to discuss a hack-ish approach to selectively diff when addresses don't line up. The approach is a bit sketchy but can be done natively in Ghidra with no special tooling:

- Identify the function offset and section base address for the targets in both programs.
- Open the Memory Map (`View -> Memory Map`) and re-base the block/section of the comparison target to match the target function based on the offset.

A simplistic example is to just re-base the section whose function is at a higher offset to `0x0` and re-base the target at the difference in the offsets. Then the Program Differences tool can be used like normal.

{{< figure src="/ghidra-program-differences-rebase.png" alt="Example Rebase for Program Differences" >}}

This approach isn't ideal as it will have effects on the Code Browser overall (as whole sections have just been moved) but might be useful as a quick hack to get the built-in Program Differences tool to work when image bases, sections, and functions don't align nicely.

In my use-case of `hvax64.exe`, and `hvix64.exe`, this approach allowed me to quickly see a large amount of the shared code between the binaries. This is of course expected, but allows one to key in on the model-specific differences in the implementations, which is pretty neat!

{{< figure src="/ghidra-program-diff-window.png" alt="Diff View for Intel/AMD Hypervisor Binaries" >}}


If there's an obviously better way to do this natively in Ghidra that I'm not aware of, please let me know!
