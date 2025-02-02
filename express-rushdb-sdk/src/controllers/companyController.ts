import { Request, Response } from 'express';
import { db } from '../db';
import { CompanyDto } from '../types/company';

export async function createCompany(req: Request, res: Response) {
  try {
    const company: CompanyDto = req.body;

    const result = await db.records.create('COMPANY', company);

    return res.json(result.data);
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Something went wrong' });
  }
}

export async function updateCompany(req: Request, res: Response) {
  try {
    const { companyId } = req.params;
    const updateData: CompanyDto = req.body;

    const result = await db.records.update(companyId, updateData);
    return res.json(result.data);
  } catch (error) {
    console.error('Error updating company:', error);
    return res.status(500).json({ error: 'Failed to update company' });
  }
}

export async function deleteCompany(req: Request, res: Response) {
  const tx = await db.tx.begin();
  try {
    const { companyId } = req.params;
    let employeeIds: string[] = [];
    let departmentsIds: string[] = [];

    const employeesQuery = await db.records.find(
      {
        labels: ['EMPLOYEE'],
        where: {
          DEPARTMENT: {
            COMPANY: {
              $id: companyId,
            },
          },
        },
      },
      tx
    );

    const departmentsQuery = await db.records.find(
      {
        labels: ['DEPARTMENT'],
        where: {
          COMPANY: {
            $id: companyId,
          },
        },
      },
      tx
    );

    if (employeesQuery.data?.length) {
      employeeIds = employeesQuery.data.map(({ __id }) => __id);
    }

    if (departmentsQuery.data?.length) {
      departmentsIds = departmentsQuery.data.map(({ __id }) => __id);
    }

    const resultToDelete = [
      companyId,
      ...(employeeIds?.length ? [...employeeIds] : []),
      ...(departmentsIds?.length ? [...departmentsIds] : []),
    ];

    const result = await db.records.deleteById(resultToDelete, tx);
    await tx.commit();

    return res.json(result);
  } catch (error) {
    console.error('Error deleting company:', error);
    await tx.rollback();
    return res.status(500).json({ error: 'Failed to delete company' });
  }
}

export async function getCompanyById(req: Request, res: Response) {
  try {
    const { companyId } = req.params;

    const result = await db.records.findUniq('COMPANY', {
      where: {
        $id: companyId,
      },
    });

    if (!result.data) {
      return res.status(404).json({ error: 'Company not found' });
    }

    return res.json(result.data);
  } catch (error) {
    console.error('Error retrieving company by ID:', error);
    return res.status(500).json({ error: 'Failed to retrieve company' });
  }
}

export async function getCompanyStructureById(req: Request, res: Response) {
  try {
    const { companyId } = req.params;

    // @ts-expect-error
    const result = await db.records.findUniq('COMPANY', {
      labels: ['COMPANY'],
      where: {
        $id: companyId,
        DEPARTMENT: {
          $alias: '$dept',
          EMPLOYEE: {
            $alias: '$emp',
          },
        },
      },
      aggregate: {
        DEPARTMENT: {
          fn: 'collect',
          alias: '$dept',
          aggregate: {
            EMPLOYEE: {
              fn: 'collect',
              alias: '$emp',
              orderBy: {
                salary: 'desc',
              },
            },
          },
        },
      },
    });

    if (!result.data) {
      return res.status(404).json({ error: 'Company not found' });
    }

    return res.json(result.data);
  } catch (error) {
    console.error('Error retrieving company details:', error);
    return res
      .status(500)
      .json({ error: 'Failed to retrieve company details' });
  }
}
