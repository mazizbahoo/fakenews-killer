# FakeNews Killer — Flutter App

This is the mobile client for FakeNews Killer. It sends text and screenshots to the analysis backend and shows the verdict, a shareable verdict card, and the misinformation tracker.

## Run

```bash
flutter pub get
flutter run
```

## Backend URL

The app uses the hosted API by default. To use a local backend instead, edit `baseUrl` in `lib/services/api_service.dart`. On an Android emulator, use `http://10.0.2.2:8000`.

## Release build

```bash
flutter build apk --release
```

See the [root README](../README.md) for the full documentation.
