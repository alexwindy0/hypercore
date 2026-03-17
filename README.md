# Hypercore E-commerce Platform

A full-stack e-commerce platform for Hypercore - a Lagos-based gym sportswear brand selling premium men's and women's athletic wear.

## Features

### Customer-Facing Website
- **Google OAuth Authentication** - Secure, passwordless login
- **Product Catalog** - Browse by gender (Men/Women), filter by size, price, search
- **Shopping Cart** - Persistent cart with localStorage + database sync
- **Checkout Flow** - Delivery details, Paystack payment integration
- **Order Tracking** - Track order status from processing to delivery
- **User Account** - Profile management, order history, address book

### Admin Dashboard
- **Dashboard Analytics** - Sales metrics, order counts, customer stats
- **Product Management** - Add, edit, delete products with image upload
- **Order Management** - View and update order statuses
- **Customer Management** - View customer list, export to CSV
- **Inventory Alerts** - Low stock notifications

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML5, CSS3, JavaScript |
| Backend | Python Flask |
| Database | PostgreSQL (Supabase) |
| Authentication | Google OAuth 2.0 + JWT |
| Payments | Paystack API |
| Email | Resend.com |
| Image Storage | Cloudinary |

## Project Structure

```
hypercore/
├── backend/                 # Flask backend
│   ├── app.py              # Main application
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   ├── models/             # Database models
│   │   ├── database.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── cart.py
│   ├── routes/             # API routes
│   │   ├── auth.py
│   │   ├── products.py
│   │   ├── cart.py
│   │   ├── orders.py
│   │   ├── users.py
│   │   ├── admin.py
│   │   └── webhooks.py
│   ├── utils/              # Utility functions
│   │   ├── security.py
│   │   ├── jwt_utils.py
│   │   ├── validation.py
│   │   └── helpers.py
│   ├── services/           # External services
│   │   ├── paystack_service.py
│   │   ├── cloudinary_service.py
│   │   └── email_service.py
│   └── middleware/         # Middleware
│       └── error_handler.py
├── frontend/               # Frontend assets
│   ├── index.html
│   ├── shop.html
│   ├── product.html
│   ├── cart.html
│   ├── checkout.html
│   ├── account.html
│   ├── login.html
│   ├── css/
│   │   ├── styles.css
│   │   ├── header.css
│   │   ├── home.css
│   │   ├── shop.css
│   │   ├── checkout.css
│   │   ├── account.css
│   │   └── auth.css
│   ├── js/
│   │   ├── utils.js
│   │   ├── home.js
│   │   ├── shop.js
│   │   ├── product.js
│   │   ├── cart.js
│   │   ├── checkout.js
│   │   └── account.js
│   ├── admin/              # Admin dashboard
│   │   ├── index.html
│   │   ├── admin.css
│   │   └── admin.js
│   └── assets/
│       └── images/
└── docs/                   # Documentation
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- PostgreSQL database (or Supabase account)
- Google OAuth credentials
- Paystack account
- Cloudinary account
- Resend account

### Backend Setup

1. **Create virtual environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Set up database:**
The application will automatically create tables on first run.


1. **Run the server:**
```bash
python app.py
```

### Frontend Setup

The frontend is static HTML/CSS/JS. Simply serve the `frontend` folder:

```bash
cd frontend
python -m http.server 8080
```

Or deploy to any static hosting service (Vercel, Netlify, etc.)

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key
PORT=5000

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# JWT
JWT_SECRET_KEY=your-jwt-secret

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Paystack
PAYSTACK_SECRET_KEY=sk_test_...
PAYSTACK_PUBLIC_KEY=pk_test_...

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Resend Email
RESEND_API_KEY=re_...
FROM_EMAIL=Hypercore <noreply@yourdomain.com>

# Admin
ADMIN_REGISTRATION_KEY=your-admin-key

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:8080
```

## API Endpoints

