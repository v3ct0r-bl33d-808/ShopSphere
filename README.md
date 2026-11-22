# ShopSphere — Smart Shopping & Inventory Management System

Flask + MySQL e-commerce demonstration for CBSE Class XII Informatics Practices.

## Setup
1. Install Python 3.10+ and MySQL.
2. Clone: `git clone https://github.com/v3ct0r-bl33d-808/ShopSphere.git`
3. `cd ShopSphere`
4. Create and activate a virtual environment: `python -m venv .venv`
5. Install dependencies: `pip install -r requirements.txt`
6. Create the schema: `mysql -u root -p < database/schema.sql`
7. Set the database environment variables shown in `.env.example`. The example file is a template; export the values in your shell or load them with python-dotenv.
8. Run `python seed.py` then `python app.py`.
9. Visit http://127.0.0.1:5000.

Demo admin: `admin@shopsphere.demo` / `ChangeMe123!`. Set ADMIN_PASSWORD before running seed.py and change it before sharing. Payment options are simulation labels only; no payment credentials or real payments are processed.

## Included
- Customer registration/login, searchable catalogue, product details, session cart and order history.
- Stock-aware transactional checkout.
- Role-protected admin dashboard, product/inventory management and order-status management.
- Pandas Series/DataFrame analysis and Matplotlib charts generated from actual order records.
- CSV product import and products/orders/customers/inventory exports.
- Data Analysis Lab for CBSE IP demonstration.

## CSV import
Required headers: `product_name,category_id,price,stock_quantity`. Optional: `description,discount,image_url`. Category IDs are in the categories table.

## CBSE IP mapping
- **Series:** product prices indexed by product name; `mean()`, `max()`.
- **DataFrame:** SQL result sets converted to DataFrames; `head()`, filtering and grouping.
- **SQL:** normalized tables, primary/foreign keys, JOINs, aggregates, parameterized statements and checkout transactions.
- **CSV:** Pandas `read_csv()` and `to_csv()`.
- **Visualization:** Matplotlib monthly revenue, category revenue and top-selling products based on database sales rows.

## Viva questions
1. Series? Labelled one-dimensional Pandas data structure.
2. DataFrame? Labelled two-dimensional tabular data structure.
3. Primary key? Uniquely identifies a row.
4. Foreign key? Enforces a relationship between tables.
5. JOIN? Combines related rows from tables.
6. GROUP BY? Groups rows for aggregate calculations.
7. mean()? Calculates arithmetic average.
8. head()? Returns the first DataFrame rows.
9. read_csv()? Loads CSV data into a DataFrame.
10. to_csv()? Exports data to CSV.
11. Flask? Lightweight Python web framework.
12. MySQL? Relational database management system.
13. Session? Maintains user state across requests.
14. Hashing? One-way password transformation.
15. Parameterized SQL? Passes values separately from SQL syntax.
16. Transaction? Atomic set of database operations.
17. Matplotlib? Python plotting library.
18. Inventory? Available product stock.
19. CSV? Delimited plain-text tabular format.
20. Why validate CSV? To prevent malformed records entering the database.

## Security and limitations
Before public deployment, add CSRF protection, secure cookie settings, HTTPS, rate limiting, strong secrets and a production WSGI server. Never commit `.env`. This is an educational demonstration, not a production payment platform.
