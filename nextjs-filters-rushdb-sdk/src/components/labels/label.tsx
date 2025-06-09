import { cva, VariantProps } from 'class-variance-authority'
import { FC, ReactNode } from 'react'
import { cn } from '@/lib/utils'
import {
  labelVariants,
  labelOutlineVariants,
} from '@/components/labels/constants'

export const label = cva<{
  size: Record<string, string>
  variant: Record<string, string>
}>(
  'inline-grid shrink-0 grid-flow-col place-items-center max-w-[120px] truncate border rounded-full',
  {
    variants: {
      variant: { ...labelVariants, ...labelOutlineVariants },
      size: {
        medium: 'gap-1.5 px-3 py-1 text-xs font-medium',
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
  active = true,
  children,
  className,
  quantity,
  size,
  type = 'button',
  variant,
  ...props
}) => {
  // Determine which variant to use based on active state
  const getVariantClasses = () => {
    if (!variant || variant === 'blank')
      return active ? labelVariants.blank : labelOutlineVariants.blank

    const colorKey = variant as keyof typeof labelVariants
    return active ? labelVariants[colorKey] : labelOutlineVariants[colorKey]
  }

  return (
    <button
      className={cn(
        'inline-grid shrink-0 grid-flow-col place-items-center max-w-[120px] truncate border rounded-full gap-1.5 px-3 py-1 text-xs font-medium',
        getVariantClasses(),
        className
      )}
      type={type}
      {...props}
    >
      <span>{children}</span>
      {quantity && <span className="opacity-75">{quantity}</span>}
    </button>
  )
}

Label.displayName = 'Label'
