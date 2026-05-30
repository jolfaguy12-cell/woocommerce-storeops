<?php

defined('ABSPATH') || exit;

class StoreOps_REST_API {
    public static function init(): void {
        add_action('rest_api_init', [__CLASS__, 'register_routes']);
    }

    public static function register_routes(): void {
        register_rest_route('storeops/v1', '/products', [
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => [__CLASS__, 'products'],
            'args' => [
                'page' => ['default' => 1, 'sanitize_callback' => 'absint'],
                'per_page' => ['default' => 50, 'sanitize_callback' => 'absint'],
                'status' => ['default' => 'any', 'sanitize_callback' => 'sanitize_key'],
            ],
        ]);

        register_rest_route('storeops/v1', '/products/(?P<id>\d+)/variations', [
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => [__CLASS__, 'product_variations'],
        ]);

        register_rest_route('storeops/v1', '/changes', [
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => [__CLASS__, 'changes'],
        ]);

        register_rest_route('storeops/v1', '/changes/ack', [
            'methods' => WP_REST_Server::CREATABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => [__CLASS__, 'ack_changes'],
        ]);

        register_rest_route('storeops/v1', '/products/changed', [
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => [__CLASS__, 'changed_products'],
            'args' => [
                'cursor' => ['default' => 0, 'sanitize_callback' => 'absint'],
                'limit' => ['default' => 50, 'sanitize_callback' => 'absint'],
            ],
        ]);

        register_rest_route('storeops/v1', '/products/full-sync', [
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => [__CLASS__, 'full_sync_products'],
            'args' => [
                'page' => ['default' => 1, 'sanitize_callback' => 'absint'],
                'limit' => ['default' => 50, 'sanitize_callback' => 'absint'],
            ],
        ]);

        register_rest_route('storeops/v1', '/connection-test', [
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => ['StoreOps_Security', 'verify_request'],
            'callback' => static fn() => ['status' => 'ok', 'plugin' => STOREOPS_CONNECTOR_VERSION],
        ]);
    }

    public static function products(WP_REST_Request $request): array {
        $limit = min(max((int) $request->get_param('per_page'), 1), 100);
        $page = max((int) $request->get_param('page'), 1);
        $result = StoreOps_Product_Reader::all_products($page, $limit);
        update_option('storeops_last_successful_sync_at', current_time('mysql'), false);
        return ['items' => $result['items'], 'page' => $page, 'total' => $result['total'], 'pages' => $result['pages'], 'has_more' => $page < $result['pages']];
    }

    public static function product_variations(WP_REST_Request $request): array {
        $product = wc_get_product((int) $request['id']);
        if (!$product || !$product->is_type('variable')) {
            return ['items' => []];
        }
        $items = [];
        foreach ($product->get_children() as $variation_id) {
            $variation = wc_get_product($variation_id);
            if ($variation) {
                $items[] = StoreOps_Product_Reader::read_product($variation);
            }
        }
        return ['items' => $items];
    }

    public static function changes(): array {
        return ['changed_product_ids' => array_map('intval', array_keys((array) get_option('storeops_changed_products', [])))];
    }

    public static function ack_changes(WP_REST_Request $request): array {
        $ids = array_map('intval', (array) $request->get_param('product_ids'));
        $changed = (array) get_option('storeops_changed_products', []);
        foreach ($ids as $id) {
            unset($changed[$id]);
        }
        update_option('storeops_changed_products', $changed, false);
        return ['status' => 'ok', 'remaining' => count($changed)];
    }

    public static function changed_products(WP_REST_Request $request): array {
        $limit = min(max((int) $request->get_param('limit'), 1), 100);
        $cursor = (int) $request->get_param('cursor');
        $items = StoreOps_Product_Reader::changed_since($cursor, $limit);
        update_option('storeops_last_successful_sync_at', current_time('mysql'), false);
        return ['items' => $items, 'next_cursor' => time(), 'has_more' => count($items) >= $limit];
    }

    public static function full_sync_products(WP_REST_Request $request): array {
        $request->set_param('per_page', $request->get_param('limit'));
        return self::products($request);
    }
}
