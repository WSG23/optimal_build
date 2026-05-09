import {
  Drawer,
  IconButton,
  TextField,
  Typography,
  Avatar,
} from '@mui/material'
import Close from '@mui/icons-material/Close'
import Send from '@mui/icons-material/Send'
import SmartToy from '@mui/icons-material/SmartToy'
import { useState, useRef, useEffect } from 'react'
import type { ChatMessage } from '../hooks/useAIAssistant'

interface AIAssistantSidebarProps {
  open: boolean
  onClose: () => void
  messages: ChatMessage[]
  onSendMessage: (msg: string) => void
  isTyping: boolean
}

export function AIAssistantSidebar({
  open,
  onClose,
  messages,
  onSendMessage,
  isTyping,
}: AIAssistantSidebarProps) {
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isTyping])

  const handleSend = () => {
    if (!input.trim()) return
    onSendMessage(input)
    setInput('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      variant="persistent"
      PaperProps={{
        sx: {
          width: 380,
          background: 'var(--ob-color-bg-surface-main)',
          borderLeft: '1px solid var(--ob-color-border-light)',
          boxShadow: 'var(--ob-shadow-xl)',
        },
      }}
    >
      <div
        className="ai-assistant"
        style={{ display: 'flex', flexDirection: 'column', height: '100%' }}
      >
        {/* Header */}
        <div
          style={{
            padding: 'var(--ob-space-100)',
            borderBottom: '1px solid var(--ob-color-border-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--ob-color-brand-primary)',
            color: 'white',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-75)',
            }}
          >
            <Avatar
              sx={{ bgcolor: 'white', color: 'var(--ob-color-brand-primary)' }}
            >
              <SmartToy />
            </Avatar>
            <div>
              <Typography variant="subtitle1" fontWeight={600}>
                Planner Bot
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.9 }}>
                AI Site Analyst
              </Typography>
            </div>
          </div>
          <IconButton onClick={onClose} size="small" sx={{ color: 'white' }}>
            <Close />
          </IconButton>
        </div>

        {/* Messages */}
        <div
          ref={scrollRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--ob-space-100)',
            background: 'var(--ob-color-bg-surface, #f5f5f7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-100)',
          }}
        >
          {messages.map((msg) => {
            const isBot = msg.role === 'assistant'
            return (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  justifyContent: isBot ? 'flex-start' : 'flex-end',
                  marginBottom: 'var(--ob-space-25)',
                }}
              >
                <div
                  style={{
                    maxWidth: '85%',
                    padding: 'var(--ob-space-75) var(--ob-space-100)',
                    borderRadius: isBot ? '4px 4px 4px 2px' : '4px 4px 2px 4px',
                    background: isBot
                      ? 'white'
                      : 'var(--ob-color-brand-primary)',
                    color: isBot ? 'text.primary' : 'white',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                    fontSize: 'var(--ob-font-size-sm)',
                    lineHeight: 'var(--ob-line-height-normal)',
                  }}
                >
                  {msg.content}
                </div>
              </div>
            )
          })}

          {isTyping && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div
                style={{
                  padding: 'var(--ob-space-75) var(--ob-space-100)',
                  borderRadius:
                    'var(--ob-radius-sm) var(--ob-radius-sm) var(--ob-radius-sm) var(--ob-radius-xs)',
                  background: 'white',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    gap: 'var(--ob-space-25)',
                    alignItems: 'center',
                    height: '14px',
                  }}
                >
                  <span
                    className="dot-flashing"
                    style={{
                      width: 6,
                      height: 6,
                      background: 'var(--ob-color-text-muted, #ccc)',
                      borderRadius: '50%',
                      animation: 'pulse 1s infinite',
                    }}
                  />
                  <span
                    className="dot-flashing"
                    style={{
                      width: 6,
                      height: 6,
                      background: 'var(--ob-color-text-muted, #ccc)',
                      borderRadius: '50%',
                      animation: 'pulse 1s infinite 0.2s',
                    }}
                  />
                  <span
                    className="dot-flashing"
                    style={{
                      width: 6,
                      height: 6,
                      background: 'var(--ob-color-text-muted, #ccc)',
                      borderRadius: '50%',
                      animation: 'pulse 1s infinite 0.4s',
                    }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div
          style={{
            padding: 'var(--ob-space-100)',
            background: 'white',
            borderTop: '1px solid var(--ob-color-border-light)',
          }}
        >
          <TextField
            fullWidth
            placeholder="Ask about density, setbacks..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            size="small"
            InputProps={{
              endAdornment: (
                <IconButton
                  onClick={handleSend}
                  disabled={!input.trim()}
                  color="primary"
                >
                  <Send />
                </IconButton>
              ),
              sx: { borderRadius: 'var(--ob-radius-md)' },
            }}
          />
        </div>
      </div>
    </Drawer>
  )
}
