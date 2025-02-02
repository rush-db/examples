import { Router } from 'express';
import {
  createDepartment,
  deleteDepartment,
  getAllDepartmentsByCompany,
  getDepartmentById,
  getDepartmentStatsById,
  updateDepartment,
} from '../controllers/departmentController';
import employeeRoutes from './employeeRoutes';

const router = Router({ mergeParams: true });

router.post('/', createDepartment);
router.put('/:departmentId', updateDepartment);
router.delete('/:departmentId', deleteDepartment);
router.get('/', getAllDepartmentsByCompany);
router.get('/:departmentId', getDepartmentById);
router.get('/:departmentId/stats', getDepartmentStatsById);

router.use('/:departmentId/employees', employeeRoutes);
export default router;
