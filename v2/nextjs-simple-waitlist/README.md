# Next.js Simple Waitlist

A simple waitlist application built with Next.js and RushDB that allows users to join a waitlist by submitting their email address.

## Features

- Clean, responsive waitlist form
- Email validation
- RushDB integration for data storage
- Success/error feedback
- Dark mode support

## Setup

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Configure RushDB:**

   - Copy `.env.local.example` to `.env.local`
   - Add your RushDB API key:
     ```
     RUSHDB_API_KEY=your_rushdb_api_key_here
     ```

3. **Run the development server:**

   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Visit [http://localhost:3000](http://localhost:3000) to see the waitlist form.

## API Endpoint

The application includes a REST API endpoint at `/api/waitlist` that:

- Accepts POST requests with email in the request body
- Validates email format
- Stores emails in RushDB with the label "Waitlist"
- Returns success/error responses

### Example API Usage

```javascript
fetch("/api/waitlist", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ email: "user@example.com" }),
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

## Project Structure

```
src/
├── app/
│   ├── api/
│   │   └── waitlist/
│   │       └── route.ts      # API endpoint for waitlist
│   ├── globals.css           # Global styles
│   ├── layout.tsx            # Root layout
│   └── page.tsx              # Main waitlist page
└── ...
```

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
