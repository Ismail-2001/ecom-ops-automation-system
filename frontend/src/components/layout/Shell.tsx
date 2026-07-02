import Sidebar from "./Sidebar"
import Topbar from "./Topbar"

export default function Shell({ children, title, subtitle, actions }: {
  children: React.ReactNode
  title?: string
  subtitle?: string
  actions?: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-void">
      <Sidebar />
      <div className="ml-[240px]">
        <Topbar title={title} subtitle={subtitle} actions={actions} />
        <main className="p-6">{children}</main>
      </div>
    </div>
  )
}
