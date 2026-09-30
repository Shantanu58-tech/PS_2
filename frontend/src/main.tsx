import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'
import './situation.css'
import './landing.css'

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 30000, retry: 2 } } })

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)

// fade the boot splash out once the first screen has rendered
requestAnimationFrame(() => setTimeout(() => {
  const boot = document.getElementById('boot')
  if (!boot) return
  boot.style.opacity = '0'
  setTimeout(() => boot.remove(), 500)
}, 250))
