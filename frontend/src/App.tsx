import { useState } from 'react'
import Navbar from './components/common/Navbar'
import Sidebar from './components/common/Sidebar'
import Dashboard from './pages/Dashboard'
import ChurnAnalysis from './pages/ChurnAnalysis'
import SalesForecast from './pages/SalesForecast'
import CustomerSegments from './pages/CustomerSegments'
import InventoryDemand from './pages/InventoryDemand'

type Page =
  | 'Dashboard'
  | 'Churn Analysis'
  | 'Sales Forecast'
  | 'Customer Segments'
  | 'Inventory & Demand'

function App() {
  const [activePage, setActivePage] = useState<Page>('Dashboard')

  const renderPage = () => {
    switch (activePage) {
      case 'Churn Analysis':
        return <ChurnAnalysis />

      case 'Sales Forecast':
        return <SalesForecast />

      case 'Customer Segments':
        return <CustomerSegments />

      case 'Inventory & Demand':
        return <InventoryDemand />

      case 'Dashboard':
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <div className="flex min-h-[calc(100vh-5rem)]">
        <Sidebar
          activePage={activePage}
          onPageChange={setActivePage}
        />

        <main className="min-w-0 flex-1 overflow-x-hidden">
          <div className="min-h-full bg-[radial-gradient(circle_at_top_right,rgba(14,165,233,0.08),transparent_30%),radial-gradient(circle_at_bottom_left,rgba(139,92,246,0.08),transparent_30%)] p-4 sm:p-6 lg:p-8">
            {renderPage()}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App