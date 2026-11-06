# Vite React useForm Example

A comprehensive form application built with React, TypeScript, and Vite, demonstrating advanced form handling with validation and data persistence.

## Features

- **Advanced Form Management**: Built with React Hook Form for efficient form state management
- **Schema Validation**: Uses Zod for robust client-side validation
- **TypeScript**: Fully typed with TypeScript for better development experience
- **Real-time Validation**: Form validation occurs as you type
- **Data Persistence**: Stores form submissions in RushDB
- **Responsive Design**: Clean, modern UI that works on all devices
- **Comprehensive Form Fields**: Includes various input types and complex nested data structures

## Form Sections

The application includes a multi-section form with:

### Personal Information

- First Name, Last Name
- Email, Phone Number
- Date of Birth

### Address Information

- Street Address, City, State
- ZIP Code, Country

### Professional Information

- Company, Position
- Experience Level (Entry to Executive)
- Salary, Skills (dynamic array)

### Preferences

- Newsletter subscription
- Notifications settings
- Public profile visibility
- Data sharing preferences

### Additional Information

- Bio (up to 500 characters)
- Website, LinkedIn, GitHub URLs

## Tech Stack

- **Frontend Framework**: React 19.1.0
- **Build Tool**: Vite 7.0.0
- **Language**: TypeScript 5.8.3
- **Form Management**: React Hook Form 7.58.1
- **Validation**: Zod 3.25.67 with @hookform/resolvers
- **Database**: RushDB JavaScript SDK 1.7.0
- **Linting**: ESLint 9.29.0

## Prerequisites

- Node.js (version 18 or higher)
- npm or yarn
- RushDB account and API credentials

## Environment Setup

Create a `.env` file in the root directory with your RushDB credentials:

```env
VITE_RUSHDB_API_TOKEN=your_rushdb_api_token_here
VITE_RUSHDB_URL=your_rushdb_url_here
```

## Installation

1. Clone the repository or navigate to the project directory:

   ```bash
   cd vite-react-useForm
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Set up your environment variables (see Environment Setup above)

4. Start the development server:

   ```bash
   npm run dev
   ```

5. Open your browser and navigate to `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build the project for production
- `npm run lint` - Run ESLint to check for code issues
- `npm run preview` - Preview the production build locally

## Project Structure

```
src/
├── App.tsx          # Main application component with form logic
├── App.css          # Application styles
├── db.ts            # RushDB configuration
├── main.tsx         # Application entry point
├── index.css        # Global styles
└── vite-env.d.ts    # Vite environment types
```

## Key Features Explained

### Form Validation

The application uses Zod schemas for comprehensive validation:

- Required field validation
- Email format validation
- URL validation for social links
- Minimum/maximum length constraints
- Custom validation messages

### Dynamic Skills Management

Users can dynamically add and remove skills with real-time validation and duplicate prevention.

### Real-time Form State

The form provides immediate feedback with:

- Real-time validation as you type
- Visual error indicators
- Form submission status updates
- Success/error messaging

### Data Persistence

All form submissions are stored in RushDB with additional metadata:

- Submission timestamp
- User agent information
- Form version tracking

## Usage Example

1. Fill out the comprehensive form with your information
2. Watch real-time validation feedback as you type
3. Add multiple skills using the dynamic skills section
4. Set your preferences using checkboxes
5. Submit the form to see success confirmation
6. Data is automatically saved to your RushDB instance

## Development Notes

- The form uses `mode: "onChange"` for real-time validation
- All form fields are strongly typed with TypeScript
- Error handling includes both client-side validation and server errors
- The form resets automatically after successful submission

## Contributing

1. Ensure all new code follows the existing TypeScript patterns
2. Add appropriate Zod validation for any new form fields
3. Test form validation and submission thoroughly
4. Update this README if adding new features

## License

This project is provided as an example and learning resource.
