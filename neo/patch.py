#!/usr/bin/env python3
"""Firefox Neo patches. Usage: patch.py <mozilla-source-root>. Every edit asserts it matched."""
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
