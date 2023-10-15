+++

title = "Driver Hacking Notes"
date = 2020-09-12 00:05:29 

+++

## Bug-Hunting

- [Hacksys. *Extreme Vulnerable Driver*](https://github.com/hacksysteam/HackSysExtremeVulnerableDriver). Driver with most common driver vulnerabilities.
- [Forshaw. *Introduction to Logical Privilege Escalation on Windows*](https://conference.hitb.org/hitbsecconf2017ams/materials/D2T3%20-%20James%20Forshaw%20-%20Introduction%20to%20Logical%20Privilege%20Escalation%20on%20Windows.pdf). Includes brief explanations on kernel-based EOP.

## Known Vulnerable Drivers

### 2a. Publications

- [Eclypsium. *Get Off the Kernel If You Can't Drive](/archives/725b68740124d34b42fc959e9c10bd642cb6a5c41b7550a749f90c05e414176f_EXTERNAL-Get-off-the-kernel-if-you-cant-drive-DEFCON27.pdf.html). Presentation documenting known vulnerable drivers and malware abuse methodologies.
- [ReWolf. *MSI ntiolib.sys/winio.sys local privilege escalation*](http://blog.rewolf.pl/blog/?p=1630). MSI local EOP writeup.
- [Eclypsium. Drivers. *Screwed Drivers*](https://github.com/eclypsium/Screwed-Drivers/blob/master/DRIVERS.md). List of vulnerable drivers (with hashes)
- [ACTIVELabs. *Viper RGB Driver Local Privilege Escalation (CVE-2019-18845)](https://www.activecyber.us/activelabs/viper-rgb-driver-local-privilege-escalation-cve-2019-18845)

### 2b. Binaries

- [Gigabyte](https://gist.github.com/joshfinley/59cc0c8cbc49f94d6c6a6b938fbfebb8)
- [Capcom](https://github.com/FuzzySecurity/Capcom-Rootkit/blob/master/Driver/Capcom.sys)
- [Asus Driver7](https://github.com/joshfinley/AsusDriversPrivEscala/blob/master/driver7-x64.sys)

### 2c. Exploits

- [Hoangprod. *DanSpecial*](https://github.com/hoangprod/DanSpecial). Gigabyte driver exploit.
- [Rewolf. *rewolf-msi-exploit*](https://github.com/rwfpl/rewolf-msi-exploit). MSI epxloit
- [Barakat. *CVE-2019-16098*](https://github.com/Barakat/CVE-2019-16098)
- [Chigusa. *AsusDrivesPrivEscala](https://github.com/Chigusa0w0/AsusDriversPrivEscala)
- [SecureAuth Labs. *[CORE-2018-0007] - GIGABYTE Driver Elevation of Privilege Vulnerabilities*](https://seclists.org/fulldisclosure/2018/Dec/39)

### 2d. Loaders

- [Devcon](/archives/0e9c112d0469f4456f6dd3178c2f4891896c28fcbce8a5bcef53ac6f58118e14_devcon.html)

### 2e. Unsigned Utility Drivers

- [Zerosum0x0. *ShellcodeDriver*](https://github.com/zerosum0x0/ShellcodeDriver). Run usermode shellcode (uses CAPCOM logic).

## In Malware

### 3a. LoJax

### 3b. Slingshot
