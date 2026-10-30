# Credential Hardening

> **MITRE D3FEND:** `Harden` | [D3-SPP - Strong Password Policy](https://d3fend.mitre.org/technique/d3f:StrongPasswordPolicy/)

## Overview
Default credentials are one of the most common vulnerabilities in Industrial Control Systems. Many ICS devices ship with well-known default usernames and passwords that are documented in manuals and online databases. Attackers routinely scan for and exploit default credentials to gain unauthorized access to PLCs, HMIs, and engineering workstations.

This challenge requires you to change the default passwords on two critical systems in the CybICS testbed: the **OpenPLC runtime** and the **FUXA HMI**.

The flag has the format `CybICS(flag)`.

## Task 1: Harden OpenPLC Credentials

The OpenPLC web interface runs on port **8080** and uses the default credentials:
- **Username:** `openplc`
- **Password:** `openplc`

### Steps
1. Open a web browser and navigate to `http://<DEVICE_IP>:8080`
2. Log in with the default credentials
3. Click **Users** in the left-hand menu (it is a menu entry of its own, not
   part of **Settings**)
4. Click the `openplc` row, type a new password into **Password** and click
   **Save changes**
5. Click **Verify Defense** on this challenge page to confirm

## Task 2: Harden FUXA Credentials

The FUXA HMI runs on port **1881** and uses the default admin credentials:
- **Username:** `admin`
- **Password:** `123456`

### Steps
1. Open a web browser and navigate to `http://<DEVICE_IP>:1881`
2. Log in with the default admin credentials
3. Open the user management. FUXA has no account menu at the top right (the
   `admin` name there only shows who is logged in); users are managed in the
   editor:
   - click the round blue menu button at the **bottom left** and choose
     **Editor**,
   - in the editor, click the **gear icon** at the top left; the **Setup**
     dialog opens,
   - under **Misc**, click **Users**. This opens the **Users settings** page,
     which you can also reach directly at `http://<DEVICE_IP>:1881/users`.
4. Click the pencil next to `admin`, type a new password into **Password** and
   confirm with **OK**. The new password is active at once; the editor's save
   icon is not needed for it
5. Click **Verify Defense** on this challenge page to confirm

## Important Notes
- Remember your new passwords! If you forget them, you may need to restart the containers.
- Choose passwords that are strong enough to resist dictionary attacks (the same attack you performed in the Password Attack challenge).
- Do not change the usernames — only the passwords need to be changed.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques Defended Against

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Persistence, Lateral Movement | Insecure Credentials: Default Credentials | [T1694.001](https://attack.mitre.org/techniques/T1694/001/) | Adversaries use default credentials to gain initial access |
| Persistence, Lateral Movement | Valid Accounts | [T0859](https://attack.mitre.org/techniques/T0859/) | Compromised credentials enable persistent access |

### MITRE D3FEND - Defensive Techniques Applied

| Technique | ID | Description |
|-----------|-----|-------------|
| Strong Password Policy | [D3-SPP](https://d3fend.mitre.org/technique/d3f:StrongPasswordPolicy/) | Enforcing strong, non-default passwords |
| Credential Rotation | [D3-CRO](https://d3fend.mitre.org/technique/d3f:CredentialRotation/) | Changing default credentials to prevent unauthorized access |
| Authentication Event Monitoring | [D3-AEM](https://d3fend.mitre.org/technique/d3f:AuthenticationEventMonitoring/) | Monitoring for brute force and unauthorized login attempts |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Identification and Authentication (IA)** | IA-5 | Authenticator management — changing default passwords |
| **Access Control (AC)** | AC-2 | Account management — proper credential configuration |
| **Configuration Management (CM)** | CM-6 | Configuration settings — removing default configurations |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.3 specifically addresses the challenge of default credentials in OT environments. IA-5 (Authenticator Management) requires organizations to change default authenticators upon installation. CM-6 (Configuration Settings) recommends establishing secure baseline configurations that do not include factory-default credentials. Many ICS security incidents begin with exploitation of default credentials — this is one of the simplest yet most impactful hardening steps.

</details>

## Defensive Thinking

After completing this challenge, consider:
- How would you enforce a password policy on ICS devices that don't support it natively?
- What are the risks of account lockout mechanisms in OT environments?
- How would you manage credentials across dozens or hundreds of ICS devices?
- What role does multi-factor authentication play in ICS environments?


## Hints

For OpenPLC, navigate to the web UI at port 8080, log in with `openplc`/`openplc`, then go to **Users** in the sidebar to find the password change option. For FUXA, log in at port 1881 and look in the editor, not at the top right: the round button at the bottom left leads to **Editor**, its gear icon opens **Setup**, and **Users** there is the **Users settings** page (`/users`). Edit the `admin` user.

## Solution

1. **OpenPLC** — Navigate to `http://<DEVICE_IP>:8080`, log in with the default credentials (`openplc`/`openplc`), click **Users** in the left-hand menu, open the `openplc` user and change its password to something non-default (**Save changes**).
2. **FUXA** — Navigate to `http://<DEVICE_IP>:1881`, log in with the default credentials (`admin`/`123456`), open **Editor** from the round button at the bottom left, then the gear icon at the top left (**Setup**) and **Users** (or go straight to `http://<DEVICE_IP>:1881/users`), click the pencil next to `admin`, set a new password and confirm with **OK**.
3. Click **Verify Defense** in the CTF interface for each task to receive the flag.

**Flag (OpenPLC):** `CybICS(0penPLC_h4rd3n3d)`

**Flag (FUXA):** `CybICS(FUXA_s3cur3d)`
