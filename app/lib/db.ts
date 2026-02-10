import path from "node:path";

type SqliteDb = {
  prepare(sql: string): { run: (...args: unknown[]) => unknown; get: (...args: unknown[]) => unknown; all: (...args: unknown[]) => unknown[] };
};
// eslint-disable-next-line @typescript-eslint/no-require-imports
const Database = require("better-sqlite3") as new (filename?: string, options?: object) => SqliteDb;

function getDbPath(): string {
  if (process.env.DATABASE_PATH) return process.env.DATABASE_PATH;
  const appDir = path.resolve(process.cwd());
  const projectRoot = path.join(appDir, "..");
  return path.join(projectRoot, "database", "data.db");
}

let db: SqliteDb | null = null;

function ensureCatalogImagesTable(database: SqliteDb) {
  try {
    database.prepare(
      "CREATE TABLE IF NOT EXISTS catalog_images (catalog_id INTEGER PRIMARY KEY, image_path TEXT)"
    ).run();
  } catch {
    // ignore
  }
}

function ensureProductBadgeColumn(database: SqliteDb) {
  try {
    const info = database.prepare("PRAGMA table_info(products)").all() as Array<{ name: string }>;
    if (!info.some((c) => c.name === "product_badge")) {
      database.prepare("ALTER TABLE products ADD COLUMN product_badge TEXT").run();
    }
  } catch {
    // ignore
  }
}

export function getDb(): SqliteDb {
  if (!db) {
    db = new Database(getDbPath(), { readonly: false });
    ensureCatalogImagesTable(db);
    ensureProductBadgeColumn(db);
  }
  return db;
}

export function getUserByTelegramId(telegramUserId: number) {
  const database = getDb();
  const row = database
    .prepare(
      "SELECT id, user_id, user_name, ref_id, join_date, discounts FROM users WHERE user_id = ?"
    )
    .get(telegramUserId) as
    | { id: number; user_id: number; user_name: string | null; ref_id: number | null; join_date: string | null; discounts: number }
    | undefined;
  return row ?? null;
}

export function getUserSubscriptions(telegramUserId: number) {
  const database = getDb();
  const rows = database
    .prepare(
      `SELECT s.id, s.user_id, s.product_id, s.start_date, s.end_date, s.status, s.product_name, p.product_photo
       FROM subscriptions s
       LEFT JOIN products p ON p.id = s.product_id
       WHERE s.user_id = ?
       ORDER BY s.end_date DESC`
    )
    .all(telegramUserId) as Array<{
    id: number;
    user_id: number;
    product_id: number;
    start_date: string;
    end_date: string;
    status: string;
    product_name: string | null;
    product_photo: string | null;
  }>;
  return rows.map((r) => ({
    id: r.id,
    user_id: r.user_id,
    product_id: r.product_id,
    start_date: r.start_date,
    end_date: r.end_date,
    active: r.status === "active" ? 1 : 0,
    product_name: r.product_name ?? null,
    product_photo: r.product_photo ?? null,
    status: r.status,
  }));
}

/** Отримати просту підписку за id та user_id (для повідомлення в групу при скасуванні). */
export function getSubscriptionByIdAndUser(
  subscriptionId: number,
  telegramUserId: number
): { id: number; product_name: string | null } | null {
  const database = getDb();
  const row = database
    .prepare("SELECT id, product_name FROM subscriptions WHERE id = ? AND user_id = ?")
    .get(subscriptionId, telegramUserId) as { id: number; product_name: string | null } | undefined;
  return row ?? null;
}

/** Скасувати підписку користувача (проста підписка). Повертає true, якщо оновлено. */
export function cancelUserSubscription(subscriptionId: number, telegramUserId: number): boolean {
  const database = getDb();
  const result = database
    .prepare("UPDATE subscriptions SET status = 'cancelled' WHERE id = ? AND user_id = ?")
    .run(subscriptionId, telegramUserId) as { changes: number };
  return result.changes > 0;
}

/** Отримати повторювану підписку за id та user_id (для скасування та повідомлення в групу). */
export function getRecurringSubscriptionByIdAndUser(
  recurringId: number,
  telegramUserId: number
): { id: number; product_name: string | null } | null {
  const database = getDb();
  const row = database
    .prepare("SELECT id, product_name FROM recurring_subscriptions WHERE id = ? AND user_id = ?")
    .get(recurringId, telegramUserId) as { id: number; product_name: string | null } | undefined;
  return row ?? null;
}

/** Скасувати повторювану підписку (деактивація, як у боті). Повертає true, якщо оновлено. */
export function cancelRecurringSubscription(recurringId: number, telegramUserId: number): boolean {
  const database = getDb();
  const result = database
    .prepare(
      "UPDATE recurring_subscriptions SET status = 'inactive', updated_at = datetime('now') WHERE id = ? AND user_id = ?"
    )
    .run(recurringId, telegramUserId) as { changes: number };
  return result.changes > 0;
}

function ensurePaymentsTempDataTable(database: SqliteDb) {
  try {
    database.prepare(
      `CREATE TABLE IF NOT EXISTS payments_temp_data (
        id INTEGER PRIMARY KEY,
        invoice_id TEXT UNIQUE,
        wallet_id TEXT,
        payment_type TEXT,
        local_payment_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`
    ).run();
  } catch {
    // ignore
  }
}