### Authentication
- `POST /api/auth/google` - Google OAuth login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/profile` - Update profile

### Products
- `GET /api/products/` - List products (with filters)
- `GET /api/products/featured` - Featured products
- `GET /api/products/:id` - Get single product
- `POST /api/products/` - Create product (admin)
- `PUT /api/products/:id` - Update product (admin)
- `DELETE /api/products/:id` - Delete product (admin)

### Cart
- `GET /api/cart/` - Get cart items
- `POST /api/cart/add` - Add to cart
- `PUT /api/cart/update/:id` - Update quantity
- `DELETE /api/cart/remove/:id` - Remove item
- `DELETE /api/cart/clear` - Clear cart
- `POST /api/cart/sync` - Sync localStorage cart

### Orders
- `GET /api/orders/` - Get user orders
- `GET /api/orders/:id` - Get order details
- `POST /api/orders/checkout` - Create checkout
- `POST /api/orders/verify-payment` - Verify payment
- `GET /api/orders/track/:order_number` - Track order (public)
- `GET /api/orders/admin/all` - Get all orders (admin)
- `PUT /api/orders/admin/:id/status` - Update status (admin)

### Admin
- `GET /api/admin/dashboard` - Dashboard data
- `GET /api/admin/analytics/sales` - Sales analytics
- `GET /api/admin/analytics/products` - Top products

## Database Schema

### Users
- `id` (PK)
- `google_id` (unique)
- `email` (unique)
- `name`
- `phone`
- `address` (JSON)
- `role` (customer/admin)
- `is_active`
- `created_at`

### Products
- `id` (PK)
- `name`
- `description`
- `price`
- `sizes` (JSON array)
- `stock` (JSON object)
- `gender` (men/women)
- `category`
- `images` (JSON array)
- `is_featured`
- `is_active`
- `created_at`

### Orders
- `id` (PK)
- `order_number` (unique)
- `user_id` (FK)
- `items` (JSON)
- `subtotal`
- `delivery_fee`
- `total`
- `delivery_address` (JSON)
- `delivery_zone`
- `payment_status`
- `paystack_ref`
- `status`
- `tracking_number`
- `created_at`

### OrderItems
- `id` (PK)
- `order_id` (FK)
- `product_id` (FK)
- `quantity`
- `size`
- `price_at_time`
- `product_name`
- `product_image`

### CartItems
- `id` (PK)
- `user_id` (FK)
- `product_id` (FK)
- `quantity`
- `size`
- `created_at`

## Security Features

- HTTPS enforcement
- JWT token authentication (httpOnly cookies)
- Rate limiting (100 requests/minute)
- Input sanitization (XSS/SQL injection prevention)
- CORS whitelisting
- Security headers (CSP, HSTS, X-Frame-Options)
- File upload validation
- Admin role-based access control

## Delivery Zones & Fees

| Zone | Fee | Delivery Time |
|------|-----|---------------|
| Lagos Island | ₦2,500 | 1-2 days |
| Lagos Mainland | ₦2,000 | 1-3 days |
| Outside Lagos | ₦5,000 | 3-7 days |

## Email Notifications

- Welcome email with 10% discount code
- Order confirmation
- Payment received
- Order shipped (with tracking)
- Order delivered

## Deployment

### Backend (Render/Railway)
1. Push code to GitHub
2. Connect to Render/Railway
3. Set environment variables
4. Deploy

### Frontend (Vercel)
1. Push code to GitHub
2. Import to Vercel
3. Set build settings (static)
4. Deploy

### Database (Supabase)
1. Create Supabase project
2. Get connection string
3. Add to environment variables

## Free Tier Limits

| Service | Free Tier |
|---------|-----------|
| Render | 750 hours/month |
| Supabase | 500MB database |
| Cloudinary | 25GB storage |
| Paystack | No monthly fee (transaction fees apply) |
| Resend | 100 emails/day |
| Google OAuth | 10,000 requests/day |

## License

MIT License - feel free to use for your own projects.

## Support

For support, email support@hypercore.com.ng or create an issue on GitHub.

---

Built with 💪 in Lagos, Nigeria
