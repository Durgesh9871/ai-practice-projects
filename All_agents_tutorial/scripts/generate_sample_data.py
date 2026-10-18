import numpy as np
import pandas as pd
import os


print("Generating sample data...")

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ecommerce_demo")


# Set seed for reproducibility
RNG = np.random.default_rng(seed=7)

CATEGORIES = ["Electronics", "Beauty", "Home", "Fashion"]
BASE_PRICE = {"Electronics": 220.0, "Beauty": 35.0, "Home": 90.0, "Fashion": 60.0}
REGIONS = ["North", "South", "East", "West"]


N_CUSTOMERS = 800
N_PRODUCTS_PER_CATEGORY = 15
MONTHS = pd.date_range("2025-01-01", periods=6, freq="MS")  # Jan .. Jun 2025
DECLINE_MONTH = MONTHS[-1]  # June: the promotion month
ORDERS_PER_MONTH = 1400


def build_customers() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [f"C{i:04d}" for i in range(N_CUSTOMERS)],
            "region": RNG.choice(REGIONS, size=N_CUSTOMERS),
            "signup_date": pd.to_datetime("2023-01-01")
            + pd.to_timedelta(RNG.integers(0, 700, size=N_CUSTOMERS), unit="D"),
        }
    )


def build_products() -> pd.DataFrame:
    records = []
    for cat in CATEGORIES:
        for i in range(N_PRODUCTS_PER_CATEGORY):
            price = BASE_PRICE[cat] * RNG.uniform(0.85, 1.35)
            records.append(
                {
                    "product_id": f"P{cat[:2].upper()}{i:03d}",
                    "category": cat,
                    "base_price": round(price, 2),
                }
            )
    return pd.DataFrame(records)


def build_orders(customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    order_id = 0

    for month_start in MONTHS:
        is_decline_month = month_start == DECLINE_MONTH
        days_in_month = pd.Period(month_start, freq="M").days_in_month

        for _ in range(ORDERS_PER_MONTH):
            customer = customers.iloc[RNG.integers(0, len(customers))]
            product = products.iloc[RNG.integers(0, len(products))]
            category = product["category"]

            order_day = RNG.integers(0, days_in_month)
            order_date = month_start + pd.Timedelta(days=int(order_day))

            quantity = int(RNG.integers(1, 4))

            discount_pct = float(np.clip(RNG.normal(0.05, 0.02), 0.0, 0.15))

            if is_decline_month and category == "Fashion":
                discount_pct = float(np.clip(RNG.normal(0.35, 0.05), 0.20, 0.50))

            unit_price = round(product["base_price"] * (1 - discount_pct), 2)

            rows.append(
                {
                    "order_id": f"O{order_id:06d}",
                    "customer_id": customer["customer_id"],
                    "product_id": product["product_id"],
                    "order_date": order_date.date().isoformat(),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_pct": round(discount_pct, 4),
                }
            )
            order_id += 1

    return pd.DataFrame(rows)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    customers = build_customers()
    products = build_products()
    orders = build_orders(customers, products)

    customers.to_csv(os.path.join(OUT_DIR, "customers.csv"), index=False)
    products.to_csv(os.path.join(OUT_DIR, "products.csv"), index=False)
    orders.to_csv(os.path.join(OUT_DIR, "orders.csv"), index=False)

    print(
        f"Wrote {len(customers)} customers, {len(products)} products, {len(orders)} orders to {OUT_DIR}"
    )


if __name__ == "__main__":
    main()
