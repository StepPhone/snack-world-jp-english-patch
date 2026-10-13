# Snack World JP English Patch — v0.5.1

English localization overlay for the Japanese Switch base game, **010072B007418000, version 1.0.0 (v0)**. **Patch version: v0.5.1 (test build).** Game version 1.0.0 above is the compatibility requirement, not the patch version.

By **StepPhone of the StepHackerZ**.

This public repository contains release notes, installation instructions and known issues. The builder and developer instructions are maintained privately.

## Ready-to-install downloads

Open the [v0.5.1 release](https://github.com/StepPhone/snack-world-jp-english-patch/releases/tag/v0.5.1) and download **both ZIPs for your platform**:

| Platform | Required downloads |
| --- | --- |
| Eden | `Snack-World-v0.5.1-Eden-Main.zip` and `Snack-World-v0.5.1-Eden-Movies.zip` |
| Switch / Atmosphere | `Snack-World-v0.5.1-Switch-Main.zip` and `Snack-World-v0.5.1-Switch-Movies.zip` |

**No Python, terminal commands, extracted RomFS, EUR files or builder are needed for these downloads.** You still need the Japanese base game installed. The two ZIPs contain different parts of the same mod; extract both into the same folder and merge folders when prompted. Do not use the automatic Source code downloads.

## Load in Eden

1. Save and stop the game. Disable or remove the previous version of this mod.
2. Extract both Eden ZIPs into the same folder.
3. Right-click the Japanese game in Eden and open its mod directory.
4. Copy the extracted **English Translation** folder into that directory.
5. Enable **English Translation** in the game's properties and launch.

The result must be `<mod directory>/English Translation/romfs/archive_a.fa` and two MP4 files under `English Translation/romfs/mov/`. Do not nest another `romfs` folder inside it.

## Load on Switch

For a Switch already running Atmosphere with game mod support:

1. Save and close the game; keep a save backup.
2. Extract both Switch ZIPs into the same folder.
3. Copy the extracted **atmosphere** folder to the SD card root, merging folders. Preserve unrelated mods.
4. Launch the Japanese base game.

The result must be `SD:/atmosphere/contents/010072B007418000/romfs/archive_a.fa` and two MP4 files under its `mov` folder. No individual installed file exceeds 4 GiB. Physical Switch and handheld-mode testing remain outstanding. Updates and conflicting mods are unsupported until tested.

## Update or uninstall

Close the game before changing mod files. When updating, remove the old mod's `sw-t_evop_0001.mp4` opening override if present: v0.5.1 retains the original Japanese opening. Do not enable two versions together.

To uninstall in Eden, disable or remove the English Translation folder. On Switch, remove only this patch's `archive_a.fa` and its two ending movie overlays (`sw-t_eved_0001.mp4` and `sw-t_eved_0002.mp4`). Saves are not modified by installing or uninstalling.

All packaged game files were read back from the ZIPs and hash-checked against the installed mod. `SHA256SUMS.txt` provides download checksums. This packaging update contains the same v0.5.1 game files.

## Optional smaller delta package

The older `Snack-World-JP-English-Patch-v0.5.1.zip` remains available for users who prefer applying a delta to original extracted JP files. **Only that optional download requires Python 3.11+ and extracted RomFS.** Its included README explains the command. It is not required for the ready-to-install ZIPs above. The developer builder remains private.

## Included corrections

- Japanese title logo with the English start prompt.

- Repaired the Watch anime button, highlighted state and submenu: English episode labels, wrapped summaries and the original opaque background. Native texture compression preserves title-screen loading.
- Shortened the overflowing Mermaidol dialogue to two lines.

- English text and compatible graphics drawn from the EUR localization, with additional translations for unmatched Japanese entries.
- Explicit wrapping and shorter descriptions for item, boon, Jara skill and burst panels; restored missing menu font styles.
- Save, dialogue-choice and reward popup text corrections.
- Quoted voice parameters for 1,734 cues, preventing the JP parser from treating subsequent dialogue as part of a voice filename.
- Original working character-name keyboard. Choose **A/1** for Latin letters; bottom-right confirms and bottom-left cancels.
- Additional StepHackerZ startup credit after the original logos, on the native 1080p canvas scaled to the game's output.
- English ending movie overlays; the original Japanese opening is retained.

## Test status and known issues

The native ARM64 parser regression test reproduced the malformed voice filenames on both the Gale and Mayonna lines; quoted parameters return the intended IDs. **Those exact freeze scenes have not yet been replayed in-game**, so this is not a claim that every freeze is resolved.

Character creation, the corrected Jara layout, title loading, the Watch anime button and all four episode-menu pages were confirmed in user playtesting. Startup credit rendering and continuation were observed in Eden docked mode. A complete playthrough has not been performed.

**Anime videos still do not play in Eden.** The repaired menu is usable, but playback remains unresolved; its Japanese playback-control labels also remain untranslated. Enabling Eden's browser applet did not resolve playback in the reported test. No emulator configuration is included in this patch.

Quest alignment was adjusted, but EUR-style scrolling is not yet implemented or verified. The empty Madusa battle banner and intermittent striped menu backgrounds remain under investigation. Some incompatible graphics and Japanese keyboard labels remain original. The targeted text scan passed, but this does not establish that every screen is translated or free of overflow.

Report problems with a screenshot, game version, emulator/version or hardware, patch revision and reproduction steps. Keep a save before the affected scene when possible. Do not post game files, keys or personal logs publicly.

## Credits

Project and startup artwork: **StepPhone of the StepHackerZ**. [Support StepPhone](https://ko-fi.com/stepphone).

Original game and EUR localization belong to their respective rights holders. Format research references: [Kuriimu2](https://github.com/FanTranslatorsInternational/Kuriimu2), [CfgBinEditor](https://github.com/onepiecefreak3/CfgBinEditor), and [XtractQuery](https://github.com/onepiecefreak3/XtractQuery).

