import { Router } from 'express';
import {
  createEmployee,
  deleteEmployee,
  getAllEmployeesByDepartment,
  getEmployeeById,
  searchEmployee,
  updateEmployee,
} from '../controllers/employeeController';

const router = Router({ mergeParams: true });

router.post('/', createEmployee);
router.put('/:employeeId', updateEmployee);
router.delete('/:employeeId', deleteEmployee);
router.get('/search', searchEmployee);
router.get('/', getAllEmployeesByDepartment);
router.get('/:employeeId', getEmployeeById);

export default router;
