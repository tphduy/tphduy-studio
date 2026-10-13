"""Headless client for QMUI LookinServer 1.2.8 (protocol 7) on the iOS simulator.

The server is injected at launch from the bundled ../vendor/LookinServer.framework (rebuilt by
build-lookinserver.sh), or embedded by the app itself.
It listens on the host loopback, first free port in 47164-47169; several simulators share that range,
so pick the server by the app's PID, not by port.

usage:
  lookin.py scan                         list servers: port, pid, app, bundle id, OS, protocol
  lookin.py dump (PORT | --pid PID) [--print-tree CONSOLE.txt] [--raw OUT.json]
                                         one line per view: class, window frame in points,
                                         hidden/alpha, UIKit text, gesture actions, and with
                                         --print-tree the SwiftUI text, images and shapes each hosting
                                         view draws, in window points
  lookin.py ping PORT

LookinServer sees UIKit text only (UILabel, UITextField, ...). For SwiftUI text, launch with
  SIMCTL_CHILD_SWIFTUI_PRINT_TREE=1 SIMCTL_CHILD_DYLD_INSERT_LIBRARIES=<skill>/vendor/LookinServer.framework/LookinServer \\
    xcrun simctl launch --console <udid> <bundle-id> > console.txt
keep that process running (ending it ends the app), and pass console.txt to --print-tree. Only each
hosting view's latest display list is used; views no longer on screen are dropped. SWIFTUI_PRINT_TREE is
an undocumented debug switch and may change in any OS release.
Frames are window points, usable as tap coordinates after checking the view is visible and not covered.

Exit codes: 0 ok, 2 no server found, 3 server returned an error or unexpected response.
"""
import json, plistlib, re, socket, struct, subprocess, sys, time
from dataclasses import dataclass
from enum import IntEnum
from plistlib import UID

PORTS = range(47164, 47170)
CLIENT_VERSION = "1.0.7"


# ---------- NSKeyedArchiver encode ----------
@dataclass(frozen=True)
class Obj:
    """An Objective-C object to archive: class name, class chain, and {key: ("obj" | "raw", value)}."""
    cls: str
    chain: list
    fields: dict


class HandlerType(IntEnum):
    """LookinEventHandlerType."""
    TARGET_ACTION = 0
    GESTURE = 1


def archive(root):
    objects = ["$null"]
    classes = {}

    def cls_uid(name, chain):
        if name not in classes:
            objects.append({"$classname": name, "$classes": chain})
            classes[name] = UID(len(objects) - 1)
        return classes[name]

    def enc(v):
        if v is None:
            return UID(0)
        idx = len(objects)
        objects.append(None)
        if isinstance(v, (str, int, float, bool)) and not isinstance(v, Obj):
            objects[idx] = v
        elif isinstance(v, list):
            objects[idx] = {"NS.objects": [enc(x) for x in v], "$class": cls_uid("NSArray", ["NSArray", "NSObject"])}
        elif isinstance(v, dict):
            keys = list(v)
            objects[idx] = {"NS.keys": [enc(k) for k in keys], "NS.objects": [enc(v[k]) for k in keys],
                            "$class": cls_uid("NSDictionary", ["NSDictionary", "NSObject"])}
        elif isinstance(v, Obj):
            d = {}
            for k, (kind, val) in v.fields.items():
                d[k] = enc(val) if kind == "obj" else val  # "raw" = encodeInteger/encodeBool
            d["$class"] = cls_uid(v.cls, v.chain)
            objects[idx] = d
        else:
            raise TypeError(v)
        return UID(idx)

    top = enc(root)
    return plistlib.dumps({"$version": 100000, "$archiver": "NSKeyedArchiver",
                           "$top": {"root": top}, "$objects": objects}, fmt=plistlib.FMT_BINARY)


def attachment(data):
    return Obj("LookinConnectionAttachment", ["LookinConnectionAttachment", "NSObject"],
               {"0": ("obj", data), "1": ("raw", 0)})


def task(oid):
    return Obj("LookinStaticAsyncUpdateTask", ["LookinStaticAsyncUpdateTask", "NSObject"], {
        "oid": ("obj", oid), "taskType": ("raw", 0), "clientReadableVersion": ("obj", CLIENT_VERSION),
        "attrRequest": ("raw", 1), "needBasisVisualInfo": ("raw", True), "needSubitems": ("raw", False)})


