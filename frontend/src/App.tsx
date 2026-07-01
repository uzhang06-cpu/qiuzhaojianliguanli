import { useState } from 'react'
import { useAuthStore } from '@/store/auth'
import { Dashboard } from '@/pages/dashboard'
import { ReviewsPage } from '@/pages/reviews'
import { LoginPage } from '@/pages/login'
import { RegisterPage } from '@/pages/register'
import { ToastContainer } from '@/components/ui/toast'

export default function App() {
  const isAuth = useAuthStore((s) => s.token !== null)

  // Page state: login | register | dashboard | reviews
  const [page, setPage] = useState(() => {
    if (!isAuth) return 'login'
    const params = new URLSearchParams(window.location.search)
    return params.get('page') || 'dashboard'
  })

  const navigate = (p: string) => {
    const url = p === 'dashboard' ? '/' : `/?page=${p}`
    window.history.replaceState({}, '', url)
    setPage(p)
  }

  // Not authenticated → show login
  if (!isAuth) {
    return (
      <>
        {page === 'register' ? (
          <RegisterPage
            onNavigateToLogin={() => setPage('login')}
            onRegisterSuccess={() => navigate('dashboard')}
          />
        ) : (
          <LoginPage
            onNavigateToRegister={() => setPage('register')}
            onLoginSuccess={() => navigate('dashboard')}
          />
        )}
        <ToastContainer />
      </>
    )
  }

  // Authenticated → show app
  if (page === 'reviews') {
    return (
      <>
        <ReviewsPage />
        <ToastContainer />
      </>
    )
  }

  return (
    <>
      <Dashboard onNavigate={navigate} currentPage={page} />
      <ToastContainer />
    </>
  )
}
