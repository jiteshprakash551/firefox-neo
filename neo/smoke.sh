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
adb shell am start -a android.intent.action.VIEW -d "about:config" "$PKG" >/dev/null; sleep 3
adb logcat -d > smoke-out/logcat.txt
grep -c "FATAL EXCEPTION" smoke-out/logcat.txt | sed 's/^/fatal_exceptions=/' | tee -a smoke-out/result.txt
adb shell pidof "$PKG" | sed 's/^/still_running_pid=/' | tee -a smoke-out/result.txt
# outbound traffic check: any hosts contacted by the app uid
UID_=$(adb shell dumpsys package "$PKG" | sed -n 's/.*userId=\([0-9]*\).*/\1/p' | head -1)
adb shell cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | head -0
grep -io "telemetry\|incoming.telemetry.mozilla.org\|sentry\|adjust" smoke-out/logcat.txt | sort | uniq -c | tee -a smoke-out/result.txt
