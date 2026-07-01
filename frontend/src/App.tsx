import { useState, useEffect } from 'react'
import { Dashboard } from '@/pages/dashboard'
import { ReviewsPage } from '@/pages/reviews'
import { ToastContainer } from '@/components/ui/toast'

export default function App() {
  // Simple page routing (no router needed for 2 pages)
  const [page, setPage] = useState(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('page') || 'dashboard'
  })

  // Update URL without reload
  useEffect(() => {
    const url = page === 'dashboard' ? '/' : `/?page=${page}`
    window.history.replaceState({}, '', url)
  }, [page])

  if (page === 'reviews') {
    return (
      <>
        <ReviewsPage />
        <ToastContainer />
      </>
    )
  }

  // Expose navigate for sidebar
  const handleNavigate = (p: string) => setPage(p)

  return (
    <>
      <Dashboard onNavigate={handleNavigate} currentPage={page} />
      <ToastContainer />
    </>
  )
}
