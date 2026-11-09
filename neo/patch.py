#!/usr/bin/env python3
"""Firefox Neo patches. Usage: patch.py <mozilla-source-root>. Every edit asserts it matched."""
import re, sys, pathlib, glob
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

# ---- names & About
for f in [fx/"src/release/res/values/static_strings.xml", fx/"src/main/res/values/static_strings.xml", fx/"src/beta/res/values/static_strings.xml", fx/"src/nightly/res/values/static_strings.xml"]:
    edit(f, sub1(r'(<string name="app_name" translatable="false">)[^<]*(</string>)', r'\1Firefox Neo\2'), "app_name -> Firefox Neo")
sm = fx/"src/main/res/values/strings.xml"
edit(sm, sub1(r'(<string name="about_content"[^>]*>)[^<]*(</string>)', r'\1%1$s - Built by Jitesh (jiteshprakash.com.np). Built on the open-source Firefox engine from Mozilla, with telemetry removed.\2'), "About credit: Built by Jitesh")
for f in glob.glob(str(fx/"src/main/res/values-*/strings.xml")):
    p = pathlib.Path(f); s = p.read_text(encoding="utf-8")
    n = re.sub(r'\s*<string name="about_content"[^>]*>.*?</string>', '', s, flags=re.S)
    if n != s: p.write_text(n, encoding="utf-8")
print("ok: localized about_content removed")
