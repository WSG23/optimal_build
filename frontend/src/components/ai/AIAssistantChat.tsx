/**
 * AI Assistant Chat Component
 *
 * A floating chat interface for the conversational AI assistant.
 */

import { useState, useRef, useEffect, useCallback, KeyboardEvent } from 'react'
import {
  Box,
  IconButton,
  TextField,
  Typography,
  Chip,
  CircularProgress,
  Fade,
  Slide,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import SendIcon from '@mui/icons-material/Send'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import PersonIcon from '@mui/icons-material/Person'

import { Card } from '../canonical/Card'
import {
  sendChatMessage,
  ChatMessageResponse,
} from '../../api/ai'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  suggestions?: string[]
}

interface AIAssistantChatProps {
  open: boolean
  onClose: () => void
  userId?: string
  initialMessage?: string
}

export function AIAssistantChat({
  open,
  onClose,
  userId = 'anonymous',
  initialMessage,
}: AIAssistantChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus()
    }
  }, [open])

  useEffect(() => {
    if (open && initialMessage && messages.length === 0) {
      handleSendMessage(initialMessage)
    }
    // Only run on initial open with initialMessage
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initialMessage])

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || input.trim()
    if (!text || isLoading) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response: ChatMessageResponse = await sendChatMessage({
        message: text,
        conversation_id: conversationId || undefined,
        user_id: userId,
      })

      if (response.conversation_id) {
        setConversationId(response.conversation_id)
      }

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        suggestions: response.suggestions,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content:
          'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion)
  }

  return (
    <Slide direction="up" in={open} mountOnEnter unmountOnExit>
      <Box
        sx={{
          position: 'fixed',
          bottom: 'var(--ob-space-400)',
          right: 'var(--ob-space-400)',
          width: 400,
          maxWidth: 'calc(100vw - var(--ob-space-800))',
          zIndex: 1300,
        }}
      >
        <Card variant="premium" hover="none" sx={{ overflow: 'hidden' }}>
          {/* Header */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              p: 'var(--ob-space-200)',
              borderBottom: 'var(--ob-border-fine)',
              background: 'var(--ob-surface-glass-1)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 'var(--ob-space-100)' }}>
              <SmartToyIcon
                sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 24 }}
              />
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: 600,
                  color: 'var(--ob-color-text-primary)',
                }}
              >
                AI Assistant
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={onClose}
              sx={{ color: 'var(--ob-color-text-secondary)' }}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>

          {/* Messages */}
          <Box
            sx={{
              height: 400,
              overflowY: 'auto',
              p: 'var(--ob-space-200)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-200)',
              background: 'var(--ob-color-bg-base)',
            }}
          >
            {messages.length === 0 && (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  textAlign: 'center',
                  color: 'var(--ob-color-text-tertiary)',
                }}
              >
                <SmartToyIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                <Typography variant="body2">
                  Ask me anything about your deals, properties, or market insights.
                </Typography>
              </Box>
            )}

            {messages.map((message) => (
              <Fade in key={message.id}>
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems:
                      message.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 'var(--ob-space-100)',
                      maxWidth: '85%',
                    }}
                  >
                    {message.role === 'assistant' && (
                      <SmartToyIcon
                        sx={{
                          color: 'var(--ob-color-neon-cyan)',
                          fontSize: 20,
                          mt: 0.5,
                        }}
                      />
                    )}
                    <Box
                      sx={{
                        p: 'var(--ob-space-150)',
                        borderRadius: 'var(--ob-radius-sm)',
                        background:
                          message.role === 'user'
                            ? 'var(--ob-color-neon-cyan)'
                            : 'var(--ob-surface-glass-1)',
                        color:
                          message.role === 'user'
                            ? 'var(--ob-color-bg-base)'
                            : 'var(--ob-color-text-primary)',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {message.content}
                      </Typography>
                    </Box>
                    {message.role === 'user' && (
                      <PersonIcon
                        sx={{
                          color: 'var(--ob-color-text-secondary)',
                          fontSize: 20,
                          mt: 0.5,
                        }}
                      />
                    )}
                  </Box>

                  {/* Suggestions */}
                  {message.suggestions && message.suggestions.length > 0 && (
                    <Box
                      sx={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: 'var(--ob-space-50)',
                        mt: 'var(--ob-space-100)',
                        pl: 'var(--ob-space-400)',
                      }}
                    >
                      {message.suggestions.map((suggestion, idx) => (
                        <Chip
                          key={idx}
                          label={suggestion}
                          size="small"
                          variant="outlined"
                          onClick={() => handleSuggestionClick(suggestion)}
                          sx={{
                            borderColor: 'var(--ob-color-border-subtle)',
                            color: 'var(--ob-color-text-secondary)',
                            fontSize: '0.75rem',
                            cursor: 'pointer',
                            '&:hover': {
                              borderColor: 'var(--ob-color-neon-cyan)',
                              color: 'var(--ob-color-neon-cyan)',
                            },
                          }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              </Fade>
            ))}

            {isLoading && (
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--ob-space-100)',
                }}
              >
                <SmartToyIcon
                  sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 20 }}
                />
                <CircularProgress size={16} sx={{ color: 'var(--ob-color-neon-cyan)' }} />
              </Box>
            )}

            <div ref={messagesEndRef} />
          </Box>

          {/* Input */}
          <Box
            sx={{
              p: 'var(--ob-space-200)',
              borderTop: 'var(--ob-border-fine)',
              background: 'var(--ob-surface-glass-1)',
              display: 'flex',
              gap: 'var(--ob-space-100)',
            }}
          >
            <TextField
              inputRef={inputRef}
              fullWidth
              size="small"
              placeholder="Ask a question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={isLoading}
              sx={{
                '& .MuiOutlinedInput-root': {
                  background: 'var(--ob-color-bg-base)',
                  borderRadius: 'var(--ob-radius-xs)',
                  '& fieldset': {
                    borderColor: 'var(--ob-color-border-subtle)',
                  },
                  '&:hover fieldset': {
                    borderColor: 'var(--ob-color-border-default)',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: 'var(--ob-color-neon-cyan)',
                  },
                },
                '& .MuiInputBase-input': {
                  color: 'var(--ob-color-text-primary)',
                  fontSize: '0.875rem',
                },
              }}
            />
            <IconButton
              onClick={() => handleSendMessage()}
              disabled={!input.trim() || isLoading}
              sx={{
                color: 'var(--ob-color-neon-cyan)',
                '&:disabled': {
                  color: 'var(--ob-color-text-disabled)',
                },
              }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Card>
      </Box>
    </Slide>
  )
}

export default AIAssistantChat
