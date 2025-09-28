import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { TranslationProvider } from './i18n'
import '@ob/tokens.css'
import './index.css'

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <TranslationProvider locale="en">
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </TranslationProvider>
  </React.StrictMode>,
)
