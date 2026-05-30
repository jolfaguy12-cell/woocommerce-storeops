<?php

defined('ABSPATH') || exit;

class StoreOps_REST_API {
    public static function init(): void {
        add_action('rest_api_init', [__CLASS__, 'register_routes']);
    }

    public static function register_routes(): void {
        register_rest_route('storeops/v1', '/products/changed', [
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => [__CLASS__, 'changed_products'],
            'args' => [
                'cursor' => ['default' => 0, 'sanitize_callback' => 'absint'],
                'limit' => ['default' => 100, 'sanitize_callback' => 'absint'],
            ],
        ]);

        register_rest_route('storeops/v1', '/connection-test', [
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => static fn() => ['status' => 'ok', 'plugin' => STOREOPS_CONNECTOR_VERSION],
        ]);
    }

    public static function changed_products(WP_REST_Request $request): array {
        $limit = min(max((int) $request->get_param('limit'), 1), 250);
        $cursor = (int) $request->get_param('cursor');
        $items = StoreOps_Product_Reader::changed_since($cursor, $limit);

        update_option('storeops_last_successful_sync_at', current_time('mysql'), false);

        return [
            'items' => $items,
            'next_cursor' => time(),
            'has_more' => count($items) >= $limit,
        ];
    }
}
