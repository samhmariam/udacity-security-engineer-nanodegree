# Responding to a Nation-State Cyber Attack

**Prepared by:** Samuel Hailemariam  
**Report date:** 23 June 2026  
**Environment:** South Udan Tridanium processing plant jump host

## Executive Summary

The South Udan Tridanium processing plant's Linux jump host was compromised
after a password-based SSH attack. The investigation identified three files
detected by ClamAV, an additional downloader script that evaded the antivirus
scan, command-and-control infrastructure at `darkl0rd.com:7758`, the source IP
`192.168.56.1`, a persistence account named `darklord`, and a root-owned
backdoor process named `remotesec` listening on TCP port `56565`.

Containment actions included defining a YARA signature for the malicious
domain, confirming that OSSEC recorded SSH authentication activity, blocking
SSH traffic from the attacking IP with iptables, and setting
`PermitRootLogin no` in `/etc/ssh/sshd_config`. Hardening work included an
OpenVAS vulnerability scan, removal of detailed Apache version disclosure, and
definition of a dedicated non-login Apache account and group.

The host should remain isolated until the malicious files, backdoor account,
backdoor process, persistence mechanisms, and unauthorized SSH keys have been
removed and the system has been rescanned. Because a privileged backdoor ran on
the host, rebuilding from a known-good image is safer than assuming that
file-by-file cleanup restored trust. All credentials and keys that were present
on or used through the jump host should be rotated.

## 1. Threat Detection

### 1.1 ClamAV malware scan

Command executed:

```text
clamscan -r /home/ubuntu/Downloads/
```

The submitted scan output identified:

```text
/home/ubuntu/Downloads/moni.lod: OK
/home/ubuntu/Downloads/notes.txt: OK
/home/ubuntu/Downloads/SSH-One: OK
/home/ubuntu/Downloads/gates.lod: OK
/home/ubuntu/Downloads/ft32: Unix.Malware.Agent-6774375-0 FOUND
/home/ubuntu/Downloads/ft64: Unix.Malware.Agent-6774336-0 FOUND
/home/ubuntu/Downloads/wipefs: Unix.Tool.Miner-6443173-0 FOUND
/home/ubuntu/Downloads/tmplog: OK
```

The supplied PDF only preserved the first two lines of the scan summary:

```text
Known viruses: 8874078
Engine version: 0.100.3
```

The original capture did not contain the remaining ClamAV summary fields.
A replacement terminal capture should include the entire output through the
start/end timestamps. The report does not invent those missing values.

### 1.2 Suspicious file and malware behavior

**Suspicious file:** `/home/ubuntu/Downloads/SSH-One`

**Embedded callout URLs:**

```text
http://darkl0rd.com:7758/SSH-T
http://darkl0rd.com:7758/SSH-One
```

The file is a Bash downloader. Its embedded URLs show that it contacts the
`darkl0rd.com` command-and-control host on TCP port `7758` and retrieves
payloads named `SSH-T` and `SSH-One`. This behavior supports classifying the
file as a delivery or persistence component even though the original ClamAV
scan marked it `OK`.

### 1.3 Complete YARA rule

Save as `npa_darkl0rd_domain.yar`:

```yara
rule NPA_Darkl0rd_Domain
{
    meta:
        description = "Detects the darkl0rd.com NPA command-and-control domain"
        author = "Samuel Hailemariam"
        date = "2026-06-23"
        severity = "high"

    strings:
        $domain = "darkl0rd.com" ascii wide nocase
        $url_ssh_t = "http://darkl0rd.com:7758/SSH-T" ascii nocase
        $url_ssh_one = "http://darkl0rd.com:7758/SSH-One" ascii nocase

    condition:
        $domain or any of ($url_*)
}
```

Example validation:

```text
yara npa_darkl0rd_domain.yar /home/ubuntu/Downloads/
```

## 2. Threat Mitigation

### 2.1 Host-based intrusion detection

OSSEC was active while an SSH login was performed. The supplied OSSEC WebUI
capture records:

- `SSH Authentication success`
- `sshd: password accepted for ubuntu`
- `Session opened for user ubuntu`

This proves that the HIDS monitored the SSH login and generated authentication
events.

### 2.2 Attacker IP and firewall control

**Attacker IP:** `192.168.56.1`

Rule that blocks new and existing inbound SSH attempts from that address:

```text
sudo iptables -I INPUT 1 -p tcp -s 192.168.56.1 --dport 22 -j DROP
```

Verification and persistence:

```text
sudo iptables -L INPUT -n --line-numbers
sudo netfilter-persistent save
```

The source address is an indicator of compromise, not a permanent attribution
mechanism. In production, the block should also be applied at upstream
firewalls and monitored for related infrastructure.

### 2.3 Backdoor indicators and remediation

- **Backdoor user:** `darklord`
- **Backdoor process:** `remotesec`
- **Listening endpoint:** `0.0.0.0:56565/tcp`

Containment and eradication actions:

```text
sudo ss -lntp | grep ':56565'
sudo pkill -f remotesec
sudo usermod --lock --expiredate 1 darklord
sudo userdel -r darklord
sudo find /etc/systemd /etc/cron* /var/spool/cron -type f -exec grep -H 'remotesec\|56565\|darklord' {} \;
sudo find /root /home -name authorized_keys -type f -print
```

