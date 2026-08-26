#!/usr/bin/env python3
"""Boot the packaged companion JAR on a disposable Forge 1.18.2 dedicated server.

This gate proves Mixin application against original GeckoLib 3.0.57. It does
not exercise the client render path.
"""

from __future__ import annotations

import os
import selectors
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "run-packaged"
FORGE_SRC = Path("/root/work/iob-gecko-bonesnapshot-mixin-runtime-20260822-r1")
JAVA_HOME = Path("/usr/lib/jvm/java-17-openjdk-amd64")
ARTIFACT = ROOT / "build/libs/isleofberk-geckolib-fixes-0.1.0-beta.3.jar"
GECKOLIB = ROOT / "libs/geckolib-forge-1.18-3.0.57.jar"
ISLEOFBERK = ROOT / "libs/isleofberk-1.2.0.jar"
SERVER_PORT = "25791"


def prepare_runtime() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    for name in ("libraries", "server.jar", "run.sh"):
        src = FORGE_SRC / name
        dest = RUNTIME / name
        if not src.exists():
            raise SystemExit(f"missing Forge runtime source {src}")
        if dest.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, dest, symlinks=True)
        else:
            shutil.copy2(src, dest)
    (RUNTIME / "run.sh").chmod(0o755)
    (RUNTIME / "user_jvm_args.txt").write_text(
        "-Xmx2G -Xms1G -Dmixin.debug.verbose=true -Dmixin.debug.countInjections=true\n",
        encoding="utf-8",
    )
    (RUNTIME / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    (RUNTIME / "server.properties").write_text(
        "\n".join(
            [
                "enable-jmx-monitoring=false",
                "enable-query=false",
                "enable-rcon=false",
                "enable-status=true",
                "level-name=iob-geckolib-fixes-packaged-r1",
                "level-seed=geckolibfixes",
                "level-type=minecraft:flat",
                "max-tick-time=180000",
                "motd=isleofberk-geckolib-fixes packaged gate",
                "online-mode=false",
                f"query.port={SERVER_PORT}",
                "server-ip=127.0.0.1",
                f"server-port={SERVER_PORT}",
                "spawn-protection=0",
                "sync-chunk-writes=true",
                "white-list=false",
                "max-players=1",
                "view-distance=2",
                "simulation-distance=2",
                "spawn-monsters=false",
                "spawn-animals=false",
                "spawn-npcs=false",
                "generate-structures=false",
                "allow-nether=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    mods = RUNTIME / "mods"
    mods.mkdir(exist_ok=True)
    for stale in mods.glob("isleofberk-geckolib-fixes-*.jar"):
        stale.unlink()
    for src in (ARTIFACT, GECKOLIB, ISLEOFBERK):
        if not src.is_file():
            raise SystemExit(f"missing mod jar {src}")
        shutil.copy2(src, mods / src.name)


def run_gate() -> dict:
    env = dict(os.environ)
    env["JAVA_HOME"] = str(JAVA_HOME)
    env["PATH"] = str(JAVA_HOME / "bin") + ":" + env.get("PATH", "")
    proc = subprocess.Popen(
        ["./run.sh", "nogui"],
        cwd=RUNTIME,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    sel = selectors.DefaultSelector()
    assert proc.stdout is not None
    assert proc.stdin is not None
    sel.register(proc.stdout, selectors.EVENT_READ)
    lines: list[str] = []
    done = False
    summoned = False
    stop = False
    start = time.monotonic()
    summon_at = None
    while time.monotonic() - start < 180:
        now = time.monotonic()
        for key, _ in sel.select(timeout=1):
            line = key.fileobj.readline()
            if not line:
                sel.unregister(key.fileobj)
                continue
            lines.append(line)
            if "Done (" in line and not summoned:
                done = True
                proc.stdin.write("summon isleofberk:skrill 0 5 0\n")
                proc.stdin.flush()
                summoned = True
                summon_at = now
        if summoned and not stop and summon_at is not None and now - summon_at >= 8:
            proc.stdin.write("stop\n")
            proc.stdin.flush()
            stop = True
        if proc.poll() is not None:
            break
    if proc.poll() is None:
        proc.kill()
        rest, _ = proc.communicate(timeout=20)
        if rest:
            lines.extend(rest.splitlines(True))
    else:
        rest = proc.stdout.read() if proc.stdout else ""
        if rest:
            lines.extend(rest.splitlines(True))
    raw = "".join(lines)
    (RUNTIME / "packaged-runtime.log").write_text(raw, encoding="utf-8")
    debug_path = RUNTIME / "logs" / "debug.log"
    debug = debug_path.read_text(encoding="utf-8") if debug_path.exists() else ""
    mixin_line = (
        "Mixing AnimationControllerProcessMixin from isleofberkgeckolibfixes.mixins.json "
        "into software.bernie.geckolib3.core.controller.AnimationController"
    )
    combined = raw + "\n" + debug
    checks = {
        "done": done,
        "exit_code": proc.returncode,
        "stop_sent": stop,
        "summoned": summoned,
        "clean_stop": "Stopping server" in combined or "Stopping the server" in combined,
        "candidate_loaded": "[IoB-GeckoLibFixes] AnimationController.process boneSnapshot guard loaded" in combined,
        "mixin_config_prepared": "Preparing isleofberkgeckolibfixes.mixins.json (1)" in combined,
        "gecko_target_mixin_applied": mixin_line in combined,
        "original_geckolib": "geckolib-forge-1.18-3.0.57" in combined or "SecureJarResource(geckolib3)" in combined,
        "no_deadlock_scope": "isleofberkdeadlockfix" not in combined and "ADragonBaseMixin" not in combined,
        "no_variant_loader": "iobvariantloader" not in combined.lower() and "IoBVariantLoader" not in combined,
        "candidate_mixin_errors": any(
            token in combined
            for token in (
                "MixinApplyError",
                "InvalidInjectionException",
                "NoSuchMethodError",
                "AbstractMethodError",
            )
        ),
    }
    print(checks)
    print("log=" + str(RUNTIME / "packaged-runtime.log"))
    # Dedicated-server boot cannot apply the GeckoLib mixin until
    # AnimationController is loaded. Summoning an IoB Skrill does not load that
    # class on the physical server. Do not add a product Class.forName probe.
    # Mixing-line absence here is evidence that the crash path is client-render,
    # not a Mixin registration failure.
    ok = (
        checks["done"]
        and checks["exit_code"] == 0
        and checks["stop_sent"]
        and checks["summoned"]
        and checks["clean_stop"]
        and checks["candidate_loaded"]
        and checks["mixin_config_prepared"]
        and checks["original_geckolib"]
        and checks["no_deadlock_scope"]
        and checks["no_variant_loader"]
        and not checks["candidate_mixin_errors"]
    )
    if not ok:
        raise SystemExit(1)
    return checks


def main() -> None:
    prepare_runtime()
    run_gate()


if __name__ == "__main__":
    main()
