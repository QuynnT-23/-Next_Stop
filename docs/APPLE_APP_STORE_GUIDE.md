# Next Stop: Apple App Store (iOS) Publishing & Mobile Deployment Guide

This guide outlines the end-to-end architecture and step-by-step pipeline to compile, containerize, test, and publish **Next Stop** to the **Apple App Store** for iPhone and iPad.

---

## 1. Architecture Overview

```
+-----------------------------------------------------------+
|                   Next Stop (Python & Pygame)             |
|   - Dynamic Analog Virtual Joystick (Left)                |
|   - Mobile Action Cluster (Fire/Aim, Dash, Block, Super)  |
|   - Native Touch Events (SDL / pygame.FINGERDOWN/UP)      |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                  Pygbag WASM Compilation                  |
|   - Compiles Python runtime + Pygame CE to WebAssembly    |
|   - Generates static index.html, .wasm, and web assets   |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                Capacitor (iOS Native Wrapper)             |
|   - Wraps WASM web bundle into an official Xcode project  |
|   - Embeds native WKWebView with metal hardware accel     |
|   - Configures Safe Area, Notch Insets, and Orientation   |
+-----------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------+
|               Xcode & Apple App Store Connect             |
|   - Code Signing & Provisioning Profiles                  |
|   - TestFlight Beta Builds for iOS Devices                |
|   - App Store Production Review & Worldwide Release       |
+-----------------------------------------------------------+
```

---

## 2. Prerequisites

1. **Hardware & OS**: macOS Sequoia / Sonoma running on an Apple Silicon or Intel Mac.
2. **Software**:
   - Xcode 15+ installed via the Mac App Store.
   - Xcode Command Line Tools: `xcode-select --install`
   - CocoaPods (if required by native plugins): `brew install cocoapods`
   - Node.js 18+ and npm: `brew install node`
   - Python 3.11+: `./.venv/bin/python3`
