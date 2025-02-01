# Express RushDB SDK Demo

This demo application showcases how to use [RushDB](https://rushdb.com) — an open‑source database built on Neo4j—in combination with Express and TypeScript to quickly prototype a REST API without authorization, authentication modules.

## Technology Stack

- **Node.js**
- **Express**
- **TypeScript**
- **RushDB SDK**
- **dotenv**
- **ts-node & nodemon**

## Endpoints Structure

This demo implements a hierarchical resource structure: **Company** → **Department** → **Employee**. Below is the outline of endpoints:

### Company
- `POST /companies`  
  Create a new company.
- `GET /companies/:companyId`  
  Retrieve a company by its ID.
- `PUT /companies/:companyId`  
  Update a company.
- `DELETE /companies/:companyId`  
  Delete a company.
- `GET /companies/:companyId/details`  
  Retrieve detailed company information with aggregated data (e.g., the company structure with nested departments, employees).

### Department (Nested within Company)
- `POST /companies/:companyId/departments`  
  Create a new department for the company.
- `GET /companies/:companyId/departments`  
  Get the list of departments for the company.
- `GET /companies/:companyId/departments/:departmentId`  
  Retrieve a department by its ID.
- `PUT /companies/:companyId/departments/:departmentId`  
  Update a department.
- `DELETE /companies/:companyId/departments/:departmentId`  
  Delete a department.
- `GET /companies/:companyId/departments/:departmentId/stats`  
  Get aggregated statistics for a department (e.g., aggregates on salary and employee count).

### Employee (Nested within Department)
- `POST /companies/:companyId/departments/:departmentId/employees`  
  Create new employee(s) for the department.
- `GET /companies/:companyId/departments/:departmentId/employees/search`  
  Search for employees by name and salary range.
- `GET /companies/:companyId/departments/:departmentId/employees`  
  Retrieve the list of employees in the department.
- `GET /companies/:companyId/departments/:departmentId/employees/:employeeId`  
  Retrieve an employee by ID.
- `PUT /companies/:companyId/departments/:departmentId/employees/:employeeId`  
  Update an employee.
- `DELETE /companies/:companyId/departments/:departmentId/employees/:employeeId`  
  Delete an employee.

## Postman Collection

For testing the API, please use the [Postman collection](./express-demo.postman_collection) located in the project root.

## Data Structures

### Company

```typescript
export interface Employee {
  name: string;
  position: string;
  email: string;
  dob: string;
  salary: number;
}
```

### Department

```typescript
export interface Department {
  name: string;
  description: string;
}
```

### Employee

```typescript
export interface Company {
  name: string;
  address: string;
  foundedAt: string;
  rating: number;
}
```

## Package.json

Below is an example of the `package.json` for this demo:

```json
{
  "name": "express-rushdb-sdk",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "build": "npx tsc",
    "start": "node dist/index.js",
    "dev": "nodemon --exec ts-node src/index.ts"
  },{
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "printWidth": 80,
  "bracketSpacing": true,
  "semi": true,
  "importOrder": ["^react$", "<THIRD_PARTY_MODULES>", "^@/.*", "^[./]"],
  "importOrderSeparation": true,
  "importOrderSortSpecifiers": true
}
  "keywords": [],
  "author": "",
  "license": "ISC",
  "description": "",
  "dependencies": {
    "@rushdb/javascript-sdk": "^0.9.5",
    "dotenv": "^16.4.7",
    "express": "^4.21.2"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^22.10.10",
    "concurrently": "^9.1.2",
    "nodemon": "^3.1.9",
    "ts-node": "^10.9.2",
    "typescript": "^5.7.3"
  }
}
