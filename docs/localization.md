# Date & Localization Settings

StoreOps stores all database timestamps as UTC Gregorian values. The dashboard, reports, and Telegram messages convert timestamps for display using the Core Server datetime utilities.

Environment defaults:

```env
DATE_DISPLAY_MODE=jalali
TIMEZONE=Asia/Tehran
```

Supported display modes are `jalali` and `gregorian`.
