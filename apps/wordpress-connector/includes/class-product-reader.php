<?php

defined('ABSPATH') || exit;

class StoreOps_Product_Reader {
    public static function read_product(WC_Product $product): array {
        $parent_id = $product->is_type('variation') ? $product->get_parent_id() : null;
        $category_names = [];
        $category_product_id = $parent_id ?: $product->get_id();
        foreach (wc_get_product_terms($category_product_id, 'product_cat', ['fields' => 'names']) as $name) {
            $category_names[] = $name;
        }

        return [
            'product_id' => $parent_id ?: $product->get_id(),
            'variation_id' => $product->is_type('variation') ? $product->get_id() : null,
            'parent_product_id' => $parent_id,
            'name' => $product->get_name(),
            'variation_attributes' => $product->is_type('variation') ? $product->get_attributes() : null,
            'sku' => $product->get_sku(),
            'stock_quantity' => $product->get_stock_quantity(),
            'stock_status' => $product->get_stock_status(),
            'manage_stock' => $product->managing_stock(),
            'category' => implode(', ', $category_names),
            'product_edit_url' => get_edit_post_link($parent_id ?: $product->get_id(), 'raw'),
            'last_modified_at' => $product->get_date_modified() ? $product->get_date_modified()->date(DATE_ATOM) : null,
        ];
    }

    public static function changed_since(int $cursor, int $limit): array {
        $query = new WC_Product_Query([
            'limit' => $limit,
            'orderby' => 'modified',
            'order' => 'ASC',
            'return' => 'objects',
            'paginate' => false,
            'date_modified' => '>' . gmdate('Y-m-d H:i:s', $cursor),
        ]);

        $items = [];
        foreach ($query->get_products() as $product) {
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
