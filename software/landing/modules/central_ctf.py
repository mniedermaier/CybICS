"""
Reference client for the CybICS CTF central server.

Meant to be vendored into CybICS' landing service (software/landing/modules/)
as a single file: standard library only, Python 3.9+.

Design rules, all following from "the central server is optional":

* Nothing happens until the user enrols from the landing page. A fresh or
  disabled client makes no network calls at all.
* The landing page keeps validating flags locally. The client only *reports*
  local solves; a server that is down, slow or gone never blocks or fails a
  local submission.
* Reports survive outages. Solves sit in a persistent outbox until the server
  answers with a final result, and every heartbeat reconciles the local solve
  list with the server's, so nothing is lost if the outbox file is.
* Solves that existed locally before enrolment (old progress on a reused Pi)
  are not reported: the client snapshots them as a baseline at enrolment.

Typical wiring in landing:

    client = CTFClient(state_path="data/central_ctf.json",
                       local_solves=lambda: ctf_manager.load_progress()["solved_challenges"],
                       flag_for=lambda cid: (ctf_manager.get_challenge(cid)[0] or {}).get("flag"),
                       status=collect_status)
    client.start()                         # background heartbeat if enrolled
    ...
    # after a successful local /ctf/submit or /ctf/verify:
    client.report_solve(challenge_id, flag)
"""
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

log = logging.getLogger("central_ctf")

API_PREFIX = "/api/v1"
DEFAULT_INTERVAL = 30
TIMEOUT = 8
# Enrolment may queue briefly at the proxy when a whole class joins at once.
ENROLL_TIMEOUT = 30

# Results that mean "counted, or already on record". Every other result is
# final too (the solve leaves the outbox), but the solve is not reported again;
# see _settle(). Unknown future result values are treated the same way.
DONE_RESULTS = {"accepted", "duplicate"}


class CTFClientError(Exception):
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


