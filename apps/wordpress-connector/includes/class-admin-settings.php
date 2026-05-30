<?php

defined('ABSPATH') || exit;

class StoreOps_Admin_Settings {
    public static function init(): void {
        add_action('admin_menu', [__CLASS__, 'menu']);
        add_action('admin_init', [__CLASS__, 'register_settings']);
    }

    public static function menu(): void {
        add_options_page('WooCommerce StoreOps', 'StoreOps Connector', 'manage_woocommerce', 'storeops-connector', [__CLASS__, 'render']);
    }

    public static function register_settings(): void {
        foreach (['storeops_enabled', 'storeops_server_url', 'storeops_api_key', 'storeops_hmac_secret', 'storeops_low_stock_threshold', 'storeops_social_networks', 'storeops_telegram_enabled'] as $option) {
            register_setting('storeops_connector', $option);
        }
    }

    public static function render(): void {
        ?>
        <div class="wrap">
            <h1>WooCommerce StoreOps Connector</h1>
            <p>This lightweight connector exposes WooCommerce inventory data to the Python Core Server. Heavy processing, Telegram, and reports are intentionally not run in WordPress.</p>
            <form method="post" action="options.php">
                <?php settings_fields('storeops_connector'); ?>
                <table class="form-table" role="presentation">
                    <tr><th>Enable connector</th><td><input type="checkbox" name="storeops_enabled" value="1" <?php checked(get_option('storeops_enabled'), 1); ?>></td></tr>
                    <tr><th>Server 2 URL</th><td><input class="regular-text" type="url" name="storeops_server_url" value="<?php echo esc_attr(get_option('storeops_server_url', '')); ?>"></td></tr>
                    <tr><th>API key</th><td><input class="regular-text" type="password" name="storeops_api_key" value="<?php echo esc_attr(get_option('storeops_api_key', '')); ?>"></td></tr>
                    <tr><th>HMAC secret</th><td><input class="regular-text" type="password" name="storeops_hmac_secret" value="<?php echo esc_attr(get_option('storeops_hmac_secret', '')); ?>"><p class="description">Used to verify signed Core Server requests.</p></td></tr>
                    <tr><th>Default low-stock threshold</th><td><input type="number" min="0" name="storeops_low_stock_threshold" value="<?php echo esc_attr(get_option('storeops_low_stock_threshold', 2)); ?>"></td></tr>
                    <tr><th>Social networks</th><td><label><input type="checkbox" name="storeops_social_networks[]" value="telegram"> Telegram</label> <label><input type="checkbox" name="storeops_social_networks[]" value="email"> Email</label></td></tr>
                    <tr><th>Telegram enabled in Core</th><td><input type="checkbox" name="storeops_telegram_enabled" value="1" <?php checked(get_option('storeops_telegram_enabled'), 1); ?>><p class="description">Bot token is stored only on the Python Core Server.</p></td></tr>
                </table>
                <?php submit_button(); ?>
            </form>
            <button class="button" disabled>Connection test (Phase 1 UI placeholder)</button>
        </div>
        <?php
    }
}
