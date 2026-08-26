package network.vonix.isleofberkgeckolibfixes;

import com.mojang.logging.LogUtils;
import net.minecraftforge.fml.common.Mod;
import org.slf4j.Logger;

@Mod(IsleOfBerkGeckoLibFixes.MOD_ID)
public class IsleOfBerkGeckoLibFixes {
    public static final String MOD_ID = "isleofberkgeckolibfixes";
    public static final Logger LOGGER = LogUtils.getLogger();

    public IsleOfBerkGeckoLibFixes() {
        LOGGER.info(
                "[IoB-GeckoLibFixes] AnimationController.process boneSnapshot guard loaded "
                        + "(v0.1.0-beta.3 beta prerelease). This companion does not replace "
                        + "GeckoLib or Isle of Berk.");
    }
}
