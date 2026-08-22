# Production Mixin / refmap remapping contract

This companion targets a **third-party named class**, not an obfuscated
Minecraft class. The production contract is inspectable in the packaged JAR.

## What is remapped, and what is not

| Name | Obfuscated in production? | Mixin `remap` |
|---|---|---|
| `net.minecraft.*` members (not used by this Mixin) | Yes (SRG in the Forge 1.18.2 runtime) | would be `true` |
| `software.bernie.geckolib3.core.controller.AnimationController` | No. GeckoLib ships named bytecode | **`false`** |
| `saveSnapshotsForAnimation(Animation, Map)` | No. GeckoLib private method, original name | **`false`** |
| `process(double, AnimationEvent, List, Map, MolangParser, boolean)` | No. GeckoLib public method, original name | **`false`** |

ForgeGradle still uses official Mojang mappings for the Minecraft toolchain
(`mappings channel: 'official', version: '1.18.2'`). That mapping set is
**not** applied to GeckoLib 3.0.57 method names.

## Exact production hook

Mixin class: `network.vonix.isleofberkgeckolibfixes.mixin.AnimationControllerProcessMixin`

Target class: `software.bernie.geckolib3.core.controller.AnimationController`

Method descriptor:

```
process(DLsoftware/bernie/geckolib3/core/event/predicate/AnimationEvent;Ljava/util/List;Ljava/util/Map;Lsoftware/bernie/geckolib3/core/molang/MolangParser;Z)V
```

Injection:

```
INVOKE Lsoftware/bernie/geckolib3/core/controller/AnimationController;saveSnapshotsForAnimation(Lsoftware/bernie/geckolib3/core/builder/Animation;Ljava/util/Map;)V
shift = AFTER
require = 1
```

`@Pseudo` is intentionally **absent**. GeckoLib 3.0.57 is a compile-only
dependency, so Mixin annotation processing must fail the candidate build if
the class, descriptor, or INVOKE target is missing.

## How Forge finds the Mixin

1. JAR manifest `MixinConfigs: isleofberkgeckolibfixes.mixins.json`
2. `isleofberkgeckolibfixes.mixins.json` lists
   `AnimationControllerProcessMixin` under `mixins` (common / both physical
   sides) and names `refmap: isleofberkgeckolibfixes.refmap.json`
3. `isleofberkgeckolibfixes.refmap.json` is packaged next to the Mixin JSON

Because every target in this Mixin is already a named GeckoLib binary name,
the generated refmap is expected to contain **empty** `mappings` / `data`
objects:

```json
{ "mappings": {}, "data": {} }
```

That empty refmap is the production contract for a `remap = false` GeckoLib
3.0.57 hook, **not** a missing-refmap failure. The file must still exist in
the JAR so Mixin can load the config.

Gradle `runClient` / `runServer` still set:

```
mixin.env.remapRefMap=true
mixin.env.refMapRemappingFile=<project>/build/createSrgToMcp/output.srg
```

Those properties exist so any future Minecraft-named inject would remap
correctly in the development environment. They do not rewrite GeckoLib names.

## Dedicated-server vs client apply

`AnimationController` is loaded on dedicated servers (GeckoLib core). Mixin
debug logs on a dedicated server should still show:

```
Mixing AnimationControllerProcessMixin from isleofberkgeckolibfixes.mixins.json
into software.bernie.geckolib3.core.controller.AnimationController
```

That log line proves the bytecode hook applied. It does **not** prove the
client render NPE is gone. See [VALIDATION.md](VALIDATION.md).
