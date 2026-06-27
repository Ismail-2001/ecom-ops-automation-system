"use client"

import { Sidebar } from "./Sidebar"

interface ShellProps {
  children: React.ReactNode
}

export function Shell({ children }: ShellProps) {
  return (
    <div className="min-h-screen bg-void">
      <Sidebar />
      <main className="ml-[220px] min-h-screen">
        {children}
      </main>
    </div>
  )
}
