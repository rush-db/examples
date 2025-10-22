import type { NextApiRequest, NextApiResponse } from 'next'
import { db } from '@/db'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { id } = req.query as { id: string }

  try {
    const result = await db.records.findById(id)

    const data = {
      id: result.id(),
      ...result.data,
    }
    return res.status(200).json({ ok: true, data })
  } catch (e: any) {
    return res.status(500).json({ ok: false, message: e?.message || 'Error' })
  }
}
