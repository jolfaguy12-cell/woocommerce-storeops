<?php

defined('ABSPATH') || exit;

class StoreOps_Change_Tracker {
    public static function init(): void {
        add_action('woocommerce_new_order', [__CLASS__, 'track_order_products']);
        add_action('woocommerce_order_status_changed', [__CLASS__, 'track_order_products']);
        add_action('woocommerce_product_set_stock', [__CLASS__, 'track_stock_change']);
        add_action('woocommerce_variation_set_stock', [__CLASS__, 'track_stock_change']);
        add_action('woocommerce_update_product', [__CLASS__, 'track_product_id']);
        add_action('woocommerce_update_product_variation', [__CLASS__, 'track_product_id']);
    }

    public static function track_order_products(int $order_id): void {
        $order = wc_get_order($order_id);
        if (!$order) {
            return;
        }
        foreach ($order->get_items() as $item) {
            self::track_product_id((int) ($item->get_variation_id() ?: $item->get_product_id()));
        }
    }

    public static function track_stock_change(WC_Product $product): void {
        self::track_product_id($product->get_id());
    }

    public static function track_product_id(int $product_id): void {
        $changed = get_option('storeops_changed_products', []);
        $changed[$product_id] = time();
        update_option('storeops_changed_products', $changed, false);
    }
}
