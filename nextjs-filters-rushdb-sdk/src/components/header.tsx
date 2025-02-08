import { Button } from '@/components/ui/button'
import { Logo } from '@/components/logo'

interface HeaderProps {
  onOpenModal: () => void
}

export function Header({ onOpenModal }: HeaderProps) {
  return (
    <header className="flex justify-between items-center p-4 bg-background border-b fixed top-0 w-full">
      <div className="flex gap-2 items-center">
        <Logo />
        <h1 className="text-2xl font-bold">RushDB Demo App</h1>
      </div>
      <Button onClick={onOpenModal}>Open Code Editor</Button>
    </header>
  )
}
