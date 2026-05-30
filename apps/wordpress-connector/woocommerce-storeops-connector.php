<?php
/**
 * Plugin Name: WooCommerce StoreOps Connector
 * Description: Lightweight WooCommerce data connector for the WooCommerce StoreOps Python Core Server.
 * Version: 0.1.0
 * Author: WooCommerce StoreOps
 * Requires PHP: 8.0
 * Requires Plugins: woocommerce
 */

defined('ABSPATH') || exit;

define('STOREOPS_CONNECTOR_VERSION', '0.1.0');
define('STOREOPS_CONNECTOR_PATH', plugin_dir_path(__FILE__));
define('STOREOPS_CONNECTOR_URL', plugin_dir_url(__FILE__));

require_once STOREOPS_CONNECTOR_PATH . 'includes/class-security.php';
require_once STOREOPS_CONNECTOR_PATH . 'includes/class-product-reader.php';
require_once STOREOPS_CONNECTOR_PATH . 'includes/class-change-tracker.php';
require_once STOREOPS_CONNECTOR_PATH . 'includes/class-rest-api.php';
require_once STOREOPS_CONNECTOR_PATH . 'includes/class-admin-settings.php';

add_action('plugins_loaded', static function (): void {
    if (!class_exists('WooCommerce')) {
        return;
    }

    StoreOps_Admin_Settings::init();
    StoreOps_REST_API::init();
    StoreOps_Change_Tracker::init();
});
