/**
 * AI Floating Action Button
 *
 * A floating button that opens the AI assistant chat.
 */

import { useState } from 'react'
import { Fab, Badge, Tooltip, Zoom } from '@mui/material'
import SmartToyIcon from '@mui/icons-material/SmartToy'

import { AIAssistantChat } from './AIAssistantChat'

interface AIFloatingButtonProps {
  userId?: string
  showBadge?: boolean
  badgeContent?: number
  initialMessage?: string
}

export function AIFloatingButton({
  userId = 'anonymous',
  showBadge = false,
  badgeContent = 0,
  initialMessage,
}: AIFloatingButtonProps) {
  const [chatOpen, setChatOpen] = useState(false)

  const handleOpenChat = () => {
    setChatOpen(true)
  }

  const handleCloseChat = () => {
    setChatOpen(false)
  }

  return (
    <>
      <Zoom in={!chatOpen}>
        <Tooltip title="AI Assistant" placement="left">
          <Fab
            aria-label="Open AI assistant"
            onClick={handleOpenChat}
            sx={{
              position: 'fixed',
              bottom: 'var(--ob-space-400)',
              right: 'var(--ob-space-400)',
              background:
                'linear-gradient(135deg, var(--ob-color-brand-primary), var(--ob-color-neon-blue))',
              color: 'var(--ob-color-bg-base)',
              '&:hover': {
                background:
                  'linear-gradient(135deg, var(--ob-color-brand-primary), var(--ob-color-neon-blue))',
                boxShadow:
                  '0 0 var(--ob-space-150) var(--ob-color-brand-primary)',
              },
              zIndex: 1200,
            }}
          >
            <Badge
              badgeContent={showBadge ? badgeContent : 0}
              color="error"
              invisible={!showBadge || badgeContent === 0}
            >
              <SmartToyIcon />
            </Badge>
          </Fab>
        </Tooltip>
      </Zoom>

      <AIAssistantChat
        open={chatOpen}
        onClose={handleCloseChat}
        userId={userId}
        initialMessage={initialMessage}
      />
    </>
  )
}

export default AIFloatingButton
