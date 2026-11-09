#!/usr/bin/env python3
"""Neo Browser patches. Usage: patch.py <mozilla-source-root>. Every edit asserts it matched."""
import re, sys, pathlib, glob, os
NAME = os.environ.get("NEO_NAME", "Neo Browser")
root = pathlib.Path(sys.argv[1])
fx = root / "mobile/android/fenix/app"

def edit(path, fn, desc):
    p = pathlib.Path(path)
    s = p.read_text(encoding="utf-8")
    n = fn(s)
    assert n != s, f"PATCH DID NOT APPLY: {desc} ({path})"
    p.write_text(n, encoding="utf-8")
    print("ok:", desc)

def sub1(pat, rep, flags=re.S):
    def f(s):
        n, c = re.subn(pat, rep, s, count=1, flags=flags)
        return n if c else s
    return f

# ---- build.gradle: identity, no shared Firefox uid, telemetry/crash reporting off
bg = fx / "build.gradle"
edit(bg, lambda s: s.replace('applicationId "org.mozilla"', 'applicationId "np.com.jiteshprakash"'), "applicationId -> np.com.jiteshprakash")
edit(bg, lambda s: s.replace('applicationIdSuffix ".firefox"', 'applicationIdSuffix ".neo"').replace('applicationIdSuffix ".firefox_beta"', 'applicationIdSuffix ".neobeta"'), "app id suffix .neo")
edit(bg, lambda s: s.replace('"sharedUserId": "org.mozilla.firefox.sharedID",', ''), "drop Firefox sharedUserId")
edit(bg, sub1(r"(android\.defaultConfig\.with \{\s*buildConfigField 'boolean', 'CRASH_REPORTING', )'true'(\s*buildConfigField 'boolean', 'TELEMETRY', )'true'", r"\1'false'\2'false'"), "BuildConfig CRASH_REPORTING/TELEMETRY = false")

# ---- Settings.kt defaults
st = fx / "src/main/java/org/mozilla/fenix/utils/Settings.kt"
def pref(key, old, new, desc):
    edit(st, sub1(r"(R\.string\.%s\),\s*)%s" % (key, re.escape(old)), r"\g<1>%s" % new), desc)
pref("pref_key_telemetry", "default = true,", "default = false,", "usage telemetry default OFF")
pref("pref_key_dark_theme", "default = false,", "default = true,", "dark theme default ON")
pref("pref_key_oled_theme", "default = false,", "default = true,", "OLED/true-black default ON")
pref("pref_key_tracking_protection_standard_option", "true,", "false,", "ETP standard not default")
pref("pref_key_tracking_protection_strict_default", "false,", "true,", "ETP STRICT default")
pref("pref_key_https_only", "default = false,", "default = true,", "HTTPS-only default ON")
pref("pref_key_show_search_suggestions", "default = true,", "default = false,", "search suggestions default OFF")
edit(st, sub1(r"(R\.string\.pref_key_enable_contile\),\s*default = )true", r"\1false"), "sponsored shortcuts (Contile) default OFF")
edit(st, sub1(r"(defaultValue = \{ )homescreenSections\[HomeScreenSection\.POCKET\] == true( \},)", r"\1false\2"), "sponsored/Pocket stories default OFF")
edit(st, sub1(r"(featureFlag = ContentRecommendationsFeatureHelper)", r"\1"), "noop-anchor") if False else None
edit(st, sub1(r"defaultValue = \{ enableFxSuggest \}", "defaultValue = { false }"), "sponsored suggestions default OFF")

# ---- user-visible "Firefox" -> "Neo" in all string resources (before About text is set)
cnt = 0
for f in glob.glob(str(fx/"src/main/res/values*/strings.xml")):
    p = pathlib.Path(f); t = p.read_text(encoding="utf-8")
    # keep truthful names of Mozilla-run services / legal docs; everything else becomes the app name
    n = re.sub(r"Firefox(?! (?:Account|account|Relay|Monitor|Suggest|Sync|Terms|Privacy|Focus|Klar|Accounts|Send|Color|Colors))", "Neo", t)
    if n != t: p.write_text(n, encoding="utf-8"); cnt += 1
assert cnt > 50, "string rebrand touched too few files"
print("ok: Firefox->Neo in", cnt, "string files")
# ---- Mozilla-specific onboarding (Mozilla ToU, data sharing, marketing, sync) is skipped
edit(st, lambda s: s.replace("if (isBenchmarkBuild && !forceOnboardingForBenchmark) {", "if (isBenchmarkBuild || !forceOnboardingForBenchmark) {"), "skip Mozilla onboarding flow")

# ---- hide Mozilla-specific settings entries: Play Store rating (Mozilla listing) and Nimbus "remote improvements"
prefx = fx/"src/main/res/xml/preferences.xml"
def hide(key):
    def f(s):
        return s.replace('android:key="@string/%s"' % key, 'android:key="@string/%s"\n            app:isPreferenceVisible="false"' % key, 1)
    return f
edit(prefx, hide("pref_key_rate"), "hide Rate on Google Play")
edit(prefx, hide("pref_key_remote_improvements"), "hide Remote improvements (Nimbus rollouts)")
edit(st, lambda s: s.replace("default = { appContext.components.nimbus.sdk.rolloutParticipation },", "default = { false },"), "rollouts default OFF")

# ---- no periodic Nimbus experiment/message fetch from Mozilla servers while experimentation is off
mw = fx/"src/main/java/org/mozilla/fenix/messaging/MessageNotificationWorker.kt"
edit(mw, lambda s: s.replace("        val nimbus = context.components.nimbus\n\n        // Refresh messages", "        val nimbus = context.components.nimbus\n        if (!context.components.settings.isExperimentationEnabled) return Result.success()\n\n        // Refresh messages", 1), "MessageNotificationWorker: no Nimbus fetch when experimentation off")

