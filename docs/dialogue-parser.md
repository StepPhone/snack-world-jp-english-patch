# Voice parameter correction

Two reported freezes displayed an empty speech bubble while audio continued: after receiving Gale and in Mayonna's tavern conversation. Crash-register bytes corresponded to the affected dialogue strings.

The Japanese native tag scanner accepts both `#` and a quote as parameter delimiters. Its parameter-copy routine searches for a closing quote before falling back to `>`. Consequently, a tag such as `<PV#voice_id>` followed by dialogue containing a double quote can consume the intervening dialogue as part of the voice filename.

The repair uses the native quoted form, `<PV"voice_id">`. Dialogue content and Japanese voice IDs are retained. No executable modification is required.

An isolated Unicorn test executed the original JP ARM64 tag scanner at `0x6a7c74` and parameter-copy routine at `0x6a92a0`, with host stubs for allocation and memory copying. Both reported lines produced oversized parameters before the correction and their exact intended voice IDs afterward. This directly verifies the parser behavior; it is not a full emulation of either game scene.

The staged archive corrected 1,734 voice parameters and passed independent verification of all 18,392 members. The available saves were after the affected scenes, so replay validation remains outstanding. Other freeze causes are possible.
