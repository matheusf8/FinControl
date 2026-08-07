import { useEffect, useState } from 'react'

type HealthResponse = {
  status: string
  app: string
}

// App.tsx é só um placeholder de Sprint 1: confirma que Vite + Tailwind +
// proxy pro backend estão funcionando. As telas de verdade entram na Sprint 3.
function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setError('Backend não respondeu (rode `uvicorn app.main:app --reload` na pasta backend/)'))
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-semibold text-gray-900 dark:text-gray-100">FinControl</h1>
        <p className="text-gray-500 dark:text-gray-400">Setup da Sprint 1</p>
        {health && (
          <p className="text-green-600 dark:text-green-400">
            ✅ Backend conectado: {health.app} ({health.status})
          </p>
        )}
        {error && <p className="text-red-600 dark:text-red-400">⚠️ {error}</p>}
      </div>
    </div>
  )
}

export default App
