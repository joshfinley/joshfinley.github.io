+++
title = "Covert IPC With the Windows Kernel Transaction Manager"
date = 2025-03-31 00:05:28
draft = false
+++

> This post documents a potential technique for stealthy inter-process communication on Windows. The idea is based on the apparent absence of `Etw` (and `EtwTi`) instrumentation of system calls involving the *Windows Kernel Transaction Manager*, and the ability for processes to receive handles to transaction objects without accessing instrumented system calls.

## Overview

While re-reading Matt Hand's [*"Evading EDR"*](https://nostarch.com/evading-edr), I was following along with the methodology he described involving graph analysis of function call trees. The premise is to [convert](https://gist.githubusercontent.com/matterpreter/3d9239179372dd179801e996288c983e/raw/5dfcdaaf924e4cb3cd822fa5d00fc306004e3b71/CallTreeToJSON.py) a Ghidra analysis of call graphs in a binary to a JSON format suitable for use in [Neo4j](https://neo4j.com/), allowing for robust querying.

The example provided in Chapter 12 demonstrates identifying `Nt` family functions with edges to known `EtwTi` functions. Reading this gave me the idea to write a query that does something slightly different: Identify system call functions *without* known calls to `Etw` functions.

The query for this is relatively simple:

```
MATCH (f:Function)
WHERE f.name STARTS WITH 'Nt'
  AND NOT f.name CONTAINS '$'
  AND NOT EXISTS {
    CALL {
      WITH f
      MATCH (f)-[:CALLS*1..25]->(t:Function)
      WHERE t.name STARTS WITH 'Etw'
      RETURN t
    }
  }
RETURN f;
```

This will simply traverse the call graph from `Nt`-family functions and report on those which do not have an outgoing ETW call somewhere inside.

On my Windows 11 26100 reversing machine, this query identified 47 records. Nearly all are related to the [Windows Kernel Transaction Manager (KTM)](https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/introduction-to-ktm). After briefly reviewing the Microsoft documentation, I started to wonder if kernel service was suitable for anything useful for offensive purposes, as it *appears* to be ignored by `Etw`. 

While I haven't gone into depth to verify that no form of security instrumentation exists for these system calls in the kernel, the graph analysis results are promising. With this in mind, I set out with the purpose of at least determining if some sort of inter-process communication could be implemented using KTM. If true, it may merit a closer look and potentially some utility in same-host offensive scenarios. As a side note, I haven't extensively surveyed the previous work in the area of KTM, so it's possible that someone has stumbled upon this before, but it still seems quite niche and potentially under-explored.

While reviewing the documentation, my first aim was to determine how one would work with the transaction manager in the first place. Fortunately, it is relatively straightforward and decently documented.

The first step is to simply create a transaction object with `NtCreateTransaction`. This can be done from unprivileged user-mode contexts. While reading the [function documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-ntcreatetransaction), I noticed that it takes a parameter of type `PUNICODE_STRING`, potentially allowing for the storage of a decently large amount of information inside the kernel. If there is a way to recover this, it could be used as an odd form of generic inter-process communication.

At this point I set some criteria for the technology for further investigation:

1. The technique must allow for some sort of data to be sent to the kernel and recovered by another process.
2. There must be a way to use _only_ the uninstrumented system calls.
3. All system calls must be shown as uninstrumented by the graph query.
4. All operations must be from an unprivileged context.

Fortunately, all of these things are true!

## Proof-of-Concept

The `NtCreateTransaction` system call has the following type signature, according to Microsoft:

```C
__kernel_entry NTSYSCALLAPI NTSTATUS NtCreateTransaction(
  [out]          PHANDLE            TransactionHandle,
  [in]           ACCESS_MASK        DesiredAccess,
  [in, optional] POBJECT_ATTRIBUTES ObjectAttributes,
  [in, optional] LPGUID             Uow,
  [in, optional] HANDLE             TmHandle,
  [in, optional] ULONG              CreateOptions,
  [in, optional] ULONG              IsolationLevel,
  [in, optional] ULONG              IsolationFlags,
  [in, optional] PLARGE_INTEGER     Timeout,
  [in, optional] PUNICODE_STRING    Description
);
```

