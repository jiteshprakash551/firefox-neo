#!/usr/bin/env bash
# Runs inside the emulator job. Installs the x86_64 twin APK, launches it, captures screenshots and logs.
set -u
mkdir -p smoke-out; cd "$GITHUB_WORKSPACE"
APK=$(ls out/app-x86_64-release.apk)
$ANDROID_HOME/build-tools/*/aapt2 dump badging "$APK" | grep -E "package:|application-label:|launchable" | tee -a smoke-out/result.txt
adb install -r "$APK" 2>&1 | tee -a smoke-out/result.txt
PKG=np.com.jiteshprakash.neo
echo "PKG=$PKG" | tee -a smoke-out/result.txt
adb shell pm grant "$PKG" android.permission.POST_NOTIFICATIONS 2>/dev/null
adb logcat -c
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 | tee -a smoke-out/result.txt
sleep 30
adb exec-out screencap -p > smoke-out/01-first-launch.png
adb shell dumpsys activity activities | grep -m3 -i "mResumedActivity\|topResumedActivity" | tee -a smoke-out/result.txt
adb shell pidof "$PKG" | tee -a smoke-out/result.txt
# open a page (emulator has internet) 
adb shell am start -a android.intent.action.VIEW -d "https://example.org" "$PKG" | tee -a smoke-out/result.txt
sleep 20
adb exec-out screencap -p > smoke-out/02-example-org.png

tap_text() { # tap first UI node whose text/content-desc matches $1 (regex)
  adb shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1; adb pull /sdcard/ui.xml /tmp/ui.xml >/dev/null 2>&1
  python3 - "$1" <<'PY' > /tmp/xy.txt
import re,sys,xml.etree.ElementTree as ET
pat=re.compile(sys.argv[1],re.I)
for n in ET.parse('/tmp/ui.xml').iter('node'):
    t=(n.get('text') or '')+'|'+(n.get('content-desc') or '')
    if pat.search(t):
        m=re.findall(r'\d+',n.get('bounds')); x1,y1,x2,y2=map(int,m); print((x1+x2)//2,(y1+y2)//2); break
PY
  read X Y < /tmp/xy.txt; [ -n "${X:-}" ] && adb shell input tap $X $Y && echo "tapped '$1' at $X,$Y" | tee -a smoke-out/result.txt || echo "NOT FOUND: $1" | tee -a smoke-out/result.txt
  sleep 3
}
UIDN=$(adb shell dumpsys package "$PKG" | sed -n 's/.*userId=\([0-9]*\).*/\1/p' | head -1); echo "uid=$UIDN" >> smoke-out/result.txt
adb shell cat /proc/net/tcp6 /proc/net/tcp | awk -v u="$UIDN" '$8==u {print "conn", $3, $4}' | sort | uniq -c > smoke-out/connections-after-load.txt
adb shell am start -a android.intent.action.VIEW -d "https://example.com" "$PKG" >/dev/null; sleep 8
tap_text "menu"
adb exec-out screencap -p > smoke-out/03-menu.png
tap_text "^settings"
for i in 1 2 3 4 5 6; do adb shell input swipe 540 1800 540 600 300; done; sleep 1
tap_text "about"
adb exec-out screencap -p > smoke-out/04-about.png
adb shell input swipe 540 1800 540 600 300; sleep 1
adb exec-out screencap -p > smoke-out/05-about-scrolled.png
adb shell input keyevent KEYCODE_BACK; adb shell input keyevent KEYCODE_BACK; adb shell input keyevent KEYCODE_BACK; sleep 2
adb shell am start -a android.intent.action.VIEW -d "about:config" "$PKG" >/dev/null; sleep 3
adb logcat -d > smoke-out/logcat.txt
grep -c "FATAL EXCEPTION" smoke-out/logcat.txt | sed 's/^/fatal_exceptions=/' | tee -a smoke-out/result.txt
adb shell pidof "$PKG" | sed 's/^/still_running_pid=/' | tee -a smoke-out/result.txt
# outbound traffic check: any hosts contacted by the app uid
UID_=$(adb shell dumpsys package "$PKG" | sed -n 's/.*userId=\([0-9]*\).*/\1/p' | head -1)
adb shell cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | head -0
grep -io "telemetry\|incoming.telemetry.mozilla.org\|sentry\|adjust" smoke-out/logcat.txt | sort | uniq -c | tee -a smoke-out/result.txt
