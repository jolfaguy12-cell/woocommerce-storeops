<?php

defined('ABSPATH') || exit;

class StoreOps_Product_Reader {
    public static function read_product(WC_Product $product): array {
        $is_variation = $product->is_type('variation');
        $parent_id = $is_variation ? $product->get_parent_id() : null;
        $category_product_id = $parent_id ?: $product->get_id();
        $category_ids = wc_get_product_term_ids($category_product_id, 'product_cat');
        $category_names = wc_get_product_terms($category_product_id, 'product_cat', ['fields' => 'names']);
        $post = get_post($product->get_id());

        return [
            'woocommerce_product_id' => $is_variation ? $parent_id : $product->get_id(),
            'woocommerce_variation_id' => $is_variation ? $product->get_id() : null,
            'parent_woocommerce_product_id' => $parent_id,
            'product_type' => $is_variation ? 'variation' : $product->get_type(),
            'product_status' => $post ? $post->post_status : 'unknown',
            'product_name' => $product->get_name(),
            'variation_attributes' => $is_variation ? $product->get_attributes() : null,
            'sku' => $product->get_sku(),
            'stock_quantity' => $product->get_stock_quantity(),
            'stock_status' => $product->get_stock_status(),
            'manage_stock' => $product->managing_stock(),
            'category_ids' => array_map('intval', $category_ids),
            'category_names' => array_values(array_map('strval', $category_names)),
            'product_edit_url' => get_edit_post_link($parent_id ?: $product->get_id(), 'raw'),
            'date_created' => $product->get_date_created() ? $product->get_date_created()->date(DATE_ATOM) : null,
            'date_modified' => $product->get_date_modified() ? $product->get_date_modified()->date(DATE_ATOM) : null,
        ];
    }

    public static function all_products(int $page, int $limit): array {
        $query = new WC_Product_Query([
            'limit' => $limit,
            'page' => $page,
            'orderby' => 'ID',
            'order' => 'ASC',
            'return' => 'objects',
            'paginate' => true,
            'status' => ['publish', 'draft', 'private', 'pending', 'trash'],
            'type' => ['simple', 'variable', 'variation', 'grouped', 'external'],
        ]);

        $result = $query->get_products();
        $products = is_object($result) && isset($result->products) ? $result->products : $result;
        $items = self::flatten_products($products);

        return [
            'items' => $items,
            'total' => is_object($result) && isset($result->total) ? (int) $result->total : count($items),
            'pages' => is_object($result) && isset($result->max_num_pages) ? (int) $result->max_num_pages : 1,
        ];
    }

    public static function changed_since(int $cursor, int $limit): array {
        $query = new WC_Product_Query([
            'limit' => $limit,
            'orderby' => 'modified',
            'order' => 'ASC',
            'return' => 'objects',
            'paginate' => false,
            'status' => ['publish', 'draft', 'private', 'pending', 'trash'],
            'date_modified' => '>' . gmdate('Y-m-d H:i:s', $cursor),
        ]);

        return self::flatten_products($query->get_products());
    }

    private static function flatten_products(array $products): array {
        $items = [];
        foreach ($products as $product) {
            $items[] = self::read_product($product);
            if ($product->is_type('variable')) {
                foreach ($product->get_children() as $variation_id) {
                    $variation = wc_get_product($variation_id);
                    if ($variation) {
                        $items[] = self::read_product($variation);
                    }
                }
            }
        }

        return $items;
    }
}