# ---- About page links: point at this project, not Mozilla's release notes/support/privacy pages
ab = fx/"src/main/java/org/mozilla/fenix/settings/about/AboutFragment.kt"
def about(s):
    n = s.replace("SupportUtils.WHATS_NEW_URL,", '"https://github.com/jiteshprakash551/neo-browser",', 1)
    n = n.replace("getString(R.string.about_whats_new, getString(R.string.firefox)),", '"Source code and changes",', 1)
    n = n.replace("SupportUtils.getSumoURLForTopic(context, SupportUtils.SumoTopic.HELP),", '"https://github.com/jiteshprakash551/neo-browser/issues",', 1)
    n = n.replace("SupportUtils.getMozillaPageUrl(SupportUtils.MozillaPage.PRIVACY_NOTICE),", '"https://github.com/jiteshprakash551/neo-browser/blob/main/PRIVACY.md",', 1)
    assert n.count("jiteshprakash551/neo-browser") == 3
    return n
edit(ab, about, "About links -> Neo project (source, support, privacy)")

# ---- names & About
for f in [fx/"src/release/res/values/static_strings.xml", fx/"src/main/res/values/static_strings.xml", fx/"src/beta/res/values/static_strings.xml", fx/"src/nightly/res/values/static_strings.xml"]:
    edit(f, sub1(r'(<string name="app_name" translatable="false">)[^<]*(</string>)', r'\1' + NAME + r'\2'), "app_name -> Firefox Neo")
sm = fx/"src/main/res/values/strings.xml"
edit(sm, sub1(r'(<string name="about_content"[^>]*>)[^<]*(</string>)', r'\1%1$s - Built by Jitesh (jiteshprakash.com.np). Independent browser built on open-source code from Mozilla (Firefox and Gecko are trademarks of the Mozilla Foundation). Not affiliated with or endorsed by Mozilla. Telemetry removed.\2'), "About credit: Built by Jitesh")
for f in glob.glob(str(fx/"src/main/res/values-*/strings.xml")):
    p = pathlib.Path(f); s = p.read_text(encoding="utf-8")
    n = re.sub(r'\s*<string name="about_content"[^>]*>.*?</string>', '', s, flags=re.S)
    if n != s: p.write_text(n, encoding="utf-8")
print("ok: localized about_content removed")

# ---- Glass-inspired dark palette: blue-tinted "ink" grays + translucent raised surfaces (no real blur)
nova = root / "mobile/android/android-components/components/ui/colors/src/main/res/values/nova_colors.xml"
ink = {90:"ff0a0c18",85:"ff0d1020",80:"ff11152a",75:"ff151a33",70:"ff1b2140",65:"ff232a4d",60:"ff2e3660",55:"ff3d4672"}
def tint(s):
    for k, v in ink.items():
        s = re.sub(r'(<color name="novaGray%d">#)[0-9a-fA-F]{8}' % k, r'\g<1>%s' % v, s)
    return s
edit(nova, tint, "ink-tinted dark grays")
night = fx / "src/main/res/values-night/colors.xml"
def glass(s):
    s = s.replace('<color name="fx_mobile_surface_container_high">@color/novaGray70</color>', '<color name="fx_mobile_surface_container_high">#F21b2140</color>')
    s = s.replace('<color name="fx_mobile_surface_container_highest">@color/novaGray65</color>', '<color name="fx_mobile_surface_container_highest">#EB232a4d</color>')
    s = s.replace('<color name="fx_mobile_surface_bright">@color/novaGray65</color>', '<color name="fx_mobile_surface_bright">#EB232a4d</color>')
    s = s.replace('<color name="fx_mobile_primary">@color/novaViolet20</color>', '<color name="fx_mobile_primary">#ff8fd9ff</color>')
    return s
edit(night, glass, "translucent raised surfaces + cyan accent")

# ---- manifest: no shared UID with Mozilla's Firefox
mf = fx / "src/release/AndroidManifest.xml"
edit(mf, lambda s: re.sub(r'\s*android:sharedUserId="\$\{sharedUserId\}"', '', s), "manifest sharedUserId removed")

# ---- manifest: strip ad/attribution/push permissions + Adjust receiver
mm = fx / "src/main/AndroidManifest.xml"
def strip_perms(s):
    s = s.replace('<uses-permission android:name="com.adjust.preinstall.READ_PERMISSION"/>',
        '<uses-permission android:name="com.adjust.preinstall.READ_PERMISSION" tools:node="remove" />\n'
        '    <uses-permission android:name="com.google.android.gms.permission.AD_ID" tools:node="remove" />\n'
        '    <uses-permission android:name="com.google.android.c2dm.permission.RECEIVE" tools:node="remove" />\n'
        '    <uses-permission android:name="com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE" tools:node="remove" />')
    s = re.sub(r'<receiver\s+android:name="com\.adjust\.sdk\.AdjustPreinstallReferrerReceiver".*?</receiver>',
        '<receiver android:name="com.adjust.sdk.AdjustPreinstallReferrerReceiver" tools:node="remove" />', s, flags=re.S)
    return s
edit(mm, strip_perms, "manifest: Adjust/AD_ID/c2dm/install-referrer removed")

# ---- version name (artifact build leaves it null): "<Firefox base version>-neo"
ver = (root / "browser/config/version.txt").read_text().strip()
edit(bg, lambda s: s.replace('"${Config.releaseVersionName(project)}"', '"%s-neo"' % ver), "versionName = base version + -neo (%s)" % ver)