3. **Apple Developer Account**:
   - Enrolled in the [Apple Developer Program](https://developer.apple.com/programs/) ($99/year) to generate distribution certificates, provisioning profiles, and submit to App Store Connect.

---

## 3. Mobile Virtual On-Screen Controls Architecture

Next Stop includes a built-in virtual touch control system (`src/ui/mobile_controls.py`):

1. **Left Analog Thumbstick (`VirtualStick`)**:
   - Floating knob with dead-zone handling.
   - Returns normalized directional vectors directly to `InputHandler`.
   - Supports dragging and multi-finger tracking.
2. **Right Action Cluster (`VirtualButton`)**:
   - **FIRE / AIM**: Main primary attack button.
   - **DASH (SHIFT)**: Quick evasion dash.
   - **BLOCK (SPACE)**: Defensive posture & parry stance.
   - **SUPER (Q)**: Equipped conductor ultimate ability.
   - **USE (E)**: Contextual interaction (docking bay doors, workshop anvil, armory workbench).
3. **Touch Event Engine**:
   - Listens to both native SDL multi-touch events (`FINGERDOWN`, `FINGERMOTION`, `FINGERUP`) and mouse emulation.
   - Toggleable on desktop via the `[M]` key or clicking the top-right `📱 [M] TOUCH UI` pill.
   - Auto-enabled on touch screens.

---

## 4. Step-by-Step Build & Packaging Pipeline

### Step 1: Package Python Game into WebAssembly (WASM)

We use `pygbag` to bundle Python code, assets, and dependencies into high-performance WASM:

```bash
# 1. Install pygbag in your python environment
./.venv/bin/pip install pygbag

# 2. Build the game for web/mobile deployment
./.venv/bin/python3 -m pygbag --build .

# The generated HTML5/WASM bundle will be in build/web/
```

### Step 2: Initialize the Capacitor iOS Container

[Capacitor](https://capacitorjs.com/) wraps web/WASM applications into native iOS apps without performance compromises, using Apple's high-speed `WKWebView`:

```bash
# 1. Initialize Capacitor in the Next_Stop_2026 directory
npm init @capacitor/app@latest next-stop-ios \
  --app-id "com.chudstudios.nextstop" \
  --app-name "Next Stop" \
  --web-dir "build/web"

cd next-stop-ios

# 2. Install Capacitor iOS platform
npm install @capacitor/ios
npx cap add ios
```

### Step 3: Configure Screen Orientation & Safe Area

In `capacitor.config.json` (or `capacitor.config.ts`), lock orientation to Landscape and disable elastic bouncing:

```json
{
  "appId": "com.chudstudios.nextstop",
  "appName": "Next Stop",
  "webDir": "build/web",
  "bundledWebRuntime": false,
  "ios": {
    "contentInset": "always",
    "allowsLinkPreview": false,
    "scrollEnabled": false
  },
  "plugins": {
    "SplashScreen": {
      "launchShowDuration": 2000,
      "backgroundColor": "#0d0f14"
    }
  }
}
```

In Xcode or `Info.plist`:
- Set **Supported Interface Orientations**:
  - `UIInterfaceOrientationLandscapeLeft`
  - `UIInterfaceOrientationLandscapeRight`
- Set **Requires Full Screen**: `YES`
- Set **Status bar hidden**: `YES`
- Set **UIViewControllerBasedStatusBarAppearance**: `NO`

### Step 4: Audio Session Configuration for iOS

iOS requires WebAudio / SDL audio context unlock on the first user touch gesture:
1. `src/ui/splash_screen.py` already includes an initial click-to-start screen ("Tap to Depart"), which automatically un-mutes the browser/WKWebView audio context.
2. In native iOS, add `AVAudioSessionCategoryAmbient` in `AppDelegate.swift` so background music plays properly with the device's silent switch.

### Step 5: Sync & Open in Xcode

```bash
# Copy web assets into the native Xcode project
npx cap sync ios

# Open the project in Xcode
npx cap open ios
```

---

## 5. Xcode Signing & App Store Submission

### Step 1: Configure Signing & Capabilities in Xcode
1. In the Xcode Project Navigator, select the `App` target.
2. Navigate to **Signing & Capabilities**.
3. Check **Automatically manage signing**.
4. Select your **Apple Developer Team**.
5. Set **Bundle Identifier**: `com.chudstudios.nextstop`.

### Step 2: Test on iPhone Simulator & Physical Device
1. Connect your physical iPhone or iPad via USB.
2. Trust the developer certificate under **Settings > General > VPN & Device Management** on your iPhone.
3. Select your device in Xcode's scheme selector and click **Run** (`⌘R`).
4. Verify:
   - 60 FPS frame pacing.
   - Dual-cluster virtual thumbstick and buttons respond instantly to multi-touch.
   - Audio effects and train engine sounds trigger cleanly.
   - Notch and Dynamic Island do not obstruct HUD counters.

### Step 3: Create App Store Connect Record
1. Visit [App Store Connect](https://appstoreconnect.apple.com).
2. Go to **Apps > New App**.
3. Choose **Platform**: `iOS`.
4. Name: `Next Stop: Train Roguelite`.
5. Primary Language: `English (US)`.
6. Bundle ID: `com.chudstudios.nextstop`.
7. SKU: `CHUD-NEXTSTOP-01`.

### Step 4: Archive and Upload Build
1. In Xcode, select target destination **Any iOS Device (arm64)**.
2. Go to **Product > Archive**.
3. When the Organizer window opens, click **Distribute App**.
4. Select **App Store Connect > Upload**.
5. Keep default symbols and bitcode settings and click **Upload**.

### Step 5: TestFlight & App Store Review
1. Once processing finishes (usually 10–15 minutes), open **TestFlight** in App Store Connect.
2. Add internal and external testers.
3. Fill out App Store listing:
   - App Screenshots (6.7" iPhone 16 Pro Max & 12.9" iPad Pro).
   - App Description & Keywords.
   - Age Rating (12+ for Mild Fantasy Violence).
   - Privacy Policy & Data Collection (No third-party tracking, local storage only).
4. Click **Submit for Review**.

---

## 6. Performance & Quality Checklist

| Requirement | Status | Implementation in Next Stop |
| :--- | :---: | :--- |
| **Virtual On-Screen Touch Controls** | **Done** | `src/ui/mobile_controls.py` with multi-touch analog thumbstick & buttons |
| **Touch Toggle Key / UI** | **Done** | `[M]` key or click on `📱 TOUCH UI` toggle button |
| **60 FPS Performance** | **Done** | Optimized blitting, sub-millisecond particle batches |
| **Safe Area Insets** | **Done** | 70px margin padding ensures controls clear iPhone Dynamic Island |
| **Offline Playability** | **Done** | Full local SQLite/JSON progression, high scores, and audio |
| **Landscape Lock** | **Done** | Configured in `CapacitorConfig.json` and `Info.plist` |
| **Apple Audio Guidelines** | **Done** | Tap-to-start splash screen un-mutes WebAudio cleanly |
