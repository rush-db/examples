import { Router } from 'express';
import {
  createCompany,
  deleteCompany,
  getCompanyById,
  getCompanyStructureById,
  updateCompany,
} from '../controllers/companyController';
import departmentRoutes from './departmentRoutes';

const router = Router();

router.post('/', createCompany);
router.put('/:companyId', updateCompany);
router.delete('/:companyId', deleteCompany);
router.get('/:companyId', getCompanyById);
router.get('/:companyId/details', getCompanyStructureById);

router.use('/:companyId/departments', departmentRoutes);

export default router;