function ensureUserTokensTable(database: SqliteDb) {
  try {
    database.prepare(
      `CREATE TABLE IF NOT EXISTS user_tokens (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE,
        wallet_id TEXT UNIQUE,
        card_token TEXT,
        masked_card TEXT,
        card_type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
      )`
    ).run();
  } catch {
    // ignore
  }
}

function ensureRecurringSubscriptionsTable(database: SqliteDb) {
  try {
    database.prepare(
      `CREATE TABLE IF NOT EXISTS recurring_subscriptions (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        product_name TEXT,
        months INTEGER,
        price REAL,
        wallet_id TEXT,
        next_payment_date TEXT,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        payment_failures INTEGER DEFAULT 0
      )`
    ).run();
  } catch {
    // ignore
  }
}

/** Зберегти токен картки для помісячної підписки (як у боті). */
export function saveUserToken(
  userId: number,
  walletId: string,
  cardToken: string,
  maskedCard: string,
  cardType: string
): boolean {
  const database = getDb();
  ensureUserTokensTable(database);
  try {
    database
      .prepare(
        `INSERT OR REPLACE INTO user_tokens (user_id, wallet_id, card_token, masked_card, card_type, updated_at)
         VALUES (?, ?, ?, ?, ?, datetime('now'))`
      )
      .run(userId, walletId, cardToken, maskedCard, cardType);
    return true;
  } catch {
    return false;
  }
}

