import type { NextApiRequest, NextApiResponse } from 'next'
import { db } from '@/db'

export default async function handler(
  _req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    const result = await db.records.find({
      labels: ['CATEGORY'],

      /* Add itemsCount aggregation from related items */
      // where: {
      //   ITEM: {
      //     $alias: '$item',
      //   },
      // },
      // aggregate: {
      //   itemsCount: { fn: 'count', alias: '$item' },
      // },
    })

    const data = result.data.map((r) => ({
      id: r.id(),
      ...r.data,
    }))

    return res.status(200).json({ ok: true, data })
  } catch (e: any) {
    return res.status(500).json({ ok: false, message: e?.message || 'Error' })
  }
}
