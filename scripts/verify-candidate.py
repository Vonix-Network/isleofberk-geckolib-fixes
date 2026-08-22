#!/usr/bin/env python3
"""Deterministic source and packaged-JAR checks for isleofberk-geckolib-fixes."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "main"
FIXTURES = ROOT / "src" / "test" / "fixtures"
EXPECTED_JAR_NAME = "isleofberk-geckolib-fixes-0.1.0-beta.1.jar"
MOD_ID = "isleofberkgeckolibfixes"
MIXIN_JSON = "isleofberkgeckolibfixes.mixins.json"
REFMAP = "isleofberkgeckolibfixes.refmap.json"
MIXIN_CLASS = "AnimationControllerProcessMixin"
PROCESS_DESCRIPTOR = (
    "process(DLsoftware/bernie/geckolib3/core/event/predicate/AnimationEvent;"
    "Ljava/util/List;Ljava/util/Map;Lsoftware/bernie/geckolib3/core/molang/MolangParser;Z)V"
)
SAVE_SNAPSHOTS_TARGET = (
    "Lsoftware/bernie/geckolib3/core/controller/AnimationController;"
    "saveSnapshotsForAnimation(Lsoftware/bernie/geckolib3/core/builder/Animation;Ljava/util/Map;)V"
)

FORBIDDEN_SOURCE_NEEDLES = [
    "isleofberkdeadlockfix",
    "ADragonBaseMixin",
    "AltFollowGoalMixin",
    "ADragonBase",
    "isWaterBelow",
    "Worker-Main",
    "iobvariantloader",
    "AltFollowGoal",
    "Class.forName",
    "nordmods",
    "com.GACMD",
]


class CheckError(Exception):
    pass


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in SRC_ROOT.rglob("*"):
        if path.is_file():
            files.append(path)
    return files


def verify_sources() -> list[str]:
    notes: list[str] = []
    java_files = list((SRC_ROOT / "java").rglob("*.java"))
    if not java_files:
        raise CheckError("no Java sources under src/main/java")

    for path in java_files:
        rel = path.relative_to(ROOT).as_posix()
        if "isleofberkdeadlockfix" in rel:
            raise CheckError(f"deadlock-fix package path still present: {rel}")
        if "/network/vonix/isleofberkgeckolibfixes/" not in f"/{rel}":
            raise CheckError(f"unexpected Java package path: {rel}")
        text = path.read_text(encoding="utf-8")
        for needle in FORBIDDEN_SOURCE_NEEDLES:
            if needle in text:
                raise CheckError(f"{rel} contains forbidden identifier {needle!r}")

    mixin = SRC_ROOT / "java/network/vonix/isleofberkgeckolibfixes/mixin/AnimationControllerProcessMixin.java"
    if not mixin.is_file():
        raise CheckError(f"missing mixin source {mixin}")
    mixin_text = mixin.read_text(encoding="utf-8")
    if PROCESS_DESCRIPTOR not in mixin_text:
        raise CheckError("mixin is missing the exact process descriptor")
    if SAVE_SNAPSHOTS_TARGET not in mixin_text:
        raise CheckError("mixin is missing the saveSnapshotsForAnimation INVOKE target")
    if "@Pseudo" in mixin_text:
        raise CheckError("mixin uses @Pseudo; compile-classpath GeckoLib target must be exact")
    if "remap = false" not in mixin_text:
        raise CheckError("mixin is missing remap = false")
    if "getInitialSnapshot" not in mixin_text:
        raise CheckError("mixin does not seed from getInitialSnapshot")
    notes.append("source namespace, mixin descriptor, and forbidden-scope scan passed")

    mixin_json_path = SRC_ROOT / "resources" / MIXIN_JSON
    mixin_json = json.loads(mixin_json_path.read_text(encoding="utf-8"))
    if mixin_json.get("package") != "network.vonix.isleofberkgeckolibfixes.mixin":
        raise CheckError("mixin JSON package mismatch")
    if mixin_json.get("refmap") != REFMAP:
        raise CheckError("mixin JSON refmap mismatch")
    if mixin_json.get("mixins") != [MIXIN_CLASS]:
        raise CheckError(f"mixin JSON mixins must be exactly [{MIXIN_CLASS}]")
    if mixin_json.get("client") not in ([], None):
        raise CheckError("mixin JSON client list must be empty; common mixins list is the contract")
    if mixin_json.get("required") is not True:
        raise CheckError("mixin JSON must be required")
    notes.append("mixin JSON contract passed")

    mods_toml = (SRC_ROOT / "resources/META-INF/mods.toml").read_text(encoding="utf-8")
    required_toml = [
        'modId="isleofberkgeckolibfixes"',
        'displayName="Isle of Berk GeckoLib Fixes"',
        'displayTest="IGNORE_ALL_VERSION"',
        'modId="geckolib3"',
        'versionRange="[3.0.57,3.0.58)"',
        'modId="isleofberk"',
        'versionRange="[1.2.0,1.3)"',
    ]
    for token in required_toml:
        if token not in mods_toml:
            raise CheckError(f"mods.toml missing {token}")
    for needle in ("iobvariantloader", "isleofberkdeadlockfix", "ADragonBase"):
        if needle in mods_toml:
            raise CheckError(f"mods.toml contains forbidden token {needle!r}")
    notes.append("mods.toml contract passed")
    return notes


def zip_entries(jar: Path) -> list[str]:
    with zipfile.ZipFile(jar) as zf:
        return zf.namelist()


def read_zip_text(jar: Path, name: str) -> str:
    with zipfile.ZipFile(jar) as zf:
        try:
            return zf.read(name).decode("utf-8")
        except KeyError as exc:
            raise CheckError(f"JAR missing {name}") from exc


def verify_artifact(jar: Path) -> list[str]:
    notes: list[str] = []
    if not jar.is_file():
        raise CheckError(f"artifact not found: {jar}")
    if jar.name != EXPECTED_JAR_NAME:
        raise CheckError(f"artifact name {jar.name} != {EXPECTED_JAR_NAME}")

    entries = zip_entries(jar)
    required = read_lines(FIXTURES / "required-archive-entries.txt")
    missing = [name for name in required if name not in entries]
    if missing:
        raise CheckError(f"JAR missing required entries: {missing}")

    forbidden = read_lines(FIXTURES / "forbidden-archive-prefixes.txt")
    hits = []
    for entry in entries:
        for prefix in forbidden:
            if prefix in entry:
                hits.append(entry)
                break
    if hits:
        raise CheckError(f"JAR contains forbidden entries: {hits}")

    # Nested JARs or obvious third-party class dumps.
    nested = [e for e in entries if e.endswith(".jar")]
    if nested:
        raise CheckError(f"JAR embeds nested jars: {nested}")
    notes.append(f"archive inventory ok ({len(entries)} entries)")

    manifest = read_zip_text(jar, "META-INF/MANIFEST.MF")
    if "MixinConfigs: isleofberkgeckolibfixes.mixins.json" not in manifest.replace("\r\n", "\n").replace("\n ", ""):
        # Manifest wrapping can split MixinConfigs; compare folded form.
        folded = re.sub(r"\r?\n[ \t]", "", manifest)
        if "MixinConfigs: isleofberkgeckolibfixes.mixins.json" not in folded:
            raise CheckError(f"manifest MixinConfigs mismatch:\n{manifest}")
    if "Implementation-Version: 0.1.0-beta.1" not in manifest:
        raise CheckError("manifest Implementation-Version is not 0.1.0-beta.1")
    notes.append("manifest contract passed")

    mods_toml = read_zip_text(jar, "META-INF/mods.toml")
    if 'modId="isleofberkgeckolibfixes"' not in mods_toml:
        raise CheckError("packaged mods.toml has wrong modId")
    if "0.1.0-beta.1" not in mods_toml:
        raise CheckError("packaged mods.toml is missing expanded version 0.1.0-beta.1")
    if "${version}" in mods_toml:
        raise CheckError("packaged mods.toml still contains unexpanded ${version}")
    if 'versionRange="[3.0.57,3.0.58)"' not in mods_toml:
        raise CheckError("packaged mods.toml geckolib range mismatch")
    if "iobvariantloader" in mods_toml or "isleofberkdeadlockfix" in mods_toml:
        raise CheckError("packaged mods.toml contains deadlock/variant scope")
    notes.append("packaged mods.toml contract passed")

    mixin_json = json.loads(read_zip_text(jar, MIXIN_JSON))
    if mixin_json.get("mixins") != [MIXIN_CLASS] or mixin_json.get("refmap") != REFMAP:
        raise CheckError(f"packaged mixin JSON mismatch: {mixin_json}")
    notes.append("packaged mixin JSON contract passed")

    refmap_raw = read_zip_text(jar, REFMAP)
    try:
        refmap = json.loads(refmap_raw)
    except json.JSONDecodeError as exc:
        raise CheckError(f"refmap is not JSON: {exc}") from exc
    if not isinstance(refmap, dict) or "mappings" not in refmap or "data" not in refmap:
        raise CheckError(f"refmap missing mappings/data keys: {refmap_raw!r}")
    # remap=false GeckoLib targets are expected to produce empty mappings.
    notes.append(f"refmap present (mappings={refmap.get('mappings')!r})")

    class_names = [e for e in entries if e.endswith(".class")]
    unexpected = [
        e
        for e in class_names
        if not e.startswith("network/vonix/isleofberkgeckolibfixes/")
    ]
    if unexpected:
        raise CheckError(f"unexpected class files: {unexpected}")
    notes.append("class namespace contract passed")
    return notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("sources", "artifact", "all"), default="all")
    parser.add_argument("--jar", type=Path, default=ROOT / "build/libs" / EXPECTED_JAR_NAME)
    args = parser.parse_args()
    try:
        notes: list[str] = []
        if args.phase in ("sources", "all"):
            notes.extend(verify_sources())
        if args.phase in ("artifact", "all"):
            notes.extend(verify_artifact(args.jar))
        print("OK: " + "; ".join(notes))
        return 0
    except CheckError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
