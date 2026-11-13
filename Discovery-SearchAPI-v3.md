

## Overview

                   │                   Analyzed Image                   
───────────────────┼────────────────────────────────────────────────────
 Target            │                                                    
   digest          │  86ac9cebde77                                      
   platform        │ linux/amd64                                        
   provenance      │ git@github.com:asfadmin/Discovery-SearchAPI-v3.git 
                   │  https://github.com/asfadmin/Discovery-SearchAPI-v3/blob/389bc5d9a20d907f8200a9e2ba0933637e672a5c          
   vulnerabilities │    5C     0H     0M     0L                         
   size            │ 540 MB                                             
   packages        │ 1176                                               


## Packages and Vulnerabilities

   2C     0H     0M     0L  h11 0.14.0
pkg:pypi/h11@0.14.0

    ✗ CRITICAL GHSA-vqfr-h8mv-ghfj [OWASP Top Ten 2017 Category A9 - Using Components with Known Vulnerabilities]
      https://scout.docker.com/v/GHSA-vqfr-h8mv-ghfj?s=gitlab&n=h11&t=pypi&vr=%3C0.16.0
      Affected range : <0.16.0                                      
      Fixed version  : 0.16.0                                       
      CVSS Score     : 9.1                                          
      CVSS Vector    : CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N 
    
    ✗ CRITICAL CVE-2025-43859 [Inconsistent Interpretation of HTTP Requests ('HTTP Request/Response Smuggling')]
      https://scout.docker.com/v/CVE-2025-43859?s=github&n=h11&t=pypi&vr=%3C0.16.0
      Affected range : <0.16.0                                      
      Fixed version  : 0.16.0                                       
      CVSS Score     : 9.1                                          
      CVSS Vector    : CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N 
    

   2C     0H     0M     0L  mariadb 1:11.8.6-0+deb13u1
pkg:deb/debian/mariadb@1%3A11.8.6-0%2Bdeb13u1?os_distro=trixie&os_name=debian&os_version=13

    ✗ CRITICAL CVE-2026-92262
      https://scout.docker.com/v/CVE-2026-92262?s=debian&n=mariadb&ns=debian&t=deb&osn=debian&osv=13&vr=%3E0
      Affected range : >0        
      Fixed version  : not fixed 
    
    ✗ CRITICAL CVE-2026-85746
      https://scout.docker.com/v/CVE-2026-85746?s=debian&n=mariadb&ns=debian&t=deb&osn=debian&osv=13&vr=%3E0
      Affected range : >0        
      Fixed version  : not fixed 
    

   1C     0H     0M     0L  anyio 3.6.2
pkg:pypi/anyio@3.6.2

    ✗ CRITICAL CVE-2026-63374 [Improper Certificate Validation]
      https://scout.docker.com/v/CVE-2026-63374?s=github&n=anyio&t=pypi&vr=%3C4.14.2
      Affected range : <4.14.2                                                         
      Fixed version  : 4.14.2                                                          
      CVSS Score     : 9.3                                                             
      CVSS Vector    : CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:N/SC:N/SI:N/SA:N 
    


5 vulnerabilities found in 3 packages
  CRITICAL  5 
  HIGH      0 
  MEDIUM    0 
  LOW       0 

