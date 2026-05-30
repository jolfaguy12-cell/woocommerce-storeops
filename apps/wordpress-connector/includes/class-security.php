<?php

defined('ABSPATH') || exit;

class StoreOps_Security {
    public static function api_key(): string {
        return (string) get_option('storeops_api_key', '');
    }

    public static function hmac_secret(): string {
        return (string) get_option('storeops_hmac_secret', '');
    }

    public static function is_enabled(): bool {
        return (bool) get_option('storeops_enabled', false);
    }

    public static function verify_request(WP_REST_Request $request): bool|WP_Error {
        if (!self::is_enabled()) {
            return new WP_Error('storeops_disabled', 'StoreOps connector is disabled.', ['status' => 403]);
        }

        $provided = (string) $request->get_header('x-storeops-api-key');
        if ($provided === '' || !hash_equals(self::api_key(), $provided)) {
            return new WP_Error('storeops_auth_failed', 'Invalid StoreOps API key.', ['status' => 401]);
        }

        $timestamp = (string) $request->get_header('x-storeops-timestamp');
        $signature = (string) $request->get_header('x-storeops-signature');
        $secret = self::hmac_secret();
        if ($secret !== '') {
            if ($timestamp === '' || $signature === '' || abs(time() - (int) $timestamp) > 300) {
                return new WP_Error('storeops_replay_protection_failed', 'Invalid or expired StoreOps timestamp.', ['status' => 401]);
            }
            $message = $timestamp . '.' . $request->get_method() . '.' . $request->get_route() . '?' . wp_json_encode($request->get_query_params());
            $expected = hash_hmac('sha256', $message, $secret);
            if (!hash_equals($expected, $signature)) {
                return new WP_Error('storeops_signature_failed', 'Invalid StoreOps request signature.', ['status' => 401]);
            }
        }

        return true;
    }
}
