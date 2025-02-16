import { cva, VariantProps } from 'class-variance-authority'
import { FC, ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { labelVariants } from '@/components/labels/constants'

export const label = cva<{
  size: Record<string, string>
  variant: Record<string, string>
}>(
  'inline-grid shrink-0 grid-flow-col place-items-center max-w-[180px] truncate',
  {
    variants: {
      variant: labelVariants,
      size: {
        medium: 'rounded gap-2.5 p-2 text-xs font-bold',
      },
    },
    defaultVariants: {
      size: 'medium',
      variant: 'blank',
    },
  }
)

export const Label: FC<
  {
    active?: boolean
    children: ReactNode
    className?: string
    type?: HTMLButtonElement['type']
    quantity?: number | string
    onClick?: () => void
  } & VariantProps<typeof label>
> = ({
  active,
  children,
  className,
  quantity,
  size,
  type = 'button',
  variant,
  ...props
}) => {
  return (
    <button
      className={cn(
        label({ size, variant, className }),
        !active && 'opacity-50'
      )}
      type={type}
      {...props}
    >
      <span>{children}</span>
      {quantity && <span className="text-content-secondary">{quantity}</span>}
    </button>
  )
}

Label.displayName = 'Label'
