package network.vonix.isleofberkgeckolibfixes.mixin;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.tuple.Pair;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import software.bernie.geckolib3.core.IAnimatable;
import software.bernie.geckolib3.core.builder.Animation;
import software.bernie.geckolib3.core.controller.AnimationController;
import software.bernie.geckolib3.core.event.predicate.AnimationEvent;
import software.bernie.geckolib3.core.keyframe.BoneAnimation;
import software.bernie.geckolib3.core.molang.MolangParser;
import software.bernie.geckolib3.core.processor.IBone;
import software.bernie.geckolib3.core.snapshot.BoneSnapshot;

/**
 * Ports GeckoLib-Refined's production {@code boneSnapshot} null guard into
 * original GeckoLib 3.0.57 without forking GeckoLib.
 *
 * <p>Upstream {@code AnimationController.process} relies on
 * {@code assert boneSnapshot != null}, which is a no-op on production JVMs.
 * After {@code saveSnapshotsForAnimation}, a bone listed on the current
 * animation can still be missing from {@code boneSnapshots}. The next field
 * read ({@code rotationValueX} and siblings) then throws
 * {@code NullPointerException} on the client render path.</p>
 *
 * <p>This injects at the exact descriptor of {@code process} immediately after
 * {@code saveSnapshotsForAnimation}. Missing entries are copied from the
 * matched live bone's initial snapshot so the original transition loop sees a
 * non-null value. Optional/pseudo targets are not used: GeckoLib 3.0.57 is on
 * the compile classpath, so Mixin AP must fail the build if the hook
 * disappears.</p>
 */
@Mixin(value = AnimationController.class, remap = false)
public abstract class AnimationControllerProcessMixin<T extends IAnimatable> {
    @Shadow(remap = false)
    @Final
    private HashMap<String, BoneSnapshot> boneSnapshots;

    @Shadow(remap = false)
    protected Animation currentAnimation;

    @Inject(
            method = "process(DLsoftware/bernie/geckolib3/core/event/predicate/AnimationEvent;Ljava/util/List;Ljava/util/Map;Lsoftware/bernie/geckolib3/core/molang/MolangParser;Z)V",
            at = @At(
                    value = "INVOKE",
                    target = "Lsoftware/bernie/geckolib3/core/controller/AnimationController;saveSnapshotsForAnimation(Lsoftware/bernie/geckolib3/core/builder/Animation;Ljava/util/Map;)V",
                    shift = At.Shift.AFTER),
            require = 1,
            remap = false)
    private void vonix$seedMissingBoneSnapshots(
            double tick,
            AnimationEvent<T> event,
            List<IBone> modelRendererList,
            Map<String, Pair<IBone, BoneSnapshot>> boneSnapshotCollection,
            MolangParser parser,
            boolean crashWhenCantFindBone,
            CallbackInfo ci) {
        if (currentAnimation == null || currentAnimation.boneAnimations == null || boneSnapshots == null
                || modelRendererList == null) {
            return;
        }

        for (BoneAnimation boneAnimation : currentAnimation.boneAnimations) {
            if (boneAnimation == null || boneAnimation.boneName == null) {
                continue;
            }
            if (boneSnapshots.get(boneAnimation.boneName) != null) {
                continue;
            }

            for (IBone bone : modelRendererList) {
                if (bone != null && boneAnimation.boneName.equals(bone.getName())) {
                    BoneSnapshot initialSnapshot = bone.getInitialSnapshot();
                    if (initialSnapshot != null) {
                        boneSnapshots.put(boneAnimation.boneName, new BoneSnapshot(initialSnapshot));
                    }
                    break;
                }
            }
        }
    }
}