/** Створити повторювану підписку (як у боті). */
export function createRecurringSubscription(
  userId: number,
  productId: number,
  productName: string,
  months: number,
  price: number,
  walletId: string
): boolean {
  const database = getDb();
  ensureRecurringSubscriptionsTable(database);
  try {
    const nextDate = new Date();
    nextDate.setDate(nextDate.getDate() + 30 * months);
    const nextPaymentDate = nextDate.toISOString().slice(0, 19).replace("T", " ");
    database
      .prepare(
        `INSERT INTO recurring_subscriptions (user_id, product_id, product_name, months, price, wallet_id, next_payment_date)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .run(userId, productId, productName, months, price, walletId, nextPaymentDate);
    return true;
  } catch {
    return false;
  }
}

/** Додати просту підписку (одноразова оплата), як у боті. */
export function addSubscription(
  userId: number,
  productType: string,
  productId: number,
  productName: string,
  price: number,
  startDate: string,
  endDate: string,
  status: string
): boolean {
  const database = getDb();
  try {
    database
      .prepare(
        `INSERT INTO subscriptions (user_id, product_type, product_id, product_name, price, start_date, end_date, status)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .run(userId, productType, productId, productName, price, startDate, endDate, status);
    return true;
  } catch {
    return false;
  }
}

/** ref_id (партнера) користувача, якщо є. */
export function getRefIdByUser(buyerId: number): number | null {
  const database = getDb();
  const row = database.prepare("SELECT ref_id FROM users WHERE user_id = ?").get(buyerId) as { ref_id: number | null } | undefined;
  return row?.ref_id ?? null;
}

/** Ім'я користувача (username) за user_id. */
export function getUsernameByUserId(telegramUserId: number): string | null {
  const user = getUserByTelegramId(telegramUserId);
  return user?.user_name ?? null;
}

/** Нарахувати партнеру % від покупки реферала (як у боті). */
export function addPartnerCredit(
  partnerId: number,
  buyerId: number,
  purchaseAmount: number,
  productName: string,
  paymentType: string = "one_time"
): boolean {
  const database = getDb();
  try {
    const percent = getPartnerReferralPercent();
    const creditAmount = Math.round(purchaseAmount * (percent / 100) * 10) / 10;
    if (creditAmount <= 0) return true;
    database
      .prepare("UPDATE users SET partner_balance = COALESCE(partner_balance, 0) + ? WHERE user_id = ?")
      .run(creditAmount, partnerId);
    database
      .prepare(
        `INSERT INTO partner_earnings (partner_id, buyer_id, purchase_amount, credit_amount, percent, product_name, payment_type)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .run(partnerId, buyerId, purchaseAmount, creditAmount, percent, productName, paymentType);
    return true;
  } catch {
    return false;
  }
}

/** Зберегти платіж у pending (бот потім оновить статус при успіху). */
export function savePaymentInfo(
  paymentId: string,
  invoiceId: string,
  userId: number,
  productId: number,
  months: number,
  amount: number,
  status: string,
  paymentType: string
): boolean {
  const database = getDb();
  try {
    database
      .prepare(
        `INSERT INTO payments (
          payment_id, invoice_id, user_id, product_id, months, amount, status, payment_type, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`
      )
      .run(paymentId, invoiceId, userId, productId, months, amount, status, paymentType);
    return true;
  } catch {
    return false;
  }
}

/** Отримати платіж за invoice_id (для webhook при success). status потрібен, щоб не дублювати обробку. */
export function getPaymentByInvoiceId(invoiceId: string): {
  payment_id: string | null;
  user_id: number;
  product_id: number;
  months: number;
  amount: number;
  payment_type: string | null;
  status: string | null;
} | null {
  const database = getDb();
  const row = database
    .prepare(
      "SELECT payment_id, user_id, product_id, months, amount, payment_type, status FROM payments WHERE invoice_id = ?"
    )
    .get(invoiceId) as
    | {
        payment_id: string | null;
        user_id: number;
        product_id: number;
        months: number;
        amount: number;
        payment_type: string | null;
        status: string | null;
      }
    | undefined;
  return row ?? null;
}

/** Отримати тимчасові дані по local_payment_id (для підписки — wallet_id). */
export function getPaymentsTempDataByLocalPaymentId(localPaymentId: string): { wallet_id: string } | null {
  const database = getDb();
  ensurePaymentsTempDataTable(database);
  const row = database
    .prepare("SELECT wallet_id FROM payments_temp_data WHERE local_payment_id = ?")
    .get(localPaymentId) as { wallet_id: string } | undefined;
  return row ?? null;
}

/** Видалити тимчасові дані після обробки підписки. */
export function deletePaymentsTempDataByLocalPaymentId(localPaymentId: string): boolean {
  const database = getDb();
  try {
    const result = database
      .prepare("DELETE FROM payments_temp_data WHERE local_payment_id = ?")
      .run(localPaymentId) as { changes: number };
    return result.changes > 0;
  } catch {
    return false;
  }
}

/** Оновити статус платежу за invoice_id (викликається з webhook Monobank). */
export function updatePaymentStatusByInvoiceId(invoiceId: string, status: string): boolean {
  const database = getDb();
  try {
    const result = database
      .prepare("UPDATE payments SET status = ? WHERE invoice_id = ?")
      .run(status, invoiceId) as { changes: number };
    return result.changes > 0;
  } catch {
    return false;
  }
}

/** Зберегти тимчасові дані для підписки з токенізацією (бот використовує при success). */
export function insertPaymentsTempData(
  invoiceId: string,
  walletId: string,
  paymentType: string,
  localPaymentId: string
): boolean {
  const database = getDb();
  ensurePaymentsTempDataTable(database);
  try {
    database
      .prepare(
        `INSERT OR REPLACE INTO payments_temp_data (invoice_id, wallet_id, payment_type, local_payment_id)
         VALUES (?, ?, ?, ?)`
      )
      .run(invoiceId, walletId, paymentType, localPaymentId);
    return true;
  } catch {
    return false;
  }
}

/** Платежі користувача з назвою та фото товару (для профілю) */
export function getUserPaymentsForProfile(telegramUserId: number, limit: number = 50) {
  const database = getDb();
  return database
    .prepare(
      `SELECT p.payment_id, p.invoice_id, p.product_id, p.amount, p.status, p.created_at, p.payment_type,
              pr.product_name, pr.product_photo
       FROM payments p
       LEFT JOIN products pr ON pr.id = p.product_id
       WHERE p.user_id = ?
       ORDER BY p.created_at DESC LIMIT ?`
    )
    .all(telegramUserId, limit) as Array<{
    payment_id: string | null;
    invoice_id: string | null;
    product_id: number;
    amount: number;
    status: string | null;
    created_at: string | null;
    payment_type: string | null;
    product_name: string | null;
    product_photo: string | null;
  }>;
}

/** Автоплатежі по рекуррентних підписках (для профілю) */
export function getRecurringPaymentsForProfile(telegramUserId: number, limit: number = 30) {
  const database = getDb();
  return database
    .prepare(
      `SELECT sp.id, sp.subscription_id, sp.amount, sp.payment_date, sp.status, r.product_name
       FROM subscription_payments sp
       INNER JOIN recurring_subscriptions r ON r.id = sp.subscription_id AND r.user_id = ?
       WHERE sp.user_id = ?
       ORDER BY sp.payment_date DESC LIMIT ?`
    )
    .all(telegramUserId, telegramUserId, limit) as Array<{
    id: number;
    subscription_id: number;
    amount: number;
    payment_date: string | null;
    status: string | null;
    product_name: string | null;
  }>;
}

/** Повторювані підписки користувача (як get_user_recurring_subscriptions у боті), з product_photo з products. */
export function getUserRecurringSubscriptions(telegramUserId: number) {
  const database = getDb();
  return database
    .prepare(
      `SELECT r.id, r.product_name, r.months, r.price, r.next_payment_date, r.status, r.payment_failures, p.product_photo
       FROM recurring_subscriptions r
       LEFT JOIN products p ON p.id = r.product_id
       WHERE r.user_id = ?
       ORDER BY r.id DESC`
    )
    .all(telegramUserId) as Array<{
    id: number;
    product_name: string | null;
    months: number;
    price: number;
    next_payment_date: string | null;
    status: string | null;
    payment_failures: number;
    product_photo: string | null;
  }>;
}

/** Партнерський баланс користувача (реферальна програма). */
export function getPartnerBalance(telegramUserId: number): number {
  try {
    const database = getDb();
    const info = database.prepare("PRAGMA table_info(users)").all() as Array<{ name: string }>;
    if (!info.some((c) => c.name === "partner_balance")) return 0;
    const row = database
      .prepare("SELECT COALESCE(partner_balance, 0) FROM users WHERE user_id = ?")
      .get(telegramUserId) as { "COALESCE(partner_balance, 0)": number } | undefined;
    return row ? Number(row["COALESCE(partner_balance, 0)"]) : 0;
  } catch {
    return 0;
  }
}

/** Кількість запрошених (рефералів) користувача. */
export function getReferralCount(telegramUserId: number): number {
  const database = getDb();
  const row = database
    .prepare("SELECT COUNT(*) as c FROM users WHERE ref_id = ?")
    .get(telegramUserId) as { c: number };
  return row?.c ?? 0;
}

/** Відсоток нарахування з покупок рефералів. */
export function getPartnerReferralPercent(): number {
  try {
    const database = getDb();
    const row = database
      .prepare("SELECT value FROM partner_settings WHERE key = 'referral_percent'")
      .get() as { value: string } | undefined;
    if (row) {
      const n = parseFloat(row.value);
      if (!Number.isNaN(n)) return n;
    }
  } catch {
    // table may not exist
  }
  return 20;
}

/** Список рефералів партнера: user_id, user_name, join_date. */
export function getReferralsOfPartner(telegramUserId: number): Array<{ user_id: number; user_name: string | null; join_date: string | null }> {
  try {
    const database = getDb();
    return database
      .prepare("SELECT user_id, user_name, join_date FROM users WHERE ref_id = ? ORDER BY join_date DESC")
      .all(telegramUserId) as Array<{ user_id: number; user_name: string | null; join_date: string | null }>;
  } catch {
    return [];
  }
}

/** Історія нарахувань партнеру з покупок рефералів. */
export function getPartnerEarningsHistory(
  telegramUserId: number,
  limit: number = 20
): Array<{ buyer_id: number; purchase_amount: number; credit_amount: number; product_name: string | null; payment_type: string | null; created_at: string | null }> {
  try {
    const database = getDb();
    return database
      .prepare(
        `SELECT buyer_id, purchase_amount, credit_amount, product_name, payment_type, created_at
         FROM partner_earnings WHERE partner_id = ? ORDER BY created_at DESC LIMIT ?`
      )
      .all(telegramUserId, limit) as Array<{
      buyer_id: number;
      purchase_amount: number;
      credit_amount: number;
      product_name: string | null;
      payment_type: string | null;
      created_at: string | null;
    }>;
  } catch {
    return [];
  }
}

export function getProductTypes() {
  const database = getDb();
  return database
    .prepare(
      `SELECT p.catalog_id, p.product_type, c.image_path as catalog_photo
       FROM (SELECT DISTINCT catalog_id, product_type FROM products) p
       LEFT JOIN catalog_images c ON p.catalog_id = c.catalog_id
       ORDER BY p.catalog_id`
    )
    .all() as Array<{ catalog_id: number; product_type: string; catalog_photo: string | null }>;
}

export function getProductsByCatalog(catalogId: number) {
  const database = getDb();
  return database
    .prepare(
      "SELECT id, catalog_id, product_type, product_name, product_description, product_price, product_photo, payment_type, COALESCE(product_badge, '') as product_badge FROM products WHERE catalog_id = ?"
    )
    .all(catalogId) as Array<{
    id: number;
    catalog_id: number;
    product_type: string;
    product_name: string;
    product_description: string | null;
    product_price: number | string;
    product_photo: string | null;
    payment_type: string;
    product_badge: string;
  }>;
}

/** Всі товари (для головної / пошуку), обмеження для превʼю */
export function getProductsPreview(limit: number = 24) {
  const database = getDb();
  return database
    .prepare(
      "SELECT id, catalog_id, product_type, product_name, product_description, product_price, product_photo, payment_type, COALESCE(product_badge, '') as product_badge FROM products ORDER BY id LIMIT ?"
    )
    .all(limit) as Array<{
    id: number;
    catalog_id: number;
    product_type: string;
    product_name: string;
    product_description: string | null;
    product_price: number | string;
    product_photo: string | null;
    payment_type: string;
    product_badge: string;
  }>;
}

/** Максимальний catalog_id для створення нової категорії */
export function getMaxCatalogId(): number {
  const database = getDb();
  const row = database.prepare("SELECT MAX(catalog_id) as max FROM products").get() as { max: number | null };
  return row?.max ?? 0;
}

/** Додати категорію: один placeholder-товар + запис у catalog_images */
export function addCategory(
  catalogId: number,
  productType: string,
  imagePath: string | null
): boolean {
  const database = getDb();
  try {
    database
      .prepare(
        `INSERT INTO products (catalog_id, product_type, product_name, product_description, product_price, product_photo, payment_type)
         VALUES (?, ?, ?, NULL, 0, NULL, 'subscription')`
      )
      .run(catalogId, productType, productType);
    if (imagePath) {
      database
        .prepare(
          `INSERT INTO catalog_images (catalog_id, image_path) VALUES (?, ?)
           ON CONFLICT(catalog_id) DO UPDATE SET image_path = excluded.image_path`
        )
        .run(catalogId, imagePath);
    }
    return true;
  } catch {
    return false;
  }
}

/** Оновити назву категорії та/або зображення */
export function updateCategory(
  catalogId: number,
  productType: string,
  imagePath: string | null
): boolean {
  const database = getDb();
  try {
    database.prepare("UPDATE products SET product_type = ? WHERE catalog_id = ?").run(productType, catalogId);
    if (imagePath !== null) {
      database
        .prepare(
          `INSERT INTO catalog_images (catalog_id, image_path) VALUES (?, ?)
           ON CONFLICT(catalog_id) DO UPDATE SET image_path = excluded.image_path`
        )
        .run(catalogId, imagePath);
    }
    return true;
  } catch {
    return false;
  }
}

/** Видалити категорію (усі товари + зображення) */
export function deleteCategory(catalogId: number): boolean {
  const database = getDb();
  try {
    database.prepare("DELETE FROM products WHERE catalog_id = ?").run(catalogId);
    database.prepare("DELETE FROM catalog_images WHERE catalog_id = ?").run(catalogId);
    return true;
  } catch {
    return false;
  }
}

/** Додати товар (productPrice: число для одноразової оплати або рядок тарифів "1 - 150, 3 - 400" для підписки) */
export function createProduct(
  catalogId: number,
  productType: string,
  productName: string,
  productDescription: string | null,
  productPrice: number | string,
  productPhoto: string | null,
  paymentType: string
): boolean {
  const database = getDb();
  try {
    database
      .prepare(
        `INSERT INTO products (catalog_id, product_type, product_name, product_description, product_price, product_photo, payment_type)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .run(
        catalogId,
        productType,
        productName,
        productDescription,
        productPrice,
        productPhoto,
        paymentType
      );
    return true;
  } catch {
    return false;
  }
}

/** Оновити товар (product_price: число або рядок тарифів для підписки). catalog_id + product_type — зміна категорії товару. */
export function updateProduct(
  productId: number,
  data: {
    product_name?: string;
    product_description?: string | null;
    product_price?: number | string;
    product_photo?: string | null;
    payment_type?: string;
    product_badge?: string | null;
    catalog_id?: number;
    product_type?: string;
  }
): boolean {
  const database = getDb();
  try {
    const updates: string[] = [];
    const values: unknown[] = [];
    if (data.product_name !== undefined) {
      updates.push("product_name = ?");
      values.push(data.product_name);
    }
    if (data.product_description !== undefined) {
      updates.push("product_description = ?");
      values.push(data.product_description);
    }
    if (data.product_price !== undefined) {
      updates.push("product_price = ?");
      values.push(data.product_price);
    }
    if (data.product_photo !== undefined) {
      updates.push("product_photo = ?");
      values.push(data.product_photo);
    }
    if (data.payment_type !== undefined) {
      updates.push("payment_type = ?");
      values.push(data.payment_type);
    }
    if (data.product_badge !== undefined) {
      updates.push("product_badge = ?");
      values.push(data.product_badge || null);
    }
    if (data.catalog_id !== undefined) {
      updates.push("catalog_id = ?");
      values.push(data.catalog_id);
    }
    if (data.product_type !== undefined) {
      updates.push("product_type = ?");
      values.push(data.product_type);
    }
    if (updates.length === 0) return true;
    values.push(productId);
    database.prepare(`UPDATE products SET ${updates.join(", ")} WHERE id = ?`).run(...values);
    return true;
  } catch {
    return false;
  }
}

/** Видалити товар */
export function deleteProduct(productId: number): boolean {
  const database = getDb();
  try {
    database.prepare("DELETE FROM products WHERE id = ?").run(productId);
    return true;
  } catch {
    return false;
  }
}

/** Один товар за id */
export function getProductById(productId: number) {
  const database = getDb();
  return database
    .prepare(
      "SELECT id, catalog_id, product_type, product_name, product_description, product_price, product_photo, payment_type, COALESCE(product_badge, '') as product_badge FROM products WHERE id = ?"
    )
    .get(productId) as {
    id: number;
    catalog_id: number;
    product_type: string;
    product_name: string;
    product_description: string | null;
    product_price: number | string;
    product_photo: string | null;
    payment_type: string;
    product_badge: string;
  } | undefined;
}

/** Деталі товару для адміна: товар + кількість покупок, дохід */
export function getAdminProductDetail(productId: number): {
  product: {
    id: number;
    catalog_id: number;
    product_type: string;
    product_name: string;
    product_description: string | null;
    product_price: number | string;
    product_photo: string | null;
    payment_type: string;
  };
  oneTimePurchases: number;
  oneTimeRevenue: number;
  simpleSubscriptionsCount: number;
  recurringSubscriptionsCount: number;
  recurringRevenue: number;
  totalRevenue: number;
  recentPayments: Array<{
    type: "one_time";
    amount: number;
    status: string | null;
    created_at: string | null;
  }>;
  recentSubPayments: Array<{
    type: "subscription";
    amount: number;
    status: string | null;
    payment_date: string | null;
  }>;
} | null {
  const product = getProductById(productId);
  if (!product) return null;

  const database = getDb();
  const oneTime = database
    .prepare(
      "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM payments WHERE product_id = ? AND status = 'success'"
    )
    .get(productId) as { cnt: number; total: number };
  const simpleCount = (database.prepare("SELECT COUNT(*) as c FROM subscriptions WHERE product_id = ?").get(productId) as { c: number }).c;
  const recurringCount = (database.prepare("SELECT COUNT(*) as c FROM recurring_subscriptions WHERE product_id = ?").get(productId) as { c: number }).c;
  const recurringRev = database
    .prepare(
      `SELECT COALESCE(SUM(sp.amount), 0) as total FROM subscription_payments sp
       INNER JOIN recurring_subscriptions r ON sp.subscription_id = r.id
       WHERE r.product_id = ? AND sp.status = 'success'`
    )
    .get(productId) as { total: number };

  const recentPayments = database
    .prepare(
      "SELECT amount, status, created_at FROM payments WHERE product_id = ? ORDER BY created_at DESC LIMIT 15"
    )
    .all(productId) as Array<{ amount: number; status: string | null; created_at: string | null }>;
  const recentSubPayments = database
    .prepare(
      `SELECT sp.amount, sp.status, sp.payment_date FROM subscription_payments sp
       INNER JOIN recurring_subscriptions r ON sp.subscription_id = r.id
       WHERE r.product_id = ? ORDER BY sp.payment_date DESC LIMIT 15`
    )
    .all(productId) as Array<{ amount: number; status: string | null; payment_date: string | null }>;

  const oneTimePurchases = oneTime.cnt;
  const oneTimeRevenue = Number(oneTime.total);
  const recurringRevenue = Number(recurringRev.total);
  const totalRevenue = oneTimeRevenue + recurringRevenue;

  return {
    product,
    oneTimePurchases,
    oneTimeRevenue,
    simpleSubscriptionsCount: simpleCount,
    recurringSubscriptionsCount: recurringCount,
    recurringRevenue,
    totalRevenue,
    recentPayments: recentPayments.map((p) => ({
      type: "one_time" as const,
      amount: p.amount,
      status: p.status,
      created_at: p.created_at,
    })),
    recentSubPayments: recentSubPayments.map((p) => ({
      type: "subscription" as const,
      amount: p.amount,
      status: p.status,
      payment_date: p.payment_date,
    })),
  };
}

/** Статистика для адмін-дашборду */
export function getAdminStats() {
  const database = getDb();
  const totalUsers = (database.prepare("SELECT COUNT(*) as c FROM users").get() as { c: number }).c;
  const totalProducts = (database.prepare("SELECT COUNT(*) as c FROM products").get() as { c: number }).c;
  const categories = database.prepare("SELECT COUNT(DISTINCT catalog_id) as c FROM products").get() as { c: number };
  const totalSubs = (database.prepare("SELECT COUNT(*) as c FROM subscriptions").get() as { c: number }).c;
  const totalRecurring = (database.prepare("SELECT COUNT(*) as c FROM recurring_subscriptions").get() as { c: number }).c;
  const activeSubs = (database.prepare("SELECT COUNT(*) as c FROM subscriptions WHERE status = 'active'").get() as { c: number }).c;
  const activeRecurring = (database.prepare("SELECT COUNT(*) as c FROM recurring_subscriptions WHERE status = 'active'").get() as { c: number }).c;
  const paymentsRow = database.prepare("SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'success'").get() as { cnt: number; total: number };
  const subPaymentsRow = database.prepare("SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM subscription_payments WHERE status = 'success'").get() as { cnt: number; total: number };
  const todayPayments = database.prepare("SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'success' AND DATE(created_at) = DATE('now', 'localtime')").get() as { cnt: number; total: number };
  const monthPayments = database.prepare("SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'success' AND created_at >= DATE('now', 'localtime', 'start of month')").get() as { cnt: number; total: number };
  const newUsersToday = (database.prepare("SELECT COUNT(*) as c FROM users WHERE DATE(join_date) = DATE('now', 'localtime')").get() as { c: number }).c;
  const newUsersMonth = (database.prepare("SELECT COUNT(*) as c FROM users WHERE join_date >= DATE('now', 'localtime', 'start of month')").get() as { c: number }).c;
  return {
    totalUsers,
    totalProducts,
    totalCategories: categories.c,
    totalSubscriptions: totalSubs + totalRecurring,
    activeSubscriptions: activeSubs + activeRecurring,
    totalPaymentsCount: paymentsRow.cnt + subPaymentsRow.cnt,
    totalRevenue: (paymentsRow.total as number) + (subPaymentsRow.total as number),
    todayPaymentsCount: todayPayments.cnt,
    todayRevenue: todayPayments.total as number,
    monthPaymentsCount: monthPayments.cnt,
    monthRevenue: monthPayments.total as number,
    newUsersToday,
    newUsersMonth,
  };
}

/** Список користувачів для адміна */
export function getAdminUsers(limit: number, offset: number) {
  const database = getDb();
  return database
    .prepare(
      "SELECT id, user_id, user_name, ref_id, join_date, COALESCE(discounts, 0) as discounts FROM users ORDER BY id DESC LIMIT ? OFFSET ?"
    )
    .all(limit, offset) as Array<{
    id: number;
    user_id: number;
    user_name: string | null;
    ref_id: number | null;
    join_date: string | null;
    discounts: number;
  }>;
}

/** Деталі користувача: профіль + підписки + платежі */
export function getAdminUserDetail(userRowId: number): {
  user: {
    id: number;
    user_id: number;
    user_name: string | null;
    ref_id: number | null;
    join_date: string | null;
    discounts: number;
  };
  simpleSubscriptions: Array<{
    id: number;
    product_name: string | null;
    price: number;
    start_date: string | null;
    end_date: string | null;
    status: string | null;
  }>;
  recurringSubscriptions: Array<{
    id: number;
    product_name: string | null;
    months: number;
    price: number;
    next_payment_date: string | null;
    status: string | null;
    payment_failures: number;
  }>;
  payments: Array<{
    payment_id: string | null;
    amount: number;
    status: string | null;
    payment_type: string | null;
    created_at: string | null;
  }>;
  subPayments: Array<{
    id: number;
    subscription_id: number;
    amount: number;
    payment_date: string | null;
    status: string | null;
  }>;
} | null {
  const database = getDb();
  const user = database
    .prepare(
      "SELECT id, user_id, user_name, ref_id, join_date, COALESCE(discounts, 0) as discounts FROM users WHERE id = ?"
    )
    .get(userRowId) as {
    id: number;
    user_id: number;
    user_name: string | null;
    ref_id: number | null;
    join_date: string | null;
    discounts: number;
  } | undefined;
  if (!user) return null;

  const telegramUserId = user.user_id;
  const simpleSubscriptions = database
    .prepare(
      "SELECT id, product_name, price, start_date, end_date, status FROM subscriptions WHERE user_id = ? ORDER BY id DESC"
    )
    .all(telegramUserId) as Array<{
    id: number;
    product_name: string | null;
    price: number;
    start_date: string | null;
    end_date: string | null;
    status: string | null;
  }>;
  const recurringSubscriptions = database
    .prepare(
      "SELECT id, product_name, months, price, next_payment_date, status, payment_failures FROM recurring_subscriptions WHERE user_id = ? ORDER BY id DESC"
    )
    .all(telegramUserId) as Array<{
    id: number;
    product_name: string | null;
    months: number;
    price: number;
    next_payment_date: string | null;
    status: string | null;
    payment_failures: number;
  }>;
  const payments = database
    .prepare(
      "SELECT payment_id, amount, status, payment_type, created_at FROM payments WHERE user_id = ? ORDER BY created_at DESC"
    )
    .all(telegramUserId) as Array<{
    payment_id: string | null;
    amount: number;
    status: string | null;
    payment_type: string | null;
    created_at: string | null;
  }>;
  const subPayments = database
    .prepare(
      "SELECT id, subscription_id, amount, payment_date, status FROM subscription_payments WHERE user_id = ? ORDER BY payment_date DESC"
    )
    .all(telegramUserId) as Array<{
    id: number;
    subscription_id: number;
    amount: number;
    payment_date: string | null;
    status: string | null;
  }>;

  return {
    user,
    simpleSubscriptions,
    recurringSubscriptions,
    payments,
    subPayments,
  };
}

/** Список підписок (прості + рекуррентні) для адміна */
export function getAdminSubscriptions(limit: number, offset: number) {
  const database = getDb();
  const simple = database
    .prepare(
      "SELECT s.id, s.user_id, s.product_name, s.price, s.start_date, s.end_date, s.status, u.user_name FROM subscriptions s LEFT JOIN users u ON u.user_id = s.user_id ORDER BY s.id DESC LIMIT ? OFFSET ?"
    )
    .all(limit, offset) as Array<{
    id: number;
    user_id: number;
    product_name: string | null;
    price: number;
    start_date: string | null;
    end_date: string | null;
    status: string | null;
    user_name: string | null;
  }>;
  const recurring = database
    .prepare(
      "SELECT r.id, r.user_id, r.product_name, r.months, r.price, r.next_payment_date, r.status, r.payment_failures, u.user_name FROM recurring_subscriptions r LEFT JOIN users u ON u.user_id = r.user_id ORDER BY r.id DESC LIMIT ? OFFSET ?"
    )
    .all(limit, offset) as Array<{
    id: number;
    user_id: number;
    product_name: string | null;
    months: number;
    price: number;
    next_payment_date: string | null;
    status: string | null;
    payment_failures: number;
    user_name: string | null;
  }>;
  return { simple, recurring };
}

/** Деталі однієї підписки: дані + історія платежів (для рекуррентних) */
export function getAdminSubscriptionDetail(
  type: "simple" | "recurring",
  id: number
): {
  type: "simple";
  subscription: {
    id: number;
    user_id: number;
    user_name: string | null;
    product_name: string | null;
    price: number;
    start_date: string | null;
    end_date: string | null;
    status: string | null;
  };
  payments: never[];
} | {
  type: "recurring";
  subscription: {
    id: number;
    user_id: number;
    user_name: string | null;
    product_name: string | null;
    months: number;
    price: number;
    next_payment_date: string | null;
    status: string | null;
    payment_failures: number;
  };
  payments: Array<{
    id: number;
    amount: number;
    payment_date: string | null;
    status: string | null;
    invoice_id: string | null;
  }>;
} | null {
  const database = getDb();
  if (type === "simple") {
    const row = database
      .prepare(
        "SELECT s.id, s.user_id, s.product_name, s.price, s.start_date, s.end_date, s.status, u.user_name FROM subscriptions s LEFT JOIN users u ON u.user_id = s.user_id WHERE s.id = ?"
      )
      .get(id) as {
      id: number;
      user_id: number;
      product_name: string | null;
      price: number;
      start_date: string | null;
      end_date: string | null;
      status: string | null;
      user_name: string | null;
    } | undefined;
    if (!row) return null;
    return {
      type: "simple",
      subscription: {
        id: row.id,
        user_id: row.user_id,
        user_name: row.user_name,
        product_name: row.product_name,
        price: row.price,
        start_date: row.start_date,
        end_date: row.end_date,
        status: row.status,
      },
      payments: [],
    };
  }
  const row = database
    .prepare(
      "SELECT r.id, r.user_id, r.product_name, r.months, r.price, r.next_payment_date, r.status, r.payment_failures, u.user_name FROM recurring_subscriptions r LEFT JOIN users u ON u.user_id = r.user_id WHERE r.id = ?"
    )
    .get(id) as {
    id: number;
    user_id: number;
    product_name: string | null;
    months: number;
    price: number;
    next_payment_date: string | null;
    status: string | null;
    payment_failures: number;
    user_name: string | null;
  } | undefined;
  if (!row) return null;
  const payments = database
    .prepare(
      "SELECT id, amount, payment_date, status, invoice_id FROM subscription_payments WHERE subscription_id = ? ORDER BY payment_date DESC"
    )
    .all(id) as Array<{
    id: number;
    amount: number;
    payment_date: string | null;
    status: string | null;
    invoice_id: string | null;
  }>;
  return {
    type: "recurring",
    subscription: {
      id: row.id,
      user_id: row.user_id,
      user_name: row.user_name,
      product_name: row.product_name,
      months: row.months,
      price: row.price,
      next_payment_date: row.next_payment_date,
      status: row.status,
      payment_failures: row.payment_failures,
    },
    payments,
  };
}

/** Список платежів для адміна */
export function getAdminPayments(limit: number, offset: number) {
  const database = getDb();
  const payments = database
    .prepare(
      "SELECT p.payment_id, p.invoice_id, p.user_id, p.product_id, p.months, p.amount, p.status, p.payment_type, p.created_at, u.user_name FROM payments p LEFT JOIN users u ON u.user_id = p.user_id ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
    )
    .all(limit, offset) as Array<{
    payment_id: string | null;
    invoice_id: string | null;
    user_id: number;
    product_id: number;
    months: number;
    amount: number;
    status: string | null;
    payment_type: string | null;
    created_at: string | null;
    user_name: string | null;
  }>;
  const subPayments = database
    .prepare(
      "SELECT sp.id, sp.subscription_id, sp.user_id, sp.amount, sp.payment_date, sp.status, sp.invoice_id, u.user_name FROM subscription_payments sp LEFT JOIN users u ON u.user_id = sp.user_id ORDER BY sp.payment_date DESC LIMIT ? OFFSET ?"
    )
    .all(limit, offset) as Array<{
    id: number;
    subscription_id: number;
    user_id: number;
    amount: number;
    payment_date: string | null;
    status: string | null;
    invoice_id: string | null;
    user_name: string | null;
  }>;
  return { payments, subPayments };
}

/** Фінанси: дохід за період (дати в YYYY-MM-DD, локальний час БД) */
export function getAdminFinance(fromDate: string, toDate: string) {
  const database = getDb();
  const from = `${fromDate} 00:00:00`;
  const to = `${toDate} 23:59:59`;

  const payments = database
    .prepare(
      `SELECT amount, created_at, payment_type FROM payments 
       WHERE status = 'success' AND datetime(created_at) BETWEEN datetime(?) AND datetime(?) 
       ORDER BY created_at ASC`
    )
    .all(from, to) as Array<{ amount: number; created_at: string | null; payment_type: string | null }>;

  const subPayments = database
    .prepare(
      `SELECT amount, payment_date FROM subscription_payments 
       WHERE status = 'success' AND datetime(payment_date) BETWEEN datetime(?) AND datetime(?) 
       ORDER BY payment_date ASC`
    )
    .all(from, to) as Array<{ amount: number; payment_date: string | null }>;

  const totalOneTime = payments.reduce((s, p) => s + Number(p.amount), 0);
  const totalSub = subPayments.reduce((s, p) => s + Number(p.amount), 0);

  const byDay: Record<string, { date: string; oneTime: number; subscription: number; total: number }> = {};
  payments.forEach((p) => {
    const d = p.created_at ? p.created_at.slice(0, 10) : "";
    if (!d) return;
    if (!byDay[d]) byDay[d] = { date: d, oneTime: 0, subscription: 0, total: 0 };
    byDay[d].oneTime += Number(p.amount);
    byDay[d].total += Number(p.amount);
  });
  subPayments.forEach((p) => {
    const d = p.payment_date ? p.payment_date.slice(0, 10) : "";
    if (!d) return;
    if (!byDay[d]) byDay[d] = { date: d, oneTime: 0, subscription: 0, total: 0 };
    byDay[d].subscription += Number(p.amount);
    byDay[d].total += Number(p.amount);
  });

  const daily = Object.keys(byDay)
    .sort()
    .map((date) => byDay[date]);

  return {
    fromDate,
    toDate,
    totalRevenue: totalOneTime + totalSub,
    totalOneTime,
    totalSubscription: totalSub,
    paymentsCount: payments.length,
    subPaymentsCount: subPayments.length,
    daily,
  };
}

