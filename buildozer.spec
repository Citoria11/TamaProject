[app]
title = Scratch
package.name = scratchtama
package.domain = org.h
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# This is the crucial permission that lets the app float over your screen
android.permissions = SYSTEM_ALERT_WINDOW

# Optimized for modern 64-bit Android phones
android.archs = arm64-v8a
android.accept_sdk_license = True
