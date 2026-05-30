# Security Guide

Production communication must use HTTPS. WordPress-to-Core requests use API keys, HMAC signatures, timestamps, replay protection, and rate limiting. Telegram bot tokens are stored only on the Python 3 Core Server. Logs must avoid secrets.


The WordPress Connector is only a secure bridge. Business settings, Telegram tokens, report templates, permissions, and inventory rules must remain in the Python 3 Core Server.
