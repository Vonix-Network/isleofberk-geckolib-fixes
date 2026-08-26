# Validation limits for v0.1.0-beta.2

`v0.1.0-beta.2` is a testable compatibility candidate. Treat every claim below
as a gate, not as a production-crash-fixed statement.

## Deterministic checks (always part of `./gradlew build`)

`scripts/verify-candidate.py` is wired into Gradle `check`.

Source phase:

- Package namespace is `network.vonix.isleofberkgeckolibfixes`.
- Deadlock Fix identifiers are absent (`isleofberkdeadlockfix`,
  `ADragonBaseMixin`, `AltFollowGoalMixin`, `Worker-Main`, `isWaterBelow`).
- Variant Loader identifiers are absent (`iobvariantloader`,
  `AltFollowGoal`).
- Temporary feasibility probe `Class.forName` is absent.
- Mixin source contains the exact `process` descriptor and
  `saveSnapshotsForAnimation` INVOKE target.

Artifact phase (reobfuscated primary JAR):

- File name is `isleofberk-geckolib-fixes-0.1.0-beta.2.jar`.
- Required entries listed in `src/test/fixtures/required-archive-entries.txt`
  are present.
- Forbidden archive prefixes listed in
  `src/test/fixtures/forbidden-archive-prefixes.txt` are absent (no bundled
  GeckoLib, Isle of Berk, Variant Loader, or Deadlock Fix classes).
- `META-INF/mods.toml` has `modId="isleofberkgeckolibfixes"`, version
  `0.1.0-beta.2`, GeckoLib range `[3.0.57,3.0.58)`, no `iobvariantloader`
  dependency, and `displayTest="IGNORE_ALL_VERSION"`.
- Manifest `MixinConfigs` equals `isleofberkgeckolibfixes.mixins.json`.
- Mixin JSON lists only `AnimationControllerProcessMixin` and points at
  `isleofberkgeckolibfixes.refmap.json`.
- Refmap file exists. Empty `mappings`/`data` is accepted for this
  `remap = false` GeckoLib hook; a missing file is not.

## Beta.2 correction

Beta.1 only copied `IBone#getInitialSnapshot()` and silently skipped the
repair when that snapshot was null. Beta.2 copies a fresh snapshot from
`IBone#saveSnapshot()`, which constructs it from the live bone state. This
directly covers the `UDivjgc` failure mode while preserving the same narrow
GeckoLib 3.0.57 hook.

## Packaged Forge runtime (optional, dedicated server)

A disposable dedicated-server boot can prove:

- The **packaged** candidate JAR loads next to original
  `geckolib-forge-1.18-3.0.57` and Isle of Berk `1.2.0`.
- Mixin config `isleofberkgeckolibfixes.mixins.json` is registered and
  prepared with exactly one mixin.
- The server reaches `Done (`, can summon `isleofberk:skrill`, and stops
  cleanly.
- Deadlock Fix / Variant Loader are absent from the runtime.

That gate does **not** apply `AnimationControllerProcessMixin` unless
GeckoLib `AnimationController` is actually loaded. Dedicated-server Skrill
construction does not load that class. The feasibility prototype only saw
`Mixing ... into AnimationController` because it used a temporary
`Class.forName` probe, which is **not** in this product.

Absence of the Mixing line on a dedicated server after a Skrill summon is
therefore evidence that the crash path is client-render, not a missing Mixin
config.

## Client render-path gate (not claimed by this candidate unless run)

The original crash is a **client** NPE while rendering GeckoLib entities
(reported on Isle of Berk Skrill / Monstrous Nightmare). Fixing it requires a
physical client (or a headless client that actually runs the render path) with:

- Minecraft 1.18.2
- Forge 40.3.12
- original GeckoLib 3.0.57
- Isle of Berk 1.2.0
- this companion jar
- a world that loads and renders the affected dragons

This environment has no display (`DISPLAY` unset). Do not read a dedicated
server boot, a Mixin apply log, or a successful Gradle compile as proof that
the client render crash is gone.

## Out of scope

- Live Pterodactyl / production server restarts.
- CurseForge upload or GitHub prerelease publication by the implementer.
- Bundling or replacing GeckoLib-Refined, GeckoLib, or Isle of Berk.
- Deadlock Fix worldgen behaviour and Variant Loader follow-goal behaviour.
