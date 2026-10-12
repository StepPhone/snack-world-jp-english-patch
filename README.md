# Snack World JP English Patch — v0.5

English localization overlay for the Japanese Switch base game, **010072B007418000, version 1.0.0 (v0)**. **Patch version: v0.5 (test build).** Game version 1.0.0 above is the compatibility requirement, not the patch version.

By **StepPhone of the StepHackerZ**.

This public repository contains release notes, installation instructions and known issues. The builder and developer instructions are maintained privately.

A standalone player patch download is not currently published. Historical source-code downloads are old developer snapshots, not ready-to-install mods. The installation steps below apply once you have a generated RomFS overlay. Python, Pillow and EUR files are not needed to run an already-built overlay.

## Load in Eden

1. Save and stop the game.
2. Right-click the **Japanese** game and open its mod directory.
3. Create `English Translation/romfs` there and copy the contents of the generated `romfs` folder into it.
4. Enable **English Translation** in the game's properties, then launch.

The result should be `<mod directory>/English Translation/romfs/archive_a.fa`, plus `romfs/mov/*.mp4`. Do not nest another `romfs` folder inside it. The Japanese game-list title is normal. The English title screen and StepHackerZ startup credit identify the loaded patch.

## Load on Switch

For a Switch already running Atmosphere with game mod support:

1. Save and close the game; keep a save backup.
2. Copy the contents of the generated `romfs` folder to `SD:/atmosphere/contents/010072B007418000/romfs/`.
3. Launch the Japanese base game.

No individual output file exceeds 4 GiB. Physical Switch and handheld-mode testing are still outstanding. Updates and mods replacing the same files are unsupported until tested.

## Uninstall or update

Close the game before changing files. On Eden, disable or remove this mod's folder. On Switch, remove only this patch's archive and its three movies from the title's RomFS directory. Save data is not changed by installing or removing the overlay. When updating, replace the previous patch files rather than enabling two versions together.

## Included corrections

- Repaired the Watch anime button, highlighted state and submenu: English episode labels, wrapped summaries and the original opaque background. Native texture compression preserves title-screen loading.
- Shortened the overflowing Mermaidol dialogue to two lines.

- English text and compatible graphics drawn from the EUR localization, with additional translations for unmatched Japanese entries.
- Explicit wrapping and shorter descriptions for item, boon, Jara skill and burst panels; restored missing menu font styles.
- Save, dialogue-choice and reward popup text corrections.
- Quoted voice parameters for 1,734 cues, preventing the JP parser from treating subsequent dialogue as part of a voice filename.
- Original working character-name keyboard. Choose **A/1** for Latin letters; bottom-right confirms and bottom-left cancels.
- Additional StepHackerZ startup credit after the original logos, on the native 1080p canvas scaled to the game's output.
- English opening and ending movie overlays, retaining external Japanese audio.

## Test status and known issues

The native ARM64 parser regression test reproduced the malformed voice filenames on both the Gale and Mayonna lines; quoted parameters return the intended IDs. **Those exact freeze scenes have not yet been replayed in-game**, so this is not a claim that every freeze is resolved. See [technical notes](docs/dialogue-parser.md).

Character creation, the corrected Jara layout, title loading, the Watch anime button and all four episode-menu pages were confirmed in user playtesting. Startup credit rendering and continuation were observed in Eden docked mode. A complete playthrough has not been performed.

**Anime videos still do not play in Eden.** The repaired menu is usable, but playback remains unresolved; its Japanese playback-control labels also remain untranslated. Enabling Eden's browser applet did not resolve playback in the reported test. No emulator configuration is included in this patch.

Quest alignment was adjusted, but EUR-style scrolling is not yet implemented or verified. The empty Madusa battle banner and intermittent striped menu backgrounds remain under investigation. Some incompatible graphics and Japanese keyboard labels remain original. The targeted text scan passed, but this does not establish that every screen is translated or free of overflow.

Report problems with a screenshot, game version, emulator/version or hardware, patch revision and reproduction steps. Keep a save before the affected scene when possible. Do not post game files, keys or personal logs publicly.

## Credits

Project and startup artwork: **StepPhone of the StepHackerZ**. [Support StepPhone](https://ko-fi.com/stepphone).

Original game and EUR localization belong to their respective rights holders. Format research references: [Kuriimu2](https://github.com/FanTranslatorsInternational/Kuriimu2), [CfgBinEditor](https://github.com/onepiecefreak3/CfgBinEditor), and [XtractQuery](https://github.com/onepiecefreak3/XtractQuery).