Narrowing in on the IPC use-case, we can see the last argument is an optional `PUNICODE_STRING` type. Being able to set this in one process and retrieve it in another would represent an opportunity for a form of side-channel IPC.

The corresponding API to open a transaction is `NtOpenTransaction`, which has the following signature:

```C
__kernel_entry NTSYSCALLAPI NTSTATUS NtOpenTransaction(
  [out]          PHANDLE            TransactionHandle,
  [in]           ACCESS_MASK        DesiredAccess,
  [in, optional] POBJECT_ATTRIBUTES ObjectAttributes,
  [in]           LPGUID             Uow,
  [in, optional] HANDLE             TmHandle
);
```

What is most interesting here is that the `TmHandle` parameter is *optional*. The [documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-ntopentransaction) notes that if this parameter is `NULL`, KTM will actually search for a matching object based on the object attributes.

Conventiently, the `ObjectName` field of `OBJECT_ATTRIBUTES` allows us to define a name for the transaction object, which will be registered in the NT Object Manager namespace. Using this name, we can easily get a handle to a targeted transaction object, without any other system calls.

The next question I had was wheter the `Description` field could actually be recovered. The most likely [candidate](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-ntqueryinformationtransactionmanager) in my search was `NtQueryInformationTransactionManager`:

```C
__kernel_entry NTSYSCALLAPI NTSTATUS NtQueryInformationTransactionManager(
  [in]            HANDLE                               TransactionManagerHandle,
  [in]            TRANSACTIONMANAGER_INFORMATION_CLASS TransactionManagerInformationClass,
  [out]           PVOID                                TransactionManagerInformation,
  [in]            ULONG                                TransactionManagerInformationLength,
  [out, optional] PULONG                               ReturnLength
);
```

Although not expressly [documented by Microsoft](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-ntqueryinformationtransactionmanager), it is in fact possible to recover the `Description` field from a transaction object using this function.

To do so, we pass a reference to a `TRANSACTION_PROPERTIES_INFORMATION` structure and the `TransactionPropertiesInformation` class to `NtQueryInformationTransactionManager`. Fortunately, these are available in the `winnt.h` header, so I did not have to reverse them manually.

Like many `Nt` APIs, if the size of the returned information isn't known ahead of time, an initial call to the function must be used to discover the size locally, and then a second call can be used to obtain the full structure.

Finally, a second call can be made to `NtQueryInformationTransactionManager`, and assuming no mistakes were made, the description can be recovered!

{{< figure src="/ipc-ktm.png" alt="Inter-Process Communication via KTM" >}}

Going back to the criteria from before, this proof-of-concept was performed from a regular user's execution context on an up-to-date Windows 11 instance, none of the used system calls were shown as instrumented by the graph query, and basic IPC has been demonstrated to be possible.

## Conclusion

While far from an operational example, this evening endeavor into KTM highlights a potentially useful and under-explored IPC mechanism invisible from ETW. Monitoring operations on the NT Object Manager namespace in general would provide poor fidelity into IPC over this mechanism thanks to the distance between any such monitoring and system calls that are used to create the transaction object.

Further research might include the following:

- Validate the presumed lack of observability of KTM operations.
- Operationalize the mechanism, which would require a more thorough understanding of how subsequent operations on the object would be performed.
- Identify other useful attack surface in KTM - there has been at least [one](https://www.exploit-db.com/exploits/42233) interesting example of this.
- Test the concept on a system with robust monitoring.

Any questions, insights, or suggestions can be directed to the [Issues](https://github.com/joshfinley/joshfinley.github.io/issues) section of the repository backing this site.

Special thanks to Matt Hand and *"Evading EDR"* for leading me down this rabbit hole. 