"""
Reference client for CybICS-mgmt, the optional central server for CybICS.

Meant to be vendored into CybICS' landing service as one file
(software/landing/modules/cybics_mgmt.py): standard library only, Python 3.9+.

The installation enrols once as a *device* and gets a token. Over one
heartbeat it then reports its status, takes jobs the server signed, and, while
it is a member of a team in an event, reports the team's solves.

Design rules, all following from "the server is optional":

* Nothing happens until the user enrols from the landing page. A fresh or
  disabled client makes no network calls at all.
* The landing page keeps validating flags locally. The client only *reports*
  local solves; a server that is down, slow or gone never blocks or fails a
  local submission.
* Reports survive outages. Solves sit in a persistent outbox until the server
  answers with a final result, and every heartbeat reconciles the local solve
  list with the server's, so nothing is lost if the outbox file is.
* Solves that existed locally before joining an event (old progress on a
  reused Pi) are not reported: the client snapshots them as a baseline.
* The client runs a job only when it is signed with the key pinned at
  enrolment, carries a higher sequence number than every job before, names
  this device, and asks for an action the user allowed here (none by
  default). It executes nothing itself: landing registers one handler per
  action.

Typical wiring in landing:

    client = MgmtClient(
        state_path="data/cybics_mgmt.json",
        device_info=lambda: {"kind": "physical", "device_uid": uid, "hostname": ..., "cybics_version": ...},
        status=collect_status,
        local_solves=lambda: ctf_manager.load_progress()["solved_challenges"],
        flag_for=lambda cid: (ctf_manager.get_challenge(cid)[0] or {}).get("flag"),
        handlers={"identify": show_banner, "restart": restart_services, ...})
    client.start()                         # background threads, idle until enrolled
    ...
    # after a successful local /ctf/submit or /ctf/verify:
    client.report_solve(challenge_id, flag)
"""
import gzip
import hashlib
import hmac
import http.client
import json
import logging
import os
import ssl
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger("cybics_mgmt")

API_PREFIX = "/api/v1"
CLIENT_VERSION = "1"
DEFAULT_INTERVAL = 30
TIMEOUT = 8
# Enrolling and joining may queue briefly at the proxy when a class starts at once.
ENROLL_TIMEOUT = 30

# Results that mean "counted, or already on record". Every other result is
# final too (the solve leaves the outbox); see _settle() for which ones are
# held and retried later. Unknown future result values are treated like
# invalid_flag, as docs/API.md requires.
DONE_RESULTS = {"accepted", "duplicate"}
KNOWN_RESULTS = DONE_RESULTS | {"invalid_flag", "unknown_challenge", "event_not_running"}

ACTIONS = ("identify", "message", "restart", "reset_progress", "collect_logs")
MIN_KEY_BITS = 3072
LOGS_MAX = 256 * 1024           # compressed, as the server accepts it
LOGS_RAW_MAX = 4 * 1024 * 1024  # what is compressed at most: the newest part of the logs
HISTORY_MAX = 50
# DER prefix of a SHA-256 DigestInfo (RFC 8017, section 9.2, note 1).
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


class MgmtClientError(Exception):
    """
    An error to show the user: `code` is the server's error code or a transport
    code. `from_server` is True only when the answer carried this server's JSON
    error shape; a 4xx page from a reverse proxy in between does not count.
    """

    def __init__(self, code, message, status=None, from_server=False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.from_server = from_server


# ---------- transport and storage ----------

def _http(ssl_context, base, method, path, body=None, token=None, timeout=TIMEOUT, raw=None,
          content_type=None):
    """
    One request to the server: returns (status, JSON object) or raises
    MgmtClientError. `raw` sends bytes as they are, with `content_type`.
    """
    req = urllib.request.Request((base or "").rstrip("/") + API_PREFIX + path, method=method)  # noqa: S310
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "cybics-landing")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    elif raw is not None:
        data = raw
        req.add_header("Content-Type", content_type or "application/octet-stream")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        # The scheme is http(s) only: every server_url passes normalize_url().
        with urllib.request.urlopen(req, data=data, timeout=timeout, context=ssl_context) as resp:  # noqa: S310
            raw_answer = resp.read()
            answer = json.loads(raw_answer) if raw_answer else {}
            if not isinstance(answer, dict):
                raise ValueError("not a JSON object")
            return resp.status, answer
    except urllib.error.HTTPError as exc:
        try:
            err = json.loads(exc.read()).get("error")
        except (ValueError, AttributeError, OSError, http.client.HTTPException):
            err = None
        ours = isinstance(err, dict) and isinstance(err.get("code"), str)
        err = err if ours else {}
        raise MgmtClientError(err.get("code", f"http_{exc.code}"),
                              err.get("message", f"Server answered HTTP {exc.code}."),
                              exc.code, from_server=ours) from None
    except (OSError, http.client.HTTPException) as exc:
        # URLError, timeouts, resets, TLS errors (all OSError) and a body
        # cut off mid-transfer (IncompleteRead) on flaky Wi-Fi.
        reason = getattr(exc, "reason", None) or exc.__class__.__name__
        raise MgmtClientError("unreachable", f"Cannot reach the server: {reason}") from None
    except ValueError:   # includes JSONDecodeError and UnicodeDecodeError
        raise MgmtClientError("bad_response", "The server did not answer with a JSON object.") from None


def _write_state(path, state):
    """Write the state file atomically, fsynced, readable by its owner only (it holds the token)."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".cybics_mgmt.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            f.flush()
            os.fsync(f.fileno())   # a Pi may lose power at any moment
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _interval(value):
    """The server's heartbeat interval, defended: it decides how often a thread wakes up."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        return DEFAULT_INTERVAL
    return int(min(3600, max(5, value)))


def normalize_url(url):
    url = (url or "").strip().rstrip("/")
    if "://" not in url:
        url = "http://" + url
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise MgmtClientError("invalid_url", "Enter a server address like http://10.10.0.1:8000.")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


# ---------- job signatures ----------

def key_fingerprint(n, e):
    """SHA-256 of "<e>:<n in hex>", the value the organiser sees on the device page."""
    return hashlib.sha256(f"{e}:{n:x}".encode()).hexdigest()


def job_message(job):
    """The bytes the server signed for a job (canonical JSON of its fields)."""
    return json.dumps({k: job[k] for k in ("action", "device", "id", "params", "seq")}, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=True).encode()


def verify_signature(n, e, message, signature_hex):
    """
    RSA PKCS#1 v1.5 with SHA-256, in plain Python: the signature is raised to
    the public exponent and compared, in constant time, with the encoding the
    signature must have. Nothing of the decrypted block is parsed, so there is
    no padding parser to fool.
    """
    size = (n.bit_length() + 7) // 8
    if not isinstance(signature_hex, str) or len(signature_hex) != 2 * size:
        return False
    try:
        signature = int(signature_hex, 16)
    except ValueError:
        return False
    if not 0 < signature < n:
        return False
    digest_info = _SHA256_DIGEST_INFO + hashlib.sha256(message).digest()
    expected = b"\x00\x01" + b"\xff" * (size - len(digest_info) - 3) + b"\x00" + digest_info
    return hmac.compare_digest(pow(signature, e, n).to_bytes(size, "big"), expected)


def _pinned_key(value):
    """(n, e) from an enrolment answer's signing_key, or None if it is not a key to trust."""
    if not isinstance(value, dict) or not isinstance(value.get("n"), str) or value.get("e") != 65537:
        return None
    try:
        n = int(value["n"], 16)
    except ValueError:
        return None
    if n.bit_length() < MIN_KEY_BITS:
        return None
    return n, 65537


# ---------- state ----------

def _empty_ctf():
    return {
        "joined": False,
        "removed": False,        # out of the event by the organiser, not by the user: keep queuing
        "instance_id": None,
        "event": None,
        "team": None,
        "baseline": [],          # local solves from before joining, never reported
        "outbox": [],            # [{challenge_id, flag, solved_at, while_running}]
        "rejected": [],          # challenge ids the server refused for good
        "held": {},              # challenge id -> catalog_version it was refused in
        "held_paused": [],       # solved while running, delivered during a pause
        "catalog_version": None,
        "server_solved": [],
        "standing": None,        # {score, rank, teams, banned}
        "announcements": [],
        "last_announcement_id": 0,
        "left_local": None,      # local solves when the user left; see _adopt()
    }


# Carried over when the device joins the same team of the same event again
# (after the organiser removed it, a re-enrolment, or leave + join), so
# nothing that was queued, held or decided is lost.
CARRY_OVER = ("baseline", "outbox", "rejected", "held", "held_paused", "server_solved",
              "announcements", "last_announcement_id", "catalog_version")


