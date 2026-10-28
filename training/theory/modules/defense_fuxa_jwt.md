# Rotating a signing key

In this challenge you give the CybICS Human-Machine Interface (HMI) a signing key of its own. Every session token forged with the published default key stops working at once, and so does every token that was ever stolen. It is a small configuration change that has to be made with care, because one misplaced character takes the HMI offline. It also has a clear limit: it fixes the key, not every flaw in the HMI's code.

## The idea

A server that signs session tokens trusts whoever holds its signing key. Replacing the key is called **key rotation**: tokens signed with the old key no longer pass the check, and users simply log in again to get new ones signed with the new key.

<div class="callout analogy" markdown="1">
**Analogy:** a festival changes the stamp for the wristbands. Bands made with the old stamp, real or copied, no longer get anyone in. Guests with a valid ticket queue once more and get a band with the new stamp.
</div>

A good key has two properties. It is **secret**: it lives only in the server's configuration, never in source code, documentation or a shared backup. And it is **long and random**, because an attacker who captures one token can test guesses offline without the server noticing. A word, the name of the plant or the default with one digit changed is found quickly; 32 or more random characters are not.

In MITRE D3FEND the defence is *Credential Rotation* (D3-CRO), and changing a product's shipped setting is *Application Configuration Hardening* (D3-ACH).

## How it looks on CybICS

| Host | Address | What matters here |
|---|---|---|
| FUXA | `172.18.0.4`, port 1881 | the HMI; reads its signing key from `/_appdata/settings.js` |

FUXA's settings file is not a list of options but a small JavaScript program: one object between `module.exports = {` and the closing brace, with entries separated by commas. FUXA reads it once, at start-up, so a change takes effect only after a restart. If the file contains a syntax error, FUXA stops immediately and Docker restarts it again and again: the plant loses its HMI.

<div class="callout warning" markdown="1">
**Watch out:** the file already contains an example key line, commented out, near its end. The active entry right above it has no comma after it, so simply removing the comment marks breaks the file. Add your own line at the top of the object instead.
</div>

<div data-widget="checkpoint" data-id="restart"></div>

## How to approach it

1. **Find the container and the file.** The defense challenges change containers with Docker from the landing page's admin shell.
2. **Back up the file** before you edit it, so you can always go back.
3. **Generate a random key** on the command line rather than inventing one, and add it as the first entry of the settings object.
4. **Check the file loads** with the same JavaScript runtime FUXA uses, before you restart anything.
5. **Restart FUXA**, wait for the HMI and log in again.
6. **Try your old forged token.** It should now be refused.

The check never reads your key. It forges tokens with the default key and a list of guessable ones, makes sure FUXA refuses all of them but still accepts the tokens it signs itself, and asks only how long your key is and how many different characters it uses (a long run of the same letter is not random).

### What a new key does not fix

<div class="callout warning" markdown="1">
**Rotating the key does not end every forged admin session.** FUXA 1.2.6 has a "refresh my token" request that signs a new token for whatever user name and role the client names, as long as the token it sends along is invalid. FUXA signs that token with your new key. Anyone who can reach the HMI's port can still become administrator this way, without a password.
</div>

That is a mistake in FUXA's program, not in its configuration, so no setting fixes it. Two things do: **limit who can reach port 1881** to the operator stations that need the HMI (a firewall or network segmentation), and **upgrade or patch FUXA** once a version checks the token before refreshing it. The key is still worth rotating: it stops tokens forged offline with the published default, and it is the setting a fixed FUXA will rely on.

<details class="deep-dive" markdown="1">
<summary>Deep dive: making the change last</summary>

On a CybICS board FUXA's data folder is a Docker volume, so the key survives updates and reboots. In the virtual lab it lives only in the container: a restart keeps it, but recreating the container from its image (for example during an update) brings back the default. Real plants solve this with configuration management: the hardened setting is part of the deployment, so a rebuild cannot quietly undo it. Rotate the key whenever a token or the settings file may have leaked, and when people with access leave.

</details>

## Detect and defend

Rotation removes the sessions forged with the old key, but the key is only as safe as the file that holds it, and it does nothing against the token-refresh flaw above.

- **Protect the settings file.** Anyone who can read it can forge tokens again. Keep it out of version control and out of backups that leave the plant network.
- **Plan the restart.** Rotating logs every operator out. Choose a quiet moment and tell the people at the HMI first.
- **Keep watching sessions.** Administrator requests from an address that never logged in still deserve a look; a leaked new key looks exactly like the old attack.
- **Limit who can reach the HMI.** Only operator stations need port 1881. In FUXA 1.2.6 this is the only defence against the token-refresh flaw.
- **Combine it with the other hardening steps.** Strong passwords cover the login side of the same HMI.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The step-by-step commands are in training/defense_fuxa_jwt/README.md. The check reads only the key length and its number of distinct characters, through docker exec and node inside the FUXA container, and needs at least 32 characters and 10 distinct ones. It proves FUXA still works with its own key without a password: POST /api/heartbeat without a token returns a guest token signed with the current key, and sending that token back with a mismatching x-auth-user header gets 403 only if FUXA verified it. In the virtual lab the change is lost when the FUXA container is recreated (./cybics.sh update, image change); the admin password from Harden FUXA Credentials is lost the same way. tests/test_training.py restores settings.js from a backup and restarts FUXA after its run. The token-refresh flaw: in jwt-helper.js verifyToken, an invalid x-access-token sets the request to guest and skips the x-auth-user groups comparison, and the heartbeat route with {"params": true} then calls getNewToken, which signs {id, groups} straight from x-auth-user. POST /api/heartbeat with x-access-token: garbage and x-auth-user: {"user":"ghost","groups":-1} returns an administrator token signed with the current key, before and after rotation; tests/test_training.py pins that behaviour so a FUXA upgrade that changes it is noticed. Students should not leave thinking the defence ended forged admin sessions: discuss it, and point to port restriction as the mitigation.

</details>

## Before you start

- [Hardening credentials](/theory/defense_password): the password side of the same HMI
- [Forged session tokens](/theory/fuxa_jwt): the attack this defence stops
