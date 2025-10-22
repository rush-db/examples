import type { NextApiRequest, NextApiResponse } from 'next'
import type { SearchQuery } from '@rushdb/javascript-sdk'
import { db } from '@/db'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { id } = req.query as { id: string }

  try {
    if (req.method !== 'POST') {
      res.setHeader('Allow', ['POST'])
      return res.status(405).json({ ok: false, message: 'Method Not Allowed' })
    }

    const args = (req.body as SearchQuery) || {}
    const userWhere = args?.where || {}

    const where = {
      ...userWhere,
      CATEGORY: { $id: id },
    }
    const skip = typeof args?.skip === 'number' ? args.skip : 0
    const limit = typeof args?.limit === 'number' ? args.limit : 1000

    const items = await db.records.find({
      labels: ['ITEM'],
      where,
      skip,
      limit,
    })

    const catInstance: any = await db.records.findById(id)
    const category = catInstance
      ? { id: catInstance.id(), ...catInstance.data }
      : null

    const data = {
      category,
      items: items.data.map((item) => ({
        id: item.id(),
        ...item.data,
      })),
      total: items.total,
    }

    return res.status(200).json({ ok: true, data })
  } catch (e: any) {
    return res.status(500).json({ ok: false, message: e?.message || 'Error' })
  }
}