def package(tasks):
    return Obj("LookinStaticAsyncUpdateTasksPackage", ["LookinStaticAsyncUpdateTasksPackage", "NSObject"],
               {"tasks": ("obj", tasks)})


# ---------- NSKeyedArchiver decode ----------
def unarchive(data):
    p = plistlib.loads(data)
    objs = p["$objects"]
    memo = {}

    def dec(u):
        if isinstance(u, UID):
            i = u.data
            if i == 0:
                return None
            if i in memo:
                return memo[i]
            o = objs[i]
            if isinstance(o, dict) and "$class" in o:
                cname = objs[o["$class"].data]["$classname"]
                if "NS.objects" in o and "NS.keys" in o:
                    r = {}
                    memo[i] = r
                    for k, v in zip(o["NS.keys"], o["NS.objects"]):
                        r[dec(k)] = dec(v)
                    return r
                if "NS.objects" in o:
                    r = []
                    memo[i] = r
                    r.extend(dec(x) for x in o["NS.objects"])
                    return r
                if "NS.string" in o:
                    return o["NS.string"]
                if "NS.bytes" in o:
                    return o["NS.bytes"]
                if "NS.time" in o:
                    return o["NS.time"]
                r = {"$c": cname}
                memo[i] = r
                for k, v in o.items():
                    if k != "$class":
                        r[k] = dec(v)
                return r
            return o
        if isinstance(u, list):
            return [dec(x) for x in u]
        return u

    return dec(p["$top"]["root"])


# ---------- Peertalk framing ----------
def recv_exact(s, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed after %d of %d bytes" % (len(buf), n))
        buf += chunk
    return bytes(buf)


def request(port, rtype, data=None, tag=7, timeout=20.0):
    """Send one request; collect response frames until currentDataCount sums to dataTotalCount."""
    payload = archive(attachment(data)) if data is not None else b""
    s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    s.sendall(struct.pack(">IIII", 1, rtype, tag, len(payload)) + payload)
    out, got = [], 0
    try:
        while True:
            _, ftype, _, size = struct.unpack(">IIII", recv_exact(s, 16))
            body = recv_exact(s, size) if size else b""
            if ftype != rtype:
                continue  # push frames from the server
            resp = unarchive(body)
            out.append(resp)
            total = resp.get("dataTotalCount") or 0
            got += resp.get("currentDataCount") or 0
            if total == 0 or got >= total:
                return out
    finally:
        s.close()


# ---------- commands ----------
def cls_of(o):
    return o["classChainList"][0] if o and o.get("classChainList") else None


def walk(items, depth=0):
    for it in items or []:
        yield depth, it
        yield from walk(it.get("subitems"), depth + 1)


def rect(s):
    v = [float(x) for x in re.findall(r"-?[\d.]+(?:e-?\d+)?", s or "")]
    return v if len(v) == 4 else [0.0, 0.0, 0.0, 0.0]


def window_frames(items):
    """Map id(item) -> window rect. Frames are parent-relative; subtract the parent's bounds origin (scroll offset)."""
    out = {}

    def go(items, ox, oy):
        for it in items or []:
            x, y, w, h = rect(it.get("frame"))
            bx, by, _, _ = rect(it.get("bounds"))
            out[id(it)] = (ox + x, oy + y, w, h)
            go(it.get("subitems"), ox + x - bx, oy + y - by)

    go(items, 0.0, 0.0)
    return out


def texts(detail):
    """String attributes from 203, minus font names."""
    vals = []
    for key in ("attributesGroupList", "customAttrGroupList"):
        for g in detail.get(key) or []:
            for sec in g.get("attrSections") or []:
                for a in sec.get("attributes") or []:
                    v, ident = a.get("value"), a.get("identifier") or ""
                    if isinstance(v, str) and v and not ident.endswith("_f_n"):
                        vals.append(v)
    return list(dict.fromkeys(vals))


def listening_ports():
    """{port: pid} for listeners in the Lookin range."""
    try:
        out = subprocess.run(["lsof", "-nP", "-iTCP:%d-%d" % (PORTS[0], PORTS[-1]), "-sTCP:LISTEN", "-Fpn"],
                             capture_output=True, text=True).stdout
    except OSError:
        return {}
    ports, pid = {}, None
    for line in out.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n") and ":" in line:
            ports[int(line.rsplit(":", 1)[1])] = pid
    return ports


# ---------- SWIFTUI_PRINT_TREE ----------
# With SIMCTL_CHILD_SWIFTUI_PRINT_TREE=1 and `simctl launch --console`, SwiftUI prints a display list on every
# render: "View 0x<hosting view address> at Time(...):" then an s-expression. Item frames nest relative to the
# hosting view; `effect` nodes may carry an affine transform. "Async view" lists have no address and are skipped.
@dataclass(frozen=True)
class SwiftUILeaf:
    """Text, image or shape drawn by SwiftUI, with its frame relative to the hosting view."""
    kind: str  # "text", "image" or "shape" (SF Symbols and drawn paths)
    text: str
    frame: tuple  # (x, y, w, h)


_HEADER = re.compile(r"(?m)^(View (0x[0-9a-fA-F]+)|Async view) at Time\(seconds: [^)]*\):\s*$")
_AFFINE = re.compile(r"affine\(__C\.CGAffineTransform\(a: ([-\d.e]+), b: ([-\d.e]+), c: ([-\d.e]+), d: ([-\d.e]+), "
                     r"tx: ([-\d.e]+), ty: ([-\d.e]+)\)\)")
_TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')


def _parse_sexpr(text):
    """First balanced s-expression in text as nested lists; strings keep their quotes."""
    stack, cur = [], None
    for tok in _TOKEN.findall(_AFFINE.sub(lambda m: "(affine %s)" % " ".join(m.groups()), text)):
        if tok == "(":
            stack.append([])
        elif tok == ")":
            if not stack:
                break
            cur = stack.pop()
            if not stack:
                return cur
            stack[-1].append(cur)
        elif stack:
            stack[-1].append(tok)
    return None


def _swift_string(tok):
    r"""Decode a Swift debug-description string literal ("..." with \\, \", \n, \u{...})."""
    body = tok[1:-1] if len(tok) >= 2 and tok[0] == tok[-1] == '"' else tok
    body = re.sub(r"\\u\{([0-9a-fA-F]+)\}", lambda m: chr(int(m.group(1), 16)), body)
    return re.sub(r'\\(.)', lambda m: {"n": "\n", "t": "\t", "r": "\r"}.get(m.group(1), m.group(1)), body)


def _num(tok):
    return float(tok.rstrip(";,"))


def _apply(m, x, y):
    a, b, c, d, tx, ty = m
    return a * x + c * y + tx, b * x + d * y + ty


def _compose(m, n):
    """m then n in local space: point -> m(n(point))."""
    a, b, c, d, tx, ty = m
    a2, b2, c2, d2, tx2, ty2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
            a * tx2 + c * ty2 + tx, b * tx2 + d * ty2 + ty)


