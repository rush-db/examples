# Nuxt 3 RushDB Auth Example

A minimal Nuxt 3 application demonstrating user registration, login, protected routes, and data persistence using RushDB.  
Passwords are salted with HMAC-SHA256 (using an environment secret) and stored in RushDB. JWT tokens are set as HTTP-only cookies.

## Features

- **User Registration**: Check username uniqueness, hash passwords, store in RushDB  
- **User Login**: Verify credentials via RushDB, issue JWT token via HTTP-only cookie  
- **Protected Route**: `/users` page showing all registered users stored in RushDB, highlighting the current user  
- **Logout**: Clear authentication cookie  
- **Client + Server**: All in one Nuxt 3 project (API routes under `server/api/`)  
- **TypeScript + Tailwind CSS**

## Prerequisites

- Node.js ≥ 18  
- RushDB API token (from https://app.rushdb.com/)  
- `npm` or `yarn`

## Getting Started

### 1. Clone & Install

```bash
git clone https://github.com/rush-db/examples.git
cd examples/nuxt-auth
npm install
```

### 2. Environment

Copy `.env.example` to `.env` and fill in your values:

```ini
# .env
PORT=3000
RUSHDB_API_TOKEN=your_rushdb_token
RUSHDB_BASE_URL=https://api.rushdb.com/api/v1
AUTH_SECRET=your_hmac_secret
```

### 3. Scripts

```bash
npm run dev    # start in development mode (hot reload)
npm run build  # compile for production
npm run start  # run production build
```

## Project Structure

```
nuxt-auth/
├── .env.example
├── package.json
├── nuxt.config.ts
├── tailwind.config.js
├── tsconfig.json
└── src/
    ├── index.d.ts
    ├── composables/
    │   └── useDb.ts           # RushDB client factory
    ├── middleware/
    │   └── auth.client.ts     # Route guard for authentication
    ├── pages/
    │   ├── login.vue          # Login form
    │   ├── register.vue       # Registration form
    │   ├── users.vue          # Protected users list
    │   └── [...404].vue       # Handle 404 pages
    ├── server/
    │   └── api/
    │       ├── login.post.ts
    │       ├── logout.post.ts
    │       ├── register.post.ts
    │       └── users.get.ts
    └── shared/
        └── models/
            └── index.ts        # `UserModel` definition
```

## API Endpoints

### `POST /api/register`

- Body: `{ username, password }`  
- Responses:  
  - `200 { success: true }`  
  - `409 Username already exists`  
  - `400 Username & password required`

### `POST /api/login`

- Body: `{ username, password }`  
- Sets `auth_token` HTTP-only cookie  
- Responses:  
  - `200 { success: true }`  
  - `401 Invalid credentials`  
  - `400 Username & password required`

### `POST /api/logout`

- Clears `auth_token` cookie  
- Response: `200 { success: true }`

### `GET /api/users`

- Requires valid `auth_token` cookie  
- Returns `{ users: string[], current: string }`

## Pages & Routing

- `/register` — registration form  
- `/login` — login form  
- `/users` — protected user list (middleware enforces authentication)

Nuxt 3 auto-generates these routes from the `pages/` directory.

## Tailwind

- **UI** styled with Tailwind CSS (see `tailwind.config.js`)

## Authentication Flow

1. **Register** → check uniqueness → store username + hashed password  
2. **Login** → verify password hash → issue JWT in HTTP-only cookie  
3. **Protected Pages** → middleware reads cookie (SSR & client) → redirects if missing/invalid  
4. **Logout** → cookie max-age=0

## Customization

- Change hashing algorithm or add salt rounds  
- Extend `UserModel` in `shared/models/user.ts`  
- Adjust JWT expiration or cookie flags in `server/api/login.post.ts`  

---

Happy building with RushDB and Nuxt!
