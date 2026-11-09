# Neo Browser privacy notice

Neo Browser is built by Jitesh (jiteshprakash.com.np) from open-source Mozilla code (Firefox for Android and the Gecko engine). It is independent and not affiliated with or endorsed by Mozilla. "Firefox" and "Gecko" are trademarks of the Mozilla Foundation.

## What Neo Browser itself does not do
- Neo has no servers and collects no data. There is no Neo account, analytics or tracking.
- Mozilla telemetry (Glean), crash reporting, experiments (Nimbus), the daily usage ping, Adjust install attribution, sponsored shortcuts, sponsored suggestions and search suggestions are switched off or removed in this build.
- The first-run onboarding that asked you to share data with Mozilla is removed.

## What still connects to the network (not removed on purpose)
- Websites you open, and your search engine (Google by default - you can change it in Settings > Search).
- Mozilla Remote Settings and add-on infrastructure: search engine lists, tracking-protection and certificate/blocklist data and add-on updates. These are needed for security and normal browsing; they are requests to Mozilla servers, not telemetry.
- Safe Browsing (phishing and malware checks), kept on for your protection.
- Mozilla account sync only if you choose to sign in. That is Mozilla's service under Mozilla's terms.

## Defaults
Strict Enhanced Tracking Protection, HTTPS-only mode, dark theme, no search suggestions.

## Limits
This is a hobby-built browser with no security-team or update service behind it. You must install updates yourself from the project's releases. No claim is made that it is free of vulnerabilities or malware. Source and patches: https://github.com/jiteshprakash551/neo-browser
