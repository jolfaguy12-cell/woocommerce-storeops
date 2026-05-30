# Security Guide

Production communication must use HTTPS. WordPress-to-Core requests use API keys, HMAC signatures, timestamps, replay protection, and rate limiting. Telegram bot tokens are stored only on the Python 3 Core Server. Logs must avoid secrets.
