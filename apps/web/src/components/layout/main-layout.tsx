import { Outlet } from 'react-router-dom'
import { useState } from 'react'
import { Sidebar } from './sidebar'

export function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />
      <main
        className="min-h-screen transition-all duration-200"
        style={{ marginLeft: collapsed ? 68 : 240 }}
      >
        <div className="mx-auto max-w-[1400px] px-6 py-8 lg:px-10">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