def _leaves(node, m, out):
    if not isinstance(node, list) or not node:
        return
    head = node[0]
    if head == "item":
        frame = next((c for c in node if isinstance(c, list) and c[:1] == ["frame"]), None)
        if frame and isinstance(frame[1], list) and len(frame[1]) == 4:
            x, y, w, h = (_num(t) for t in frame[1])
            m = _compose(m, (1, 0, 0, 1, x, y))
            for c in node:
                if isinstance(c, list) and c[:1] in (["text"], ["image"], ["shape"]):
                    corners = [_apply(m, px, py) for px, py in ((0, 0), (w, 0), (0, h), (w, h))]
                    xs, ys = [p[0] for p in corners], [p[1] for p in corners]
                    label = _swift_string(c[1]) if c[0] == "text" and len(c) > 1 else ""
                    out.append(SwiftUILeaf(c[0], label, (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))))
    elif head == "effect":
        for c in node:
            if isinstance(c, list) and c[:1] == ["transform"] and len(c) > 1 and isinstance(c[1], list) and c[1][:1] == ["affine"]:
                m = _compose(m, tuple(float(v) for v in c[1][1:7]))
    for c in node[1:]:
        _leaves(c, m, out)


def read_print_tree(path):
    """{hosting view address: [SwiftUILeaf]} from the latest display list of each hosting view."""
    with open(path, errors="replace") as f:
        text = f.read()
    heads = list(_HEADER.finditer(text))
    latest = {}
    for i, h in enumerate(heads):
        if h.group(2):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
            latest[int(h.group(2), 16)] = text[h.end():end]
    out = {}
    for addr, body in latest.items():
        tree = _parse_sexpr(body)
        leaves = []
        if tree:
            _leaves(tree, (1, 0, 0, 1, 0, 0), leaves)
        out[addr] = leaves
    return out


