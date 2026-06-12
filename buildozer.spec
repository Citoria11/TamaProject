[app]
title = Scratch
package.name = scratchtama
package.domain = org.h
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,plyer
orientation = portrait
fullscreen = 0

# Permissions for battery, network and device telemetry access
android.permissions = SYSTEM_ALERT_WINDOW,INTERNET

# Optimized for modern 64-bit Android phones
android.archs = arm64-v8a
android.accept_sdk_license = True