def _empty_state():
    return {
        "enabled": False,
        "server_url": None,
        "device_id": None,
        "token": None,
        "device": None,          # {id, label, group} as the server last named them
        "signing_key": None,     # {"n": hex, "e": 65537}, pinned at enrolment
        "allowed": [],           # actions the user allowed on this device; none by default
        "last_seq": 0,           # highest job sequence number accepted
        "queue": [],             # verified jobs waiting to run
        "running": None,         # the job running right now, saved before it starts
        "results": [],           # job results not yet reported
        "history": [],           # the last HISTORY_MAX jobs, for the landing page
        "last_contact": None,
        "last_error": None,
        "heartbeat_interval": DEFAULT_INTERVAL,
        "revoked": False,        # retired by the organiser, not by the user
        "ctf": _empty_ctf(),
    }


class MgmtClient:
    def __init__(self, state_path, device_info=lambda: {}, status=lambda: {}, local_solves=lambda: [],
                 flag_for=lambda _cid: None, handlers=None, ca_file=None):
        """
        state_path   JSON file holding the enrolment and the outbox (put it on a volume)
        device_info  callable returning {kind, device_uid, hostname, cybics_version, mode}
        status       callable returning the status dict sent with each heartbeat
        local_solves callable returning the challenge ids solved locally
        flag_for     callable mapping a challenge id to its flag (from ctf_config.json)
        handlers     {action: callable(params) -> str | bytes | None}; collect_logs
                     returns the log text or bytes, the others a short result
        ca_file      optional CA bundle for a server with a private certificate
        """
        self.state_path = state_path
        self.device_info = device_info
        self.status = status
        self.local_solves = local_solves
        self.flag_for = flag_for
        self.handlers = {k: v for k, v in (handlers or {}).items() if k in ACTIONS and callable(v)}
        self._ssl = ssl.create_default_context(cafile=ca_file) if ca_file else None
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._work = threading.Event()
        self._stop = threading.Event()
        self._threads = []
        self.state = self._load()
        self._finish_interrupted()

    normalize_url = staticmethod(normalize_url)

    # ---------- persistence ----------

    def _load(self):
        state = _empty_state()
        try:
            with open(self.state_path, encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, ValueError):
            return state
        if isinstance(saved, dict):
            state.update({k: v for k, v in saved.items() if k in state and k != "ctf"})
            if isinstance(saved.get("ctf"), dict):
                state["ctf"].update({k: v for k, v in saved["ctf"].items() if k in state["ctf"]})
        return state

    def _save(self):
        _write_state(self.state_path, self.state)

    def _save_or_raise(self):
        """_save() for user actions: a full or read-only disk becomes a MgmtClientError."""
        try:
            self._save()
        except OSError as exc:
            raise MgmtClientError("state_unwritable", f"Cannot save the CybICS-mgmt settings: {exc}") from None

    def _try_save(self):
        try:
            self._save()
        except OSError as exc:   # full SD card, read-only volume: keep going in memory
            log.warning("cybics-mgmt: cannot save the state: %s", exc)
            self.state["last_error"] = {"code": "storage", "time": time.time(),
                                        "message": f"Cannot save the settings: {exc}"}

    def _request(self, method, path, body=None, timeout=TIMEOUT, raw=None, content_type=None, token=None):
        return _http(self._ssl, self.state["server_url"], method, path, body=body,
                     token=token or self.state["token"], timeout=timeout, raw=raw, content_type=content_type)

    def _safe_local_solves(self):
        try:
            return list(self.local_solves() or [])
        except Exception:  # landing's progress file may be mid-write; try again next round
            return []

    def _finish_interrupted(self):
        """A job that was running when landing stopped; a restart takes landing down with it."""
        running = self.state.get("running")
        if not isinstance(running, dict):
            self.state["running"] = None
            return
        if running.get("action") == "restart":
            self._finish(running, "done", "landing restarted")
        else:
            self._finish(running, "failed", "interrupted: landing stopped while the job ran")
        self.state["running"] = None
        self._try_save()

    # ---------- user actions: the device ----------

    def test_connection(self, server_url):
        """GET /info; returns the server's info dict or raises MgmtClientError."""
        _, info = _http(self._ssl, self.normalize_url(server_url), "GET", "/info")
        if info.get("service") != "cybics-mgmt":
            raise MgmtClientError("not_a_mgmt_server", "That address is not a CybICS-mgmt server.")
        return info

    def fingerprint(self):
        key = _pinned_key(self.state.get("signing_key"))
        return key_fingerprint(*key) if key else None

    def enroll(self, server_url, code, label=None):
        """
        Enrol this installation as a device, with an enrolment code or an
        event's join code. No action is allowed afterwards until the user
        switches some on; joining an event is a separate step (join_event).
        """
        server_url = self.normalize_url(server_url)
        try:
            device = dict(self.device_info() or {})
        except Exception as exc:
            raise MgmtClientError("device_info", f"Cannot read this installation's details: {exc}") from None
        _, resp = _http(self._ssl, server_url, "POST", "/enroll", timeout=ENROLL_TIMEOUT,
                        body={"code": code, "label": label, "device": device})
        key = _pinned_key(resp.get("signing_key"))
        if not (isinstance(resp.get("token"), str) and isinstance(resp.get("device_id"), str)):
            raise MgmtClientError("bad_response", "The server's enrolment answer is incomplete.")
        if key is None:
            raise MgmtClientError("bad_key", "The server sent no usable signing key (RSA, at least 3072 bits).")
        with self._lock:
            prev = self.state
            # A new device is in no event yet; what it had queued waits for it
            # to join the same team again.
            ctf = prev["ctf"]
            ctf["removed"] = ctf["joined"] or ctf["removed"]
            ctf["joined"] = False
            ctf["instance_id"] = None
            self.state = _empty_state()
            self.state.update({
                "enabled": True, "server_url": server_url, "device_id": resp["device_id"],
                "token": resp["token"], "device": resp.get("device") if isinstance(resp.get("device"), dict) else None,
                "signing_key": {"n": format(key[0], "x"), "e": key[1]}, "history": prev.get("history", []),
                "heartbeat_interval": _interval(resp.get("heartbeat_interval")), "ctf": ctf,
            })
            self._save_or_raise()
        self._wake.set()
        return resp

    def leave(self):
        """
        Disconnect from the server: the device is retired there and leaves its
        event. Best effort towards the server; always disables locally.
        """
        with self._lock:
            token, url = self.state.get("token"), self.state.get("server_url")
            ctf = self._ctf_left(self.state["ctf"])
            history = self.state.get("history", [])
            self.state = _empty_state()
            self.state.update({"server_url": url, "history": history, "ctf": ctf})
            try:
                self._save_or_raise()
            except MgmtClientError as exc:
                unsaved = exc
            else:
                unsaved = None
        if token and url:
            try:
                _http(self._ssl, url, "DELETE", "/device", token=token)
            except MgmtClientError:
                pass
        if unsaved:
            raise unsaved

    def set_allowed(self, actions):
        """The actions the server may ask for. Only known actions with a handler can be allowed."""
        allowed = sorted({a for a in (actions or []) if a in self.handlers})
        with self._lock:
            self.state["allowed"] = allowed
            # Jobs already queued for an action that is no longer allowed do not run.
            for job in [j for j in self.state["queue"] if j["action"] not in allowed]:
                self.state["queue"].remove(job)
                self._finish(job, "refused", "no longer allowed on this device")
            self._save_or_raise()
        self._wake.set()
        return allowed

    # ---------- user actions: the CTF ----------

    def join_event(self, join_code, team_name, team_password):
        """Join a team of an event (creating the team on first use)."""
        with self._lock:
            if not self.state["enabled"]:
                raise MgmtClientError("not_enrolled", "Connect to a CybICS-mgmt server first.")
            token = self.state["token"]
        # Read the baseline strictly, before talking to the server: joining
        # with an empty baseline because the progress file was unreadable
        # would report all old progress as new solves.
        try:
            baseline = sorted(set(self.local_solves() or []))
        except Exception as exc:
            raise MgmtClientError("progress_unreadable",
                                  f"Cannot read the local CTF progress, try again: {exc}") from None
        _, resp = self._request("POST", "/ctf/join", timeout=ENROLL_TIMEOUT, token=token, body={
            "join_code": join_code, "team_name": team_name, "team_password": team_password})
        if not (isinstance(resp.get("instance_id"), str) and isinstance(resp.get("event"), dict)
                and isinstance(resp.get("team"), dict)):
            raise MgmtClientError("bad_response", "The server's answer to joining is incomplete.")
        with self._lock:
            if self.state["token"] != token:
                raise MgmtClientError("stale", "The device was enrolled again meanwhile. Try again.")
            self._adopt(resp["instance_id"], resp["event"], resp["team"], baseline)
            self._save_or_raise()
        self._wake.set()
        return resp

    def leave_event(self):
        """
        Leave the event. Best effort towards the server; always leaves locally.
        The sync bookkeeping is kept in case the user joins the same team again.
        """
        with self._lock:
            was_in = self.state["ctf"]["joined"]
            self.state["ctf"] = self._ctf_left(self.state["ctf"])
            token = self.state["token"]
            self._save_or_raise()
        if was_in and token:
            try:
                self._request("DELETE", "/ctf/join", token=token)
            except MgmtClientError:
                pass

    def _ctf_left(self, ctf):
        """The CTF state after the user left on purpose (call with the lock held)."""
        left = _empty_ctf()
        left.update({k: ctf[k] for k in CARRY_OVER if k in ctf})
        left.update({"event": ctf.get("event"), "team": ctf.get("team"),
                     "left_local": sorted(set(self._safe_local_solves()))})
        return left

    def _adopt(self, instance_id, event, team, baseline):
        """
        The device is now in `team` of `event`, by joining or because the
        organiser put it there (call with the lock held). Same event and same
        team as before: keep what was queued, held or decided.
        """
        prev = self.state["ctf"]
        prev_event = prev.get("event") or {}
        # The slug alone is not enough: an organiser may delete an event and
        # recreate it under its old slug. And solves made for one team are
        # not reported again for another.
        same = (prev_event.get("slug") == event.get("slug")
                and prev_event.get("created_at") == event.get("created_at")
                and (prev.get("team") or {}).get("id") == team.get("id"))
        ctf = _empty_ctf()
        if same:
            ctf.update({k: prev[k] for k in CARRY_OVER if k in prev})
            if prev.get("left_local") is not None:
                # Solves made while the user had left stay unreported, like
                # any solve from before joining.
                made_while_left = set(baseline) - set(prev["left_local"])
                ctf["baseline"] = sorted(set(prev["baseline"]) | made_while_left)
        else:
            ctf["baseline"] = sorted(set(baseline))
        ctf.update({"joined": True, "instance_id": instance_id, "event": event,
                    "team": {k: team.get(k) for k in ("id", "name")}})
        self.state["ctf"] = ctf

    def report_solve(self, challenge_id, flag):
        """
        Queue a locally verified solve and nudge the sender. Never raises, never
        blocks: landing calls this in the middle of a local submission, which
        must succeed whatever happens to the server or this file.
        """
        try:
            with self._lock:
                ctf = self.state["ctf"]
                # Out of the event by the organiser: keep queuing, the device
                # will most likely be back, and these solves must not be lost.
                if not (ctf["joined"] or ctf["removed"]):
                    return
                if any(item["challenge_id"] == challenge_id for item in ctf["outbox"]):
                    return
                running = (ctf.get("event") or {}).get("state") == "running"
                ctf["outbox"].append({"challenge_id": challenge_id, "flag": flag,
                                      "solved_at": time.time(), "while_running": running})
                self._try_save()
            self._wake.set()
        except Exception:
            log.exception("cybics-mgmt: report_solve failed")

    def snapshot(self):
        """State for the landing page, without the token, the key or the baseline."""
        with self._lock:
            view = {k: v for k, v in self.state.items() if k not in ("token", "signing_key", "results", "ctf")}
            ctf = self.state["ctf"]
            view["ctf"] = {k: v for k, v in ctf.items() if k not in ("baseline", "left_local", "outbox")}
            view["ctf"]["pending"] = len(ctf["outbox"])
            view["ctf"]["outbox"] = [item["challenge_id"] for item in ctf["outbox"]]
            view["queue"] = [j["action"] for j in self.state["queue"]]
            view["key_fingerprint"] = self.fingerprint()
            view["available"] = sorted(self.handlers)
            return view

    # ---------- jobs ----------

    def _finish(self, job, state, detail=""):
        """Record a job's result for the server and the landing page (call with the lock held)."""
        detail = str(detail or "")[:500]
        self.state["results"].append({"id": job.get("id"), "seq": job.get("seq"), "state": state,
                                      "detail": detail})
        self.state["history"] = (self.state["history"] + [{
            "id": job.get("id"), "seq": job.get("seq"), "action": job.get("action"),
            "params": job.get("params"), "state": state, "detail": detail, "time": time.time()}])[-HISTORY_MAX:]

    def _accept(self, job):
        """
        Check one job from a heartbeat answer (call with the lock held). Only a
        job with a valid signature over this device and a new sequence number
        counts at all; anything else is dropped without an answer.
        """
        if not isinstance(job, dict):
            return
        seq = job.get("seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= self.state["last_seq"]:
            return   # seen before (the server repeats a job until its result arrives) or a replay
        if (job.get("device") != self.state["device_id"] or not isinstance(job.get("id"), str)
                or not isinstance(job.get("action"), str) or not isinstance(job.get("params"), dict)):
            return
        key = _pinned_key(self.state.get("signing_key"))
        try:
            valid = key is not None and verify_signature(key[0], key[1], job_message(job), job.get("signature"))
        except (TypeError, ValueError):
            valid = False
        if not valid:
            log.warning("cybics-mgmt: dropped job %r: the signature does not match the pinned key", job.get("id"))
            self.state["last_error"] = {"code": "bad_signature", "time": time.time(),
                                        "message": "A job with an invalid signature was ignored."}
            return
        self.state["last_seq"] = seq
        job = {k: job[k] for k in ("id", "seq", "action", "params")}
        if job["action"] not in self.state["allowed"] or job["action"] not in self.handlers:
            self._finish(job, "refused", "not allowed on this device")
        else:
            self.state["queue"].append(job)

    def run_next_job(self):
        """Run the oldest queued job. Returns False if there was none."""
        with self._lock:
            if not self.state["enabled"] or not self.state["queue"]:
                return False
            job = self.state["queue"].pop(0)
            device_id = self.state["device_id"]
            self.state["running"] = job
            self._try_save()   # before it runs: a restart may end this process
        try:
            result = self.handlers[job["action"]](dict(job["params"]))
            if job["action"] == "collect_logs":
                state, detail = "done", self._upload_logs(job, result)
            else:
                state, detail = "done", result if isinstance(result, str) else ""
        except MgmtClientError as exc:
            state, detail = "failed", exc.message
        except Exception as exc:
            log.exception("cybics-mgmt: job %s (%s) failed", job["id"], job["action"])
            state, detail = "failed", f"{exc.__class__.__name__}: {exc}"
        with self._lock:
            if self.state["device_id"] == device_id:   # not after a leave or a new enrolment
                self.state["running"] = None
                self._finish(job, state, detail)
                self._try_save()
        self._wake.set()   # report the result soon
        return True

    def _upload_logs(self, job, logs):
        if isinstance(logs, str):
            logs = logs.encode("utf-8", "replace")
        if not isinstance(logs, (bytes, bytearray)):
            raise MgmtClientError("bad_logs", "The log handler returned no logs.")
        logs = bytes(logs[-LOGS_RAW_MAX:])
        data = gzip.compress(logs)
        while len(data) > LOGS_MAX and len(logs) > 1024:
            logs = logs[len(logs) // 2:]   # keep the newest half until it fits
            data = gzip.compress(logs)
        self._request("POST", f"/jobs/{urllib.parse.quote(job['id'], safe='')}/logs", raw=data,
                      content_type="application/gzip", timeout=30)
        return f"{len(data) / 1024:.1f} KB uploaded"

    # ---------- sync ----------

    def _settle(self, item, result, refused=False):
        """
        Take a solve out of the outbox for good (call with the lock held).
        `refused` means `result` is the error code of a 4xx, not a `result` value.
        """
        ctf = self.state["ctf"]
        cid = item["challenge_id"]
        ctf["outbox"] = [i for i in ctf["outbox"] if i["challenge_id"] != cid]
        if result in DONE_RESULTS:
            return
        if not refused and result not in KNOWN_RESULTS:
            result = "invalid_flag"
        if result == "event_not_running" and item.get("while_running"):
            # Solved while the event ran, but the report only arrived after the
            # organiser paused or finished (the outbox may back off for
            # minutes, or the change came mid-flush). Hold it until a
            # heartbeat shows the event running again. A solve made while the
            # event was not running is not held.
            ctf["held_paused"] = sorted(set(ctf["held_paused"]) | {cid})
        elif result in ("unknown_challenge", "invalid_flag"):
            # This landing page checked the solve locally, so the server's
            # catalog disagrees: imported late, a challenge disabled for a
            # while, or the organiser imported another CybICS version's flags.
            # Hold it, and retry once the server's catalog (ids and flags)
            # changes. A cheater gains nothing: every retry is audited.
            ctf["held"][cid] = ctf["catalog_version"]
        else:
            # event_not_running (solved before the start or in a pause), or
            # a client error.
            ctf["rejected"] = sorted(set(ctf["rejected"]) | {cid})

    def _current(self, token, instance_id):
        """True if an answer belongs to the device and the instance still in place (lock held)."""
        ctf = self.state["ctf"]
        return self.state["token"] == token and ctf["joined"] and ctf["instance_id"] == instance_id

    def _flush_outbox(self):
        with self._lock:
            ctf = self.state["ctf"]
            if not ctf["joined"]:
                return
            pending = list(ctf["outbox"])
            token, instance_id = self.state["token"], ctf["instance_id"]
        for item in pending:
            try:
                _, resp = self._request("POST", "/solves", body=item, token=token)
                result, refused = resp.get("result"), False
                if not isinstance(result, str) or not result:
                    result = "unknown_result"   # a list would break the set lookups in _settle()
            except MgmtClientError as exc:
                if exc.code == "not_in_event" and exc.from_server:
                    # The organiser took the device out of its event: keep the
                    # solve queued for when it is back.
                    with self._lock:
                        if self._current(token, instance_id):
                            self.state["ctf"]["joined"] = False
                            self.state["ctf"]["removed"] = True
                            self._try_save()
                    return
                # 401/403/429 concern the device or team, not this solve; 5xx
                # and transport errors are transient; and a 4xx that is not
                # this server's JSON (a proxy's 404/408/413 page while the
                # backend restarts) says nothing about the solve. Keep it queued.
                if (exc.status is None or exc.status >= 500 or exc.status in (401, 403, 429)
                        or not exc.from_server):
                    raise
                result, refused = exc.code, True   # this server refused this solve: it never will accept it
            with self._lock:
                if not self._current(token, instance_id):
                    return   # the user left, re-joined or re-enrolled meanwhile
                self._settle(item, result, refused)
                self._try_save()

    def _heartbeat(self):
        with self._lock:
            token = self.state["token"]
            results = list(self.state["results"])
            management = {"allowed": list(self.state["allowed"]), "key_fingerprint": self.fingerprint(),
                          "client": CLIENT_VERSION}
            after = self.state["ctf"]["last_announcement_id"]
        try:
            status = dict(self.status() or {})
        except Exception:
            status = {}
        status.setdefault("local_solved", self._safe_local_solves())
        _, resp = self._request("POST", "/heartbeat", token=token, body={
            "status": status, "management": management, "job_results": results, "announcements_after": after})
        with self._lock:
            if not (self.state["enabled"] and self.state["token"] == token):
                return   # an answer for an enrolment that no longer exists
            sent = {r["id"] for r in results}
            self.state["results"] = [r for r in self.state["results"] if r["id"] not in sent]
            if isinstance(resp.get("device"), dict):
                self.state["device"] = {k: resp["device"].get(k) for k in ("id", "label", "group")}
            self.state["heartbeat_interval"] = _interval(resp.get("heartbeat_interval"))
            jobs = resp.get("jobs")
            if isinstance(jobs, list):
                for job in sorted((j for j in jobs if isinstance(j, dict) and isinstance(j.get("seq"), int)),
                                  key=lambda j: j["seq"]):
                    self._accept(job)
            self._apply_ctf(resp.get("ctf"))
            queued = bool(self.state["queue"])
            self._try_save()
        if queued:
            self._work.set()

    def _apply_ctf(self, block):
        """The CTF part of a heartbeat answer (call with the lock held)."""
        ctf = self.state["ctf"]
        if not isinstance(block, dict):
            if ctf["joined"]:
                # Taken out of the event (the organiser, or the team or event
                # was deleted): stop sending, keep queuing until it is back.
                ctf["joined"] = False
                ctf["removed"] = True
            return
        event, team = block.get("event"), block.get("team")
        if not (isinstance(block.get("instance_id"), str) and isinstance(event, dict) and isinstance(team, dict)):
            return
        if not ctf["joined"] or block["instance_id"] != ctf["instance_id"]:
            # The organiser put the device into a team (or moved it).
            try:
                baseline = list(self.local_solves() or [])
            except Exception:
                return   # the progress file is unreadable right now: adopt it next round
            self._adopt(block["instance_id"], event, team, baseline)
            ctf = self.state["ctf"]
        ctf["event"] = event
        ctf["team"] = {k: team.get(k) for k in ("id", "name")}
        ctf["standing"] = {k: team.get(k) for k in ("score", "rank", "teams", "banned")}
        solved = block.get("solved")
        ctf["server_solved"] = solved if isinstance(solved, list) else []
        if event.get("state") == "running":
            # Running (again): give held solves another try. They stay held
            # through a pause and after the end, because an organiser can
            # reopen an event that was finished by mistake.
            ctf["held_paused"] = []
        version = block.get("catalog_version")
        if version != ctf["catalog_version"]:
            ctf["catalog_version"] = version
            ctf["held"] = {}   # the catalog changed: give held solves another try
        live = block.get("announcement_ids")
        if isinstance(live, list):   # the organiser deleted some
            ctf["announcements"] = [a for a in ctf["announcements"] if a.get("id") in live]
        news = [a for a in block.get("announcements") or [] if isinstance(a, dict) and isinstance(a.get("id"), int)]
        if news:
            ctf["announcements"] = (ctf["announcements"] + news)[-20:]
            ctf["last_announcement_id"] = max(a["id"] for a in news)
        # Reconcile: a local solve the server does not know about (lost
        # outbox, removed by the organiser, solved while offline) is queued
        # again. Only while running, otherwise it would just bounce.
        if event.get("state") == "running":
            known = (set(ctf["server_solved"]) | set(ctf["baseline"]) | set(ctf["rejected"])
                     | set(ctf["held"]) | set(ctf["held_paused"]) | {i["challenge_id"] for i in ctf["outbox"]})
            for cid in self._safe_local_solves():
                if cid in known:
                    continue
                flag = None
                try:
                    flag = self.flag_for(cid)
                except Exception:
                    pass
                if flag:
                    ctf["outbox"].append({"challenge_id": cid, "flag": flag, "solved_at": None,
                                          "while_running": True})

    def sync_once(self):
        """One heartbeat plus outbox flush. Returns True on success."""
        with self._lock:
            if not self.state["enabled"]:
                return False
            token = self.state["token"]
        try:
            self._heartbeat()
            self._flush_outbox()
        except MgmtClientError as exc:
            with self._lock:
                if self.state["token"] != token:
                    return False   # stale failure from before a leave or re-enrolment
                self.state["last_error"] = {"code": exc.code, "message": exc.message, "time": time.time()}
                if exc.status == 401 and exc.from_server:
                    # (A 401 page from some proxy in between says nothing about
                    # the enrolment; it is retried like any transport error.)
                    # Retired by the organiser: stop talking to the server
                    # until the user enrols again, but keep queuing solves.
                    # (403 team_banned is not final: the organiser can
                    # reinstate the team, so the client keeps trying.)
                    ctf = self.state["ctf"]
                    ctf["removed"] = ctf["joined"] or ctf["removed"]
                    ctf["joined"] = False
                    self.state["enabled"] = False
                    self.state["revoked"] = True
                    self.state["queue"] = []
                self._try_save()
            return False
        with self._lock:
            if self.state["token"] == token:
                self.state["last_contact"] = time.time()
                if (self.state["last_error"] or {}).get("code") != "bad_signature":
                    self.state["last_error"] = None
                self._try_save()
        return True

    # ---------- background loops ----------

    def start(self):
        if any(t.is_alive() for t in self._threads):
            return
        self._stop.clear()
        self._threads = [threading.Thread(target=self._run, name="cybics-mgmt", daemon=True),
                         threading.Thread(target=self._run_jobs, name="cybics-mgmt-jobs", daemon=True)]
        for thread in self._threads:
            thread.start()

    def stop(self):
        self._stop.set()
        self._wake.set()
        self._work.set()

    def _run(self):
        failures = 0
        while not self._stop.is_set():
            try:
                ok = self.sync_once()
            except Exception:
                # Never let the sender thread die: a bug or an unexpected
                # answer would otherwise stop all reporting until landing
                # restarts. Log it and back off like for a network error.
                log.exception("cybics-mgmt: sync failed")
                ok = False
            failures = 0 if ok else failures + 1
            with self._lock:
                interval = _interval(self.state.get("heartbeat_interval"))
                enabled = self.state["enabled"]
            # Back off up to 5 minutes while the server is unreachable.
            delay = interval if ok or not enabled else min(300, interval * (2 ** min(failures, 4)))
            self._wake.wait(delay if enabled else 3600)
            self._wake.clear()

    def _run_jobs(self):
        """Jobs run one at a time on their own thread, so heartbeats keep going meanwhile."""
        while not self._stop.is_set():
            try:
                while self.run_next_job():
                    pass
            except Exception:
                log.exception("cybics-mgmt: job runner failed")
            self._work.wait(60)
            self._work.clear()