def cmd_scan():
    found = 0
    for port, pid in sorted(listening_ports().items()):
        try:
            r = request(port, 201, {"needImages": False}, timeout=3)[0]
        except OSError:
            continue
        info = r.get("0") or {}
        found += 1
        print("port=%d pid=%s app=%s bundle=%s os=%s protocol=%s" % (
            port, pid, info.get("5"), info.get("appBundleIdentifier"), info.get("4"), r.get("lookinServerVersion")))
    return 0 if found else 2


def cmd_dump(port, raw_path, print_tree_path=None):
    t0 = time.time()
    hier = request(port, 202, {"clientVersion": CLIENT_VERSION})[0]
    if hier.get("error") or not isinstance(hier.get("0"), dict):
        print("error: hierarchy request failed: %s" % (hier.get("error"),), file=sys.stderr)
        return 3
    items = hier["0"].get("1") or []
    nodes = list(walk(items))
    frames = window_frames(items)
    oids = [it["layerObject"]["oid"] for _, it in nodes if it.get("layerObject")]
    resps = request(port, 203, [package([task(o) for o in oids])], timeout=60)
    details = {d.get("displayItemOid"): d for r in resps for d in (r.get("0") or []) if not d.get("failureCode")}
    swiftui = read_print_tree(print_tree_path) if print_tree_path else {}
    joined = 0
    for depth, it in nodes:
        x, y, w, h = frames[id(it)]
        flags = []
        if it.get("hidden"):
            flags.append("hidden")
        if (it.get("alpha") if it.get("alpha") is not None else 1) < 0.01:
            flags.append("alpha=0")
        actions = []
        for e in it.get("eventHandlers") or []:
            try:
                kind = HandlerType(e.get("handlerType", 0))
            except ValueError:
                continue
            match kind:
                case HandlerType.TARGET_ACTION | HandlerType.GESTURE:
                    actions += ["%s->%s" % (e.get("eventName"), ta.get("second")) for ta in e.get("targetActions") or []]
                case _:
                    pass
        layer = it.get("layerObject") or {}
        txt = texts(details.get(layer.get("oid"), {}))
        line = "%s%s (%g,%g %gx%g)" % ("  " * depth, cls_of(it.get("viewObject")) or cls_of(layer), round(x, 2), round(y, 2), round(w, 2), round(h, 2))
        if flags:
            line += " " + " ".join(flags)
        if txt:
            line += " text=" + json.dumps(txt, ensure_ascii=False)
        if actions:
            line += " actions=" + ",".join(actions)
        addr = (it.get("viewObject") or {}).get("memoryAddress")
        leaves = swiftui.get(int(addr, 16)) if addr else None
        if leaves:
            joined += 1
            line += " swiftui=[%s]" % ", ".join(
                "%s (%g,%g %gx%g)" % (json.dumps(lf.text, ensure_ascii=False) if lf.kind == "text" else "<%s>" % lf.kind,
                                      round(x + lf.frame[0], 2), round(y + lf.frame[1], 2),
                                      round(lf.frame[2], 2), round(lf.frame[3], 2))
                for lf in leaves)
        print(line)
    print("# %d views, %.2fs, protocol %s" % (len(nodes), time.time() - t0, hier.get("lookinServerVersion")), file=sys.stderr)
    if print_tree_path:
        with_content = sum(1 for v in swiftui.values() if v)
        print("# print tree: %d hosting views with text, images or shapes, %d joined to views on screen" % (with_content, joined),
              file=sys.stderr)
    if raw_path:
        with open(raw_path, "w") as f:
            json.dump({"hierarchy": hier, "details": list(details.values())}, f, default=str)
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] not in ("scan", "dump", "ping"):
        print(__doc__, file=sys.stderr)
        return 64
    if argv[1] == "scan":
        return cmd_scan()
    if "--pid" in argv:
        pid = int(argv[argv.index("--pid") + 1])
        port = next((p for p, q in listening_ports().items() if q == pid), None)
        if port is None:
            print("error: no Lookin server for pid %d" % pid, file=sys.stderr)
            return 2
    else:
        port = int(argv[2])
    try:
        if argv[1] == "ping":
            r = request(port, 200, timeout=3)[0]
            print("port=%d protocol=%s background=%s" % (port, r.get("lookinServerVersion"), r.get("appIsInBackground")))
            return 0
        raw = argv[argv.index("--raw") + 1] if "--raw" in argv else None
        tree = argv[argv.index("--print-tree") + 1] if "--print-tree" in argv else None
        return cmd_dump(port, raw, tree)
    except OSError as e:
        print("error: no server on port %d: %s" % (port, e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
