# Isle of Berk GeckoLib Fixes

A tiny Forge 1.18.2 compatibility companion that ports
[GeckoLib-Refined](https://github.com/Vonix-Network)'s production
`boneSnapshot` null-snapshot guard onto original GeckoLib `3.0.57` through a
Mixin.

`v0.1.0-beta.1` is a **testable compatibility candidate**. It is **not** a
final release. It does **not** replace GeckoLib, does **not** replace Isle of
Berk, and does **not** replace Isle of Berk Deadlock Fix.

> Isle of Berk itself is officially discontinued. This companion is for
> clients still running the final `isleofberk-1.2.0` jar with original
> `geckolib-forge-1.18-3.0.57` on Minecraft 1.18.2.

## What this candidate does

GeckoLib 3.0.57 `AnimationController.process` can dereference a missing
`boneSnapshot` during an animation transition. Upstream guarded that with
`assert boneSnapshot != null`, which is compiled out of production JVMs
(assertions disabled). The next field read then crashes the **client render
path**:

```
java.lang.NullPointerException: Cannot read field "rotationValueX"
  because "boneSnapshot" is null
  at software.bernie.geckolib3.core.controller.AnimationController.process
```

GeckoLib-Refined fixed this in-tree by lazy-initialising the snapshot from the
matched bone's `getInitialSnapshot()` and caching it. This companion carries
the same behaviour into original GeckoLib 3.0.57:

1. Target
   `software.bernie.geckolib3.core.controller.AnimationController.process`
   with the exact 3.0.57 descriptor.
2. Inject immediately after `saveSnapshotsForAnimation`.
3. For each bone on the current animation whose snapshot is still missing,
   copy the live model's initial snapshot into `boneSnapshots` before the
   original transition loop reads `rotationValueX` / position / scale.

This is the same injection point used by the prior feasibility prototype. The
prototype's temporary `Class.forName` probe, Deadlock Fix mixins, and Variant
Loader mixins are **not** part of this product.

## Side / install contract

| Side | Required? | Why |
|---|---|---|
| **Physical client** (including singleplayer and LAN hosts) | **Yes** | `GeoEntityRenderer` calls `AnimationController.process` while rendering Isle of Berk dragons. The NPE is a client crash. |
| **Dedicated server** | **Optional** | Dedicated servers do not run the GeckoLib entity renderer. Installing this companion on the server does not fix a client that is missing it. |

`mods.toml` uses `displayTest="IGNORE_ALL_VERSION"` so a client with this
companion can join a server that does not have it, and a server that does have
it will not reject a client that does not. The Mixin is registered in the
common `mixins` list (not `client` only) because `AnimationController` is a
GeckoLib core class present on both physical sides; that does **not** make
dedicated-server installation mandatory.

**Both-sides installation is not required.** Put the jar on every client that
renders Isle of Berk entities. Server install is extra, not a substitute.

## Exact tested versions

| Component | Tested version | Declared range |
|---|---|---|
| Minecraft | 1.18.2 | `[1.18.2,1.19)` |
| Forge | 40.3.12 | `[40,41)` |
| Java | 17 | toolchain 17 |
| GeckoLib | `geckolib-forge-1.18-3.0.57` (original, not Refined) | `[3.0.57,3.0.58)` |
| Isle of Berk | `isleofberk-1.2.0` | `[1.2.0,1.3)` |

The Mixin is bytecode-specific to GeckoLib 3.0.57 `process`. This candidate
does **not** claim GeckoLib 3.0.x, 3.1, Fabric, Quilt, or later Minecraft
versions. It is **not** tested with GeckoLib-Refined (Refined already contains
the in-tree guard). Do not install this companion as a general GeckoLib
compatibility pack.

This companion is **independent of** Isle of Berk Deadlock Fix and IoB Variant
Loader. Keep Deadlock Fix if you still need the worldgen / follow-goal guards.
This jar does not provide them.

## Installation

1. Build or obtain `isleofberk-geckolib-fixes-0.1.0-beta.1.jar`.
2. Keep original `geckolib-forge-1.18-3.0.57.jar` and `isleofberk-1.2.0.jar`
   installed. Do **not** remove them.
3. Drop this companion into the **client** `mods/` folder. Repeat for every
   player client. Dedicated-server `mods/` is optional.
4. Restart the client.

Expected constructor log line:

```
[network.vonix.isleofberkgeckolibfixes.IsleOfBerkGeckoLibFixes/]:
  [IoB-GeckoLibFixes] AnimationController.process boneSnapshot guard loaded
  (v0.1.0-beta.1 compatibility candidate). This companion does not replace
  GeckoLib or Isle of Berk.
```

Expected Mixin apply line in client `logs/debug.log` once GeckoLib loads
`AnimationController` (entity render). A dedicated server may never load that
class, so this line can be absent there even when the companion is installed:

```
Mixing AnimationControllerProcessMixin from isleofberkgeckolibfixes.mixins.json
into software.bernie.geckolib3.core.controller.AnimationController
```

## Removal / rollback

1. Stop the client (and the dedicated server if you installed it there).
2. Delete `isleofberk-geckolib-fixes-0.1.0-beta.1.jar` from `mods/`.
3. Leave GeckoLib 3.0.57 and Isle of Berk 1.2.0 in place.
4. Restart.

No world data, config files, or other mods are rewritten by this companion.
Removing the jar returns GeckoLib to its original `assert`-only behaviour.

## Building

Requires JDK 17 and internet access for ForgeGradle's first resolution.

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
./gradlew clean build --no-daemon
# Output: build/libs/isleofberk-geckolib-fixes-0.1.0-beta.1.jar
```

`libs/` is for local compile-only / run-only dependency JARs. It is gitignored
and must never be committed or packaged.

`build` also runs `scripts/verify-candidate.py`, which checks the Mixin JSON,
mods.toml, manifest, refmap, and archive inventory.

## Validation limits

This beta candidate is **not** a claim that the Isle of Berk dragon-render
crash is fixed in production play.

Known gates for `v0.1.0-beta.1`:

- Java 17 ForgeGradle compile and reobfuscation of this companion.
- Packaged-JAR metadata / Mixin / refmap / forbidden-scope inspection.
- Optional dedicated-server boot of the **packaged** jar against original
  GeckoLib 3.0.57, used to prove the companion loads, the Mixin config is
  prepared, and the server can summon an Isle of Berk Skrill. Dedicated-server
  boot does not load `AnimationController`, so it cannot prove the bytecode
  hook applied.

Not exercised by this candidate unless a later report says otherwise:

- Minecraft client render of Skrill / Monstrous Nightmare / other IoB dragons.
- Multiplayer clients connecting through a production proxy.
- GeckoLib versions other than original 3.0.57.

See [docs/VALIDATION.md](docs/VALIDATION.md) and
[docs/REMAPPING.md](docs/REMAPPING.md).

## Credits

- GeckoLib by Gecko, Eliot, AzureDoom, Chappie, DerToaster (MIT).
- Isle of Berk by the GACMD team (Ghanou Craft, Apprentice Necromancer,
  TooTHleZZ & Arsian).
- In-tree `boneSnapshot` lazy-init behaviour from GeckoLib-Refined
  `1.18.2-3.0.57+refined.1` (`[OPTIMIZED]` `AnimationController.process`
  guard).
- Companion authored by Vonix Network.

## License

MIT — see [LICENSE](LICENSE).
