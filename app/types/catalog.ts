/** Каталог / типи продуктів */
export interface ProductType {
  catalog_id: number;
  product_type: string;
  catalog_photo?: string | null;
}

/** Товар у каталозі (product_price може бути числом або рядком типу "1 - 150, 3 - 400 ₴") */
export interface Product {
  id: number;
  catalog_id: number;
  product_type: string;
  product_name: string;
  product_description: string | null;
  product_price: number | string;
  product_photo: string | null;
  payment_type: string;
  product_badge?: string;
}
