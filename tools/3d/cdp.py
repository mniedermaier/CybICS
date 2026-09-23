"""A minimal Chrome DevTools Protocol client, standard library only.

There is deliberately no dependency here.  The host this runs on has no pip and
no venv, and a tool that cannot be run without first solving a packaging problem
is a tool nobody runs.  CDP is JSON over a websocket, and the subset needed to
drive a page -- handshake, masked text frames, reassembly -- is small enough to
carry.
"""
import base64
import json
import os
import secrets
import socket
import struct
import subprocess
import time
import urllib.request


class WebSocket:
    """Just enough RFC 6455 to talk to Chrome."""

    def __init__(self, url, timeout=120):
        assert url.startswith("ws://"), url
        rest = url[5:]
        hostport, _, path = rest.partition("/")
        host, _, port = hostport.partition(":")
        self.sock = socket.create_connection((host, int(port or 80)), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        self.sock.sendall(
            (
                f"GET /{path} HTTP/1.1\r\n"
                f"Host: {hostport}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        head = b""
        while b"\r\n\r\n" not in head:
            head += self.sock.recv(1)
        if b"101" not in head.split(b"\r\n")[0]:
            raise RuntimeError("websocket handshake refused: " + head.decode(errors="replace")[:200])

    def _recv_exactly(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("socket closed")
            buf += chunk
        return buf

    def send(self, text):
        payload = text.encode()
        header = bytearray([0x81])  # FIN + text
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < (1 << 16):
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        mask = secrets.token_bytes(4)
        header += mask
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def recv(self):
        """One complete message, reassembling continuation frames."""
        chunks = []
        while True:
            b0, b1 = self._recv_exactly(2)
            fin = b0 & 0x80
            opcode = b0 & 0x0F
            length = b1 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._recv_exactly(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._recv_exactly(8))[0]
            data = self._recv_exactly(length) if length else b""
            if opcode == 0x8:
                raise ConnectionError("closed by peer")
            if opcode == 0x9:  # ping -> pong
                continue
            chunks.append(data)
            if fin:
                return b"".join(chunks).decode(errors="replace")

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class Browser:
    """A headless Chrome, started and stopped by us."""

    def __init__(self, port=9222, width=1400, height=900, profile=None, software_gl=True):
        self.port = port
        profile = profile or f"/tmp/cybics-3d-chrome-{port}"
        args = [
            self._chrome(),
            "--headless=new",
            f"--remote-debugging-port={port}",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-timer-throttling",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
        ]
        if software_gl:
            # SwiftShader is slower than any real GPU, which makes it the
            # honest place to check that the scene stays inside its budget.
            args += ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"]
        else:
            # Headless Chrome defaults back to SwiftShader even when a GPU is
            # present, and then reports itself as hardware.  ANGLE over desktop
            # GL is the combination that actually reaches the DRI node; plain
            # --use-gl=egl yields no WebGL context at all here.  Verify with the
            # "gpu" field of the report rather than trusting the flag.
            args += [
                "--use-gl=angle",
                "--use-angle=gl",
                "--ignore-gpu-blocklist",
                "--disable-gpu-sandbox",
            ]
        args.append("about:blank")
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._wait_for_port()

    @staticmethod
    def _chrome():
        for name in ("google-chrome", "chromium", "chromium-browser"):
            path = subprocess.run(["which", name], capture_output=True, text=True).stdout.strip()
            if path:
                return path
        raise RuntimeError("no chrome/chromium on PATH")

    def _wait_for_port(self, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version", timeout=2)
                return
            except Exception:
                time.sleep(0.3)
        raise RuntimeError("chrome did not open its debugging port")

    def page(self):
        targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json"))
        for t in targets:
            if t["type"] == "page":
                return Page(t["webSocketDebuggerUrl"])
        raise RuntimeError("no page target")

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


class Page:
    def __init__(self, ws_url):
        self.ws = WebSocket(ws_url)
        self._id = 0
        self.events = []
        for domain in ("Page", "Runtime", "Log"):
            self.send(domain + ".enable")

    def send(self, method, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self._id:
                return msg
            if "method" in msg:
                self.events.append(msg)

    def pump(self):
        """Drain any events that arrived while we were not asking."""
        self.ws.sock.settimeout(0.2)
        try:
            while True:
                msg = json.loads(self.ws.recv())
                if "method" in msg:
                    self.events.append(msg)
        except Exception:
            pass
        finally:
            self.ws.sock.settimeout(120)

    def eval(self, expression, await_promise=False):
        r = self.send(
            "Runtime.evaluate",
            expression=expression,
            returnByValue=True,
            awaitPromise=await_promise,
        )
        result = r.get("result", {})
        if "exceptionDetails" in result:
            raise RuntimeError(str(result["exceptionDetails"])[:400])
        value = result.get("result", {})
        # NaN, Infinity and -0 have no JSON spelling, so CDP sends them under a
        # different key.  Reading only "value" turns them into None, which then
        # looks like a probe that measured nothing rather than one that went
        # wrong -- exactly the kind of silent null this tool must not produce.
        if "value" not in value and "unserializableValue" in value:
            raise RuntimeError("unserializable result: %s" % value["unserializableValue"])
        return value.get("value")

    def navigate(self, url):
        self.send("Page.navigate", url=url)

    def screenshot(self, path):
        data = self.send("Page.captureScreenshot", format="png")["result"]["data"]
        raw = base64.b64decode(data)
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(raw)
        return len(raw)

    def console_errors(self):
        out = []
        for e in self.events:
            if e["method"] == "Runtime.exceptionThrown":
                d = e["params"]["exceptionDetails"]
                out.append(str(d.get("text")) + " " + str(d.get("exception", {}).get("description", ""))[:200])
            elif e["method"] == "Log.entryAdded" and e["params"]["entry"]["level"] == "error":
                out.append(e["params"]["entry"]["text"][:200])
        return out

    def navigations(self):
        return [e for e in self.events if e["method"] == "Page.frameNavigated"]

    def close(self):
        self.ws.close()
