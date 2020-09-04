---
layout: post
title: "Fixing InfinityHook with ByePg"
description: Common techniques
series: windows_internals
titleImage:
    file: 'title.png'
---

```
git clone https://github.com/everdox/infinityhook
git clone https://github.com/can1357/ByePg.git
```

- Open both in Visual Studio, build ByePg and the InfinityHookFix projects, and add the output and source directories from ByePg and the InfinityHook fix respectively to  `Additional Include Directories` under `libinfityhook->properies->C/C++->General` and add the `Output\InfinityHookFix.lib` and `Output\ByePgLib.lib` to the linker dependencies for `kinfinityhook`. 

- Add `#include "IhFix.h"` to `libinfinityhook\infinityhook.cpp`: ![]({{https://joshfinley.github.io/}}/assets/IhFix-include.png)

- Call the `FixInfinityHook` function: 

![]({{https://joshfinley.github.io/}}/assets/IhFix-IfhInitialize.png)

- Build the solution and copy it to the target. Register and start the service: ![]({{https://joshfinley.github.io/}}/assets/osr-loader.png)

![]({{https://joshfinley.github.io/}}/assets/infinityhook-loaded.png)