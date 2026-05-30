<?php

defined('ABSPATH') || exit;

class StoreOps_Admin_Settings {
    private const CAPABILITY = 'manage_woocommerce';

    public static function init(): void {
        add_action('admin_menu', [__CLASS__, 'menu']);
        add_action('admin_post_storeops_save_settings', [__CLASS__, 'save_settings']);
        add_action('admin_post_storeops_test_connection', [__CLASS__, 'test_connection']);
        add_action('admin_notices', [__CLASS__, 'admin_notices']);
    }

    public static function menu(): void {
        add_submenu_page('woocommerce', 'WooCommerce StoreOps Connector', 'StoreOps Connector', self::CAPABILITY, 'storeops-connector', [__CLASS__, 'render']);
    }

    public static function save_settings(): void {
        if (!current_user_can(self::CAPABILITY)) {
            wp_die(esc_html__('You do not have permission to manage StoreOps settings.', 'woocommerce-storeops'));
        }

        check_admin_referer('storeops_save_settings');

        $server_url = isset($_POST['storeops_server_url']) ? esc_url_raw(wp_unslash($_POST['storeops_server_url'])) : '';
        if ($server_url !== '' && !wp_http_validate_url($server_url)) {
            self::redirect_with_notice('settings_error');
        }

        update_option('storeops_enabled', isset($_POST['storeops_enabled']) ? 1 : 0, false);
        update_option('storeops_server_url', $server_url, false);
        update_option('storeops_api_key', isset($_POST['storeops_api_key']) ? sanitize_text_field(wp_unslash($_POST['storeops_api_key'])) : '', false);
        update_option('storeops_hmac_secret', isset($_POST['storeops_hmac_secret']) ? sanitize_text_field(wp_unslash($_POST['storeops_hmac_secret'])) : '', false);

        self::redirect_with_notice('settings_saved');
    }

    public static function test_connection(): void {
        if (!current_user_can(self::CAPABILITY)) {
            wp_die(esc_html__('You do not have permission to test StoreOps settings.', 'woocommerce-storeops'));
        }

        check_admin_referer('storeops_test_connection');

        $server_url = trailingslashit((string) get_option('storeops_server_url', ''));
        if ($server_url === '/' || !wp_http_validate_url($server_url)) {
            update_option('storeops_last_failed_connection_at', current_time('mysql'), false);
            self::redirect_with_notice('test_invalid_url');
        }

        $response = wp_remote_get($server_url . 'health', [
            'timeout' => 10,
            'headers' => [
                'Accept' => 'application/json',
                'User-Agent' => 'WooCommerce StoreOps Connector/' . STOREOPS_CONNECTOR_VERSION,
            ],
        ]);

        if (is_wp_error($response)) {
            update_option('storeops_last_failed_connection_at', current_time('mysql'), false);
            self::redirect_with_notice('test_failed');
        }

        $status_code = (int) wp_remote_retrieve_response_code($response);
        if ($status_code >= 200 && $status_code < 300) {
            update_option('storeops_last_successful_connection_at', current_time('mysql'), false);
            self::redirect_with_notice('test_success');
        }

        update_option('storeops_last_failed_connection_at', current_time('mysql'), false);
        self::redirect_with_notice('test_failed');
    }

    public static function admin_notices(): void {
        if (!isset($_GET['page']) || $_GET['page'] !== 'storeops-connector' || !isset($_GET['storeops_notice'])) {
            return;
        }

        $notice = sanitize_key(wp_unslash($_GET['storeops_notice']));
        $messages = [
            'settings_saved' => ['success', 'StoreOps connector settings saved.'],
            'settings_error' => ['error', 'StoreOps settings could not be saved. Check the Core Server URL.'],
            'test_success' => ['success', 'Connection test succeeded.'],
            'test_failed' => ['error', 'Connection test failed. Confirm the Core Server URL, HTTPS, firewall, and service health.'],
            'test_invalid_url' => ['error', 'Connection test failed because the Core Server URL is missing or invalid.'],
        ];

        if (!isset($messages[$notice])) {
            return;
        }

        [$class, $message] = $messages[$notice];
        printf('<div class="notice notice-%1$s is-dismissible"><p>%2$s</p></div>', esc_attr($class), esc_html($message));
    }

    public static function render(): void {
        if (!current_user_can(self::CAPABILITY)) {
            wp_die(esc_html__('You do not have permission to manage StoreOps settings.', 'woocommerce-storeops'));
        }

        $enabled = (bool) get_option('storeops_enabled', false);
        $server_url = (string) get_option('storeops_server_url', '');
        $api_key = (string) get_option('storeops_api_key', '');
        $hmac_secret = (string) get_option('storeops_hmac_secret', '');
        $last_connection = (string) get_option('storeops_last_successful_connection_at', 'Never');
        $last_failed_connection = (string) get_option('storeops_last_failed_connection_at', 'Never');
        $last_sync = (string) get_option('storeops_last_successful_sync_at', 'Not available yet');
        ?>
        <div class="wrap">
            <h1>WooCommerce StoreOps Connector</h1>
            <p>This lightweight connector only authenticates the Python 3 Core Server, exposes required WooCommerce data, tracks changed product IDs, and reports connection status. Inventory rules, Telegram, reports, and business settings live in the Core Server dashboard.</p>

            <h2>Connector Status</h2>
            <table class="widefat striped" style="max-width: 760px;">
                <tbody>
                    <tr><th scope="row">Status</th><td><?php echo $enabled ? '<strong style="color: #008a20;">Enabled</strong>' : '<strong style="color: #b32d2e;">Disabled</strong>'; ?></td></tr>
                    <tr><th scope="row">Core Server URL</th><td><?php echo $server_url ? esc_html($server_url) : '<em>Not configured</em>'; ?></td></tr>
                    <tr><th scope="row">Last successful ping</th><td><?php echo esc_html($last_connection); ?></td></tr>
                    <tr><th scope="row">Last failed ping</th><td><?php echo esc_html($last_failed_connection); ?></td></tr>
                    <tr><th scope="row">Last successful sync</th><td><?php echo esc_html($last_sync); ?></td></tr>
                </tbody>
            </table>

            <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" style="margin-top: 24px;">
                <?php wp_nonce_field('storeops_save_settings'); ?>
                <input type="hidden" name="action" value="storeops_save_settings">
                <table class="form-table" role="presentation">
                    <tr><th scope="row">Connector enabled</th><td><label><input type="checkbox" name="storeops_enabled" value="1" <?php checked($enabled); ?>> Enable secure StoreOps REST endpoints</label></td></tr>
                    <tr><th scope="row"><label for="storeops_server_url">Core Server URL</label></th><td><input id="storeops_server_url" class="regular-text" type="url" name="storeops_server_url" value="<?php echo esc_attr($server_url); ?>" placeholder="https://storeops.example.com/"></td></tr>
                    <tr><th scope="row"><label for="storeops_api_key">API key</label></th><td><input id="storeops_api_key" class="regular-text" type="password" autocomplete="new-password" name="storeops_api_key" value="<?php echo esc_attr($api_key); ?>"></td></tr>
                    <tr><th scope="row"><label for="storeops_hmac_secret">HMAC secret</label></th><td><input id="storeops_hmac_secret" class="regular-text" type="password" autocomplete="new-password" name="storeops_hmac_secret" value="<?php echo esc_attr($hmac_secret); ?>"><p class="description">Used to verify signed Core Server requests. Leave empty only for local development.</p></td></tr>
                </table>
                <?php submit_button('Save Connector Settings'); ?>
            </form>

            <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                <?php wp_nonce_field('storeops_test_connection'); ?>
                <input type="hidden" name="action" value="storeops_test_connection">
                <?php submit_button('Test connection', 'secondary'); ?>
            </form>
        </div>
        <?php
    }

    private static function redirect_with_notice(string $notice): void {
        wp_safe_redirect(add_query_arg([
            'page' => 'storeops-connector',
            'storeops_notice' => sanitize_key($notice),
        ], admin_url('admin.php')));
        exit;
    }
}
