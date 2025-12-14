import { Route, Routes } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import SourcesPage from './pages/SourcesPage'
import DocumentsPage from './pages/DocumentsPage'
import ClausesPage from './pages/ClausesPage'
import RulesReviewPage from './pages/RulesReviewPage'
import DiffsPage from './pages/DiffsPage'
import EntitlementsPage from './pages/EntitlementsPage'

const App = () => {
  return (
    <div className="flex min-h-screen bg-surface-alt text-text-primary">
      <Sidebar />
      <main className="flex-1 px-8 py-6 overflow-y-auto">
        <Routes>
          <Route path="/" element={<SourcesPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/clauses" element={<ClausesPage />} />
          <Route path="/rules" element={<RulesReviewPage />} />
          <Route path="/diffs" element={<DiffsPage />} />
          <Route path="/entitlements" element={<EntitlementsPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
