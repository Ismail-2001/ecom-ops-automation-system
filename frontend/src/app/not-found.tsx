import Link from "next/link"
import { Home } from "lucide-react"

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center p-8">
      <div className="text-center">
        <div className="text-8xl font-display font-bold text-primary/10 mb-4">404</div>
        <h1 className="font-display text-2xl font-semibold text-text-primary mb-2">
          Page Not Found
        </h1>
        <p className="text-sm text-text-secondary mb-8 max-w-sm mx-auto">
          The page you are looking for does not exist or has been moved.
        </p>
        <Link href="/" className="btn-primary inline-flex">
          <Home className="w-4 h-4" />
          Dashboard
        </Link>
      </div>
    </div>
  )
}