def _interval(value):
    """The server's heartbeat interval, defended: it decides how often a thread wakes up."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        return DEFAULT_INTERVAL
    return int(min(3600, max(5, value)))


def _empty_state():
    return {
        "enabled": False,
        "server_url": None,
        "instance_id": None,
        "token": None,
        "team": None,
        "event": None,
        "baseline": [],          # local solves that predate enrolment, never reported
        "outbox": [],            # [{challenge_id, flag, solved_at}]
        "rejected": [],          # challenge ids the server refused for good
        "held": {},              # challenge id -> catalog_version it was unknown in
        "held_paused": [],       # solved while running, delivered during a pause
        "catalog_version": None,
        "server_solved": [],
        "standing": None,        # {score, rank, teams}
        "announcements": [],
        "last_announcement_id": 0,
        "last_contact": None,
        "last_error": None,
        "heartbeat_interval": DEFAULT_INTERVAL,
        "revoked": False,        # disabled by a 401, not by the user: keep queuing
        "left_local": None,      # local solves when the user left; see enroll()
    }


# Carried over when the instance enrols again with the same server and event,
# so nothing that was queued, held or decided is lost by re-enrolling.
CARRY_OVER = ("baseline", "outbox", "rejected", "held", "held_paused", "server_solved",
              "announcements", "last_announcement_id", "catalog_version")


class CTFClient:
    def __init__(self, state_path, local_solves=lambda: [], flag_for=lambda _cid: None,
                 status=lambda: {}, ca_file=None):
        """
        state_path   JSON file holding enrolment and outbox (put it on a volume)
        local_solves callable returning the challenge ids solved locally
        flag_for     callable mapping a challenge id to its flag (from ctf_config.json)
        status       callable returning the status dict sent with each heartbeat
        ca_file      optional CA bundle for a server with a private certificate
        """
        self.state_path = state_path
        self.local_solves = local_solves
        self.flag_for = flag_for
        self.status = status
        self._ssl = ssl.create_default_context(cafile=ca_file) if ca_file else None
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread = None
        self.state = self._load()

    # ---------- persistence ----------

    def _load(self):
        state = _empty_state()
        try:
            with open(self.state_path, encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                state.update({k: v for k, v in saved.items() if k in state})
        except (OSError, ValueError):
            pass
        return state

    def _save(self):
        directory = os.path.dirname(os.path.abspath(self.state_path))
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".central_ctf.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())   # a Pi may lose power at any moment
            os.chmod(tmp, 0o600)   # holds the instance token
            os.replace(tmp, self.state_path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ---------- HTTP ----------

    def _request(self, method, path, body=None, token=None, server_url=None, timeout=TIMEOUT):
        base = (server_url or self.state["server_url"] or "").rstrip("/")
        req = urllib.request.Request(base + API_PREFIX + path, method=method)  # noqa: S310 (see below)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "cybics-landing")
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            # The scheme is http(s) only: server_url always passes normalize_url().
            with urllib.request.urlopen(req, data=data, timeout=timeout, context=self._ssl) as resp:  # noqa: S310
                raw = resp.read()
                body = json.loads(raw) if raw else {}
                if not isinstance(body, dict):
                    raise ValueError("not a JSON object")
                return resp.status, body
        except urllib.error.HTTPError as exc:
            try:
                err = json.loads(exc.read()).get("error")
            except (ValueError, AttributeError, OSError, http.client.HTTPException):
                err = None
            ours = isinstance(err, dict) and isinstance(err.get("code"), str)
            err = err if ours else {}
            raise CTFClientError(err.get("code", f"http_{exc.code}"),
                                 err.get("message", f"Server answered HTTP {exc.code}."),
                                 exc.code, from_server=ours) from None
        except (OSError, http.client.HTTPException) as exc:
            # URLError, timeouts, resets, TLS errors (all OSError) and a body
            # cut off mid-transfer (IncompleteRead) on flaky Wi-Fi.
            reason = getattr(exc, "reason", None) or exc.__class__.__name__
            raise CTFClientError("unreachable", f"Cannot reach the CTF server: {reason}") from None
        except ValueError:   # includes JSONDecodeError and UnicodeDecodeError
            raise CTFClientError("bad_response", "The server did not answer with a JSON object.") from None

    @staticmethod
    def normalize_url(url):
        url = (url or "").strip().rstrip("/")
        if "://" not in url:
            url = "http://" + url
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise CTFClientError("invalid_url", "Enter a server address like http://10.10.0.1:8000.")
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    # ---------- user actions (landing settings page) ----------

    def test_connection(self, server_url):
        """GET /info; returns the server's info dict or raises CTFClientError."""
        _, info = self._request("GET", "/info", server_url=self.normalize_url(server_url))
        if info.get("service") != "cybics-ctf":
            raise CTFClientError("not_a_ctf_server", "That address is not a CybICS CTF server.")
        return info

    def enroll(self, server_url, join_code, team_name, team_password, instance):
        """
        instance: {"kind": "virtual"|"physical", "device_uid": <STM32 UID hex, physical only>,
                   "hostname": ..., "cybics_version": ..., "mode": ...}
        """
        server_url = self.normalize_url(server_url)
        # Read the baseline strictly, before talking to the server: enrolling
        # with an empty baseline because the progress file was unreadable would
        # report all old progress as new solves.
        try:
            baseline = sorted(set(self.local_solves() or []))
        except Exception as exc:
            raise CTFClientError("progress_unreadable",
                                 f"Cannot read the local CTF progress, try again: {exc}") from None
        _, resp = self._request("POST", "/enroll", server_url=server_url, timeout=ENROLL_TIMEOUT, body={
            "join_code": join_code, "team_name": team_name, "team_password": team_password,
            "instance": instance})
        if not (isinstance(resp.get("token"), str) and isinstance(resp.get("instance_id"), str)
                and isinstance(resp.get("event"), dict)):
            raise CTFClientError("bad_response", "The server's enrolment answer is incomplete.")
        with self._lock:
            prev = self.state
            # Same server and the same event: the slug alone is not enough, an
            # organiser may delete an event and recreate it under its old slug.
            prev_event = prev.get("event") or {}
            # And the same team: solves made for one team are not reported
            # again for another after a leave and join (that starts fresh,
            # with every current local solve as the baseline).
            same = (prev.get("server_url") == server_url
                    and prev_event.get("slug") == resp["event"].get("slug")
                    and prev_event.get("created_at") == resp["event"].get("created_at")
                    and (prev.get("team") or {}).get("id") == (resp.get("team") or {}).get("id"))
            self.state = _empty_state()
            if same:
                # Re-enrolling after a revocation, or leave + join to fix the
                # team name: keep what was queued, held or decided. Solves made
                # while the user had left stay unreported, like any solve from
                # before enrolment.
                self.state.update({k: prev[k] for k in CARRY_OVER if k in prev})
                if prev.get("left_local") is not None:
                    made_while_left = set(baseline) - set(prev["left_local"])
                    self.state["baseline"] = sorted(set(prev["baseline"]) | made_while_left)
            else:
                self.state["baseline"] = baseline
            self.state.update({
                "enabled": True, "server_url": server_url,
                "instance_id": resp["instance_id"], "token": resp["token"],
                "team": resp.get("team"), "event": resp["event"],
                "heartbeat_interval": _interval(resp.get("heartbeat_interval")),
            })
            self._save()
        self._wake.set()
        return resp

    def leave(self):
        """
        Switch the central server off. Best effort towards the server; always
        disables locally. The token is dropped; the sync bookkeeping is kept in
        case the user joins the same event again (see enroll()).
        """
        with self._lock:
            token, url = self.state.get("token"), self.state.get("server_url")
            kept = {k: self.state[k] for k in CARRY_OVER if k in self.state}
            event, team = self.state.get("event"), self.state.get("team")
            self.state = _empty_state()
            self.state.update(kept)
            self.state.update({"server_url": url, "event": event, "team": team,
                               "left_local": sorted(set(self._safe_local_solves()))})
            self._save()
        if token and url:
            try:
                self._request("DELETE", "/instance", token=token, server_url=url)
            except CTFClientError:
                pass

    def report_solve(self, challenge_id, flag):
        """
        Queue a locally verified solve and nudge the sender. Never raises, never
        blocks: landing calls this in the middle of a local submission, which
        must succeed whatever happens to the central server or this file.
        """
        try:
            with self._lock:
                # After a revocation, keep queuing: the user will most likely
                # enrol again, and these solves must not be lost.
                if not (self.state["enabled"] or self.state["revoked"]):
                    return
                if any(item["challenge_id"] == challenge_id for item in self.state["outbox"]):
                    return
                running = (self.state.get("event") or {}).get("state") == "running"
                self.state["outbox"].append({"challenge_id": challenge_id, "flag": flag,
                                             "solved_at": time.time(), "while_running": running})
                try:
                    self._save()
                except OSError as exc:   # full SD card, read-only volume: keep it in memory
                    log.warning("central CTF: cannot save the outbox: %s", exc)
                    self.state["last_error"] = {"code": "storage", "time": time.time(),
                                                "message": f"Cannot save pending reports: {exc}"}
            self._wake.set()
        except Exception:
            log.exception("central CTF: report_solve failed")

    def snapshot(self):
        """State for the landing page, without the token."""
        with self._lock:
            view = {k: v for k, v in self.state.items() if k not in ("token", "baseline", "left_local")}
            view["pending"] = len(self.state["outbox"])
            view["outbox"] = [item["challenge_id"] for item in self.state["outbox"]]
            return view

    # ---------- sync ----------

    def _safe_local_solves(self):
        try:
            return list(self.local_solves() or [])
        except Exception:  # landing's progress file may be mid-write; try again next round
            return []

    def _current(self, token):
        """True if `token` still belongs to the active enrolment (call with the lock held)."""
        return self.state["enabled"] and self.state["token"] == token

    def _settle(self, item, result):
        """Take a solve out of the outbox for good (call with the lock held)."""
        cid = item["challenge_id"]
        self.state["outbox"] = [i for i in self.state["outbox"] if i["challenge_id"] != cid]
        if result in DONE_RESULTS:
            return
        if result == "event_not_running" and item.get("while_running"):
            # Solved while the event ran, but the report only arrived after the
            # organiser paused or finished (the outbox may back off for
            # minutes, or the change came mid-flush). Hold it until a
            # heartbeat shows the event running again. A solve made while the
            # event was not running is not held.
            self.state["held_paused"] = sorted(set(self.state["held_paused"]) | {cid})
        elif result in ("unknown_challenge", "invalid_flag"):
            # This landing page checked the solve locally, so the server's
            # catalog disagrees: imported late, a challenge disabled for a
            # while, or the organiser imported another CybICS version's flags.
            # Hold it, and retry once the server's catalog (ids and flags)
            # changes. A cheater gains nothing: every retry is audited.
            self.state["held"][cid] = self.state["catalog_version"]
        else:
            # event_not_running (solved before the start or in a pause), a
            # client error, or a result this client does not know.
            self.state["rejected"] = sorted(set(self.state["rejected"]) | {cid})

    def _flush_outbox(self):
        with self._lock:
            pending = list(self.state["outbox"])
            token = self.state["token"]
        for item in pending:
            try:
                _, resp = self._request("POST", "/solves", body=item, token=token)
                result = resp.get("result") or "unknown_result"
            except CTFClientError as exc:
                # 401/403/429 concern the instance, not this solve; 5xx and
                # transport errors are transient; and a 4xx that is not this
                # server's JSON (a proxy's 404/408/413 page while the backend
                # restarts) says nothing about the solve. Keep it queued.
                if (exc.status is None or exc.status >= 500 or exc.status in (401, 403, 429)
                        or not exc.from_server):
                    raise
                result = exc.code   # this server refused this solve: it never will accept it
            with self._lock:
                if not self._current(token):
                    return   # the user left or re-enrolled meanwhile
                self._settle(item, result)
                self._save()

    def _heartbeat(self):
        with self._lock:
            token = self.state["token"]
            after = self.state["last_announcement_id"]
        try:
            status = dict(self.status() or {})
        except Exception:
            status = {}
        status.setdefault("local_solved", self._safe_local_solves())
        _, resp = self._request("POST", "/heartbeat", token=token,
                                body={"status": status, "announcements_after": after})
        with self._lock:
            if not self._current(token):
                return   # an answer for an enrolment that no longer exists
            self.state["event"] = resp.get("event")
            self.state["team"] = {k: resp["team"][k] for k in ("id", "name") if k in resp.get("team", {})}
            self.state["standing"] = {k: resp.get("team", {}).get(k) for k in ("score", "rank", "teams")}
            self.state["server_solved"] = resp.get("solved", [])
            self.state["heartbeat_interval"] = _interval(resp.get("heartbeat_interval"))
            if (resp.get("event") or {}).get("state") == "running":
                # Running (again): give held solves another try. They stay held
                # through a pause and after the end, because an organiser can
                # reopen an event that was finished by mistake.
                self.state["held_paused"] = []
            version = resp.get("catalog_version")
            if version != self.state["catalog_version"]:
                self.state["catalog_version"] = version
                self.state["held"] = {}   # the catalog changed: give held solves another try
            live = resp.get("announcement_ids")
            if isinstance(live, list):   # the organiser deleted some
                self.state["announcements"] = [a for a in self.state["announcements"] if a.get("id") in live]
            news = resp.get("announcements", [])
            if news:
                self.state["announcements"] = (self.state["announcements"] + news)[-20:]
                self.state["last_announcement_id"] = max(a["id"] for a in news)
            # Reconcile: a local solve the server does not know about (lost
            # outbox, removed by the organiser, solved while offline) is queued
            # again. Only while running, otherwise it would just bounce.
            if (resp.get("event") or {}).get("state") == "running":
                known = (set(self.state["server_solved"]) | set(self.state["baseline"])
                         | set(self.state["rejected"]) | set(self.state["held"])
                         | set(self.state["held_paused"])
                         | {i["challenge_id"] for i in self.state["outbox"]})
                for cid in self._safe_local_solves():
                    if cid in known:
                        continue
                    flag = None
                    try:
                        flag = self.flag_for(cid)
                    except Exception:
                        pass
                    if flag:
                        self.state["outbox"].append({"challenge_id": cid, "flag": flag,
                                                     "solved_at": None, "while_running": True})
            self._save()

    def sync_once(self):
        """One heartbeat plus outbox flush. Returns True on success."""
        with self._lock:
            if not self.state["enabled"]:
                return False
            token = self.state["token"]
        try:
            self._heartbeat()
            self._flush_outbox()
        except CTFClientError as exc:
            with self._lock:
                if not self._current(token):
                    return False   # stale failure from before a leave/re-enrol
                self.state["last_error"] = {"code": exc.code, "message": exc.message, "time": time.time()}
                if exc.status == 401 and exc.from_server:
                    # (A 401 page from some proxy in between says nothing about
                    # the enrolment; it is retried like any transport error.)
                    # Revoked by the organiser or the event was deleted: stop
                    # talking to the server until the user enrols again.
                    # (403 team_banned is not final: the organiser can reinstate
                    # the team, so the client keeps trying with backoff.)
                    self.state["enabled"] = False
                    self.state["revoked"] = True
                self._save()
            return False
        with self._lock:
            if not self._current(token):
                return False
            self.state["last_contact"] = time.time()
            self.state["last_error"] = None
            self._save()
        return True

    # ---------- background loop ----------

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="central-ctf", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._wake.set()

    def _run(self):
        failures = 0
        while not self._stop.is_set():
            try:
                ok = self.sync_once()
            except Exception:
                # Never let the sender thread die: a bug or an unexpected
                # answer would otherwise stop all reporting until landing
                # restarts. Log it and back off like for a network error.
                log.exception("central CTF: sync failed")
                ok = False
            failures = 0 if ok else failures + 1
            with self._lock:
                interval = _interval(self.state.get("heartbeat_interval"))
                enabled = self.state["enabled"]
            # Back off up to 5 minutes while the server is unreachable.
            delay = interval if ok or not enabled else min(300, interval * (2 ** min(failures, 4)))
            self._wake.wait(delay if enabled else 3600)
            self._wake.clear()
