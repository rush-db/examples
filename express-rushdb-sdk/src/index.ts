import dotenv from 'dotenv';

dotenv.config();

import express from 'express';
import companyRoutes from './routes/companyRoutes';

const app = express();
const port = process.env.PORT || 3008;

app.use(express.json());

app.use('/companies', companyRoutes);

app.listen(port, () => {
  console.log(`[server]: Server is running at http://localhost:${port}`);
});