Preserve volatile and disk evidence before destructive cleanup when incident
response procedures require forensic acquisition.

### 2.4 Disable SSH root access

Configuration file:

```text
/etc/ssh/sshd_config
```

Required setting:

```text
PermitRootLogin no
```

Validate and reload safely:

```text
sudo sshd -t
sudo systemctl reload ssh
sudo sshd -T | grep permitrootlogin
```

Keep the current administrative session open until a second non-root session
has successfully connected.

### 2.5 Remote-access and password-management standard

1. Route administrative access through an approved VPN or hardened bastion
   host. Restrict SSH at the network layer to administrative subnets.
2. Require MFA for VPN, bastion, privileged, and break-glass access. Prefer
   phishing-resistant authenticators.
3. Disable SSH password authentication after managed public-key or
   certificate-based access has been tested. Disable empty passwords and
   direct root login.
4. Use individual accounts, least privilege, `sudo`, session logging, and
   time-bound privileged access. Do not share administrator accounts.
5. Rate-limit and alert on failed authentication. Use controls such as
   Fail2ban, HIDS correlation, and centralized authentication logs.
6. Require long, unique passwords or passphrases and screen new passwords
   against common and compromised values. Do not rely on composition rules
   that produce predictable substitutions.
7. Change passwords and revoke keys immediately after suspected compromise,
   personnel changes, or privilege changes. Rotate managed service and
   emergency credentials on a controlled schedule; avoid arbitrary frequent
   end-user rotation when there is no evidence of compromise.
8. Store human credentials in an approved password manager and service
   credentials in a secrets manager. Never store passwords, private keys, or
   recovery codes in source code, scripts, tickets, or unencrypted files.
9. Protect private keys with passphrases and hardware-backed storage where
   possible. Maintain an inventory, owner, expiry date, and revocation process.
10. Patch SSH, VPN, PAM, and identity components promptly; review access
    quarterly and remove dormant accounts and stale keys.

## 3. System Hardening

### 3.1 OpenVAS vulnerability scan

An OpenVAS report titled **Coordinated Universal Time** was generated on
**Tuesday, 23 June 2026 at 7:55 PM**. The supplied capture shows 89 results
against host `192.168.56.101`, including findings related to supported SSH
protocol versions, exposed services, operating-system detection, and OpenSSH
detection. The scan date is visible in the evidence.

Recommended handling:

1. Export and retain the full report.
2. Validate high and medium findings before remediation.
3. Patch supported packages and remove unnecessary services.
4. Rescan after changes and document accepted residual risk.

### 3.2 Apache version disclosure

The requested evidence is also recorded in `apache_version_patching.txt`.

**Current version:** Apache HTTP Server 2.4.7

**Configuration file:** `/etc/apache2/conf-available/security.conf`

```apache
ServerTokens Prod
ServerSignature Off
```

Apply and test:

```text
sudo apache2ctl configtest
sudo systemctl reload apache2
curl -I http://127.0.0.1/
```

This reduces banner detail but does not replace patching. Apache 2.4.7 should
be upgraded through the operating system's supported package channel.

### 3.3 De-privilege the Apache account

Create the required non-privileged group and account:

```text
sudo groupadd --system apache-group
sudo useradd --system --gid apache-group --no-create-home --shell /usr/sbin/nologin apache-user
```

For the lab requirement, change the Apache installation directory ownership:

```text
sudo chown -R apache-user:apache-group /etc/apache2
```

Production note: security-sensitive configuration under `/etc/apache2` is
normally kept root-owned and non-writable by the web-service account. Only
runtime directories that Apache must write should be delegated. Follow the
course lab instruction in the lab, but preserve root ownership in a real
deployment unless the platform design explicitly requires otherwise.

**Configuration file:** `/etc/apache2/envvars`

Replace:

```text
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
```

With:

```text
export APACHE_RUN_USER=apache-user
export APACHE_RUN_GROUP=apache-group
```

Then validate:

```text
sudo apache2ctl configtest
sudo systemctl restart apache2
ps -eo user,group,pid,cmd | grep '[a]pache2'
```

The root-owned Apache parent process may remain for privileged port binding;
worker processes must run as `apache-user:apache-group`.

## 4. Incident Closure Priorities

1. Isolate and forensically preserve the compromised jump host.
2. Block the identified source and command-and-control infrastructure.
3. Remove or quarantine malicious files and terminate persistence.
4. Disable the `darklord` account and revoke all unauthorized keys.
5. Rotate credentials and keys exposed to the jump host.
6. Rebuild the host from a trusted image, patch it, and restore only verified
   configuration and data.
7. Rescan with current antivirus signatures and OpenVAS.
8. Monitor for the domain, URLs, process, user, port, and related
   authentication behavior across the environment.

## Appendix A. Evidence Integrity Note

The screenshots in the finalized PDF are reproduced from the supplied
submission. Their contents were not altered. The source submission did not
contain a complete ClamAV scan summary, so that single rubric item still
requires a new full terminal capture from the lab environment.
