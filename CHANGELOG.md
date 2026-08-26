# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

`v0.1.0-beta.2` is a testable compatibility candidate. It is not a final
release and does not replace GeckoLib or Isle of Berk.

## [Unreleased]

## [0.1.0-beta.2] - 2026-08-26

### Fixed
- Seed missing transition snapshots with `IBone.saveSnapshot()` instead of
  skipping the repair when `IBone.getInitialSnapshot()` is null. This covers
  the residual failure shown by the `UDivjgc` crash report.

## [0.1.0-beta.1] - 2026-08-22

### Added
- Standalone Forge 1.18.2 companion `isleofberkgeckolibfixes` that ports
  GeckoLib-Refined's `AnimationController.process` `boneSnapshot` null-snapshot
  guard through a Mixin.
- Exact-descriptor inject into
  `software.bernie.geckolib3.core.controller.AnimationController.process` after
  `saveSnapshotsForAnimation`, seeding a missing snapshot from the matched
  bone before the original transition loop dereferences it.
- Narrow GeckoLib dependency range `[3.0.57,3.0.58)` and Isle of Berk range
  `[1.2.0,1.3)`, tested against Forge `1.18.2-40.3.12` / Java 17.
- Client-required, dedicated-server-optional install contract with
  `displayTest="IGNORE_ALL_VERSION"`.
- Deterministic source and packaged-JAR checks that require the Mixin
  config/refmap/manifest relationship and reject Deadlock Fix, Variant Loader,
  and bundled upstream JARs.

### Scope explicitly not included
- No `ADragonBaseMixin`, worldgen deadlock guard, or Variant Loader follow-goal
  code.
- No GeckoLib or Isle of Berk classes, resources, or JARs inside the artifact.
- No performance tuning and no claim of broad GeckoLib 3.0.x compatibility.

[Unreleased]: https://github.com/Vonix-Network/isleofberk-geckolib-fixes/compare/v0.1.0-beta.1...HEAD
[0.1.0-beta.1]: https://github.com/Vonix-Network/isleofberk-geckolib-fixes/releases/tag/v0.1.0-beta.1
