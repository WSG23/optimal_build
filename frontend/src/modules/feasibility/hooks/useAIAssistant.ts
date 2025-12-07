import { useState, useCallback, useRef, useEffect } from 'react'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function useAIAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hi! I can help optimize your massing or answer zoning questions.',
      timestamp: new Date(),
    },
  ])
  const [isTyping, setIsTyping] = useState(false)
  const timeoutRef = useRef<number | null>(null)

  const sendMessage = useCallback((content: string) => {
    // Add user message
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsTyping(true)

    // Simulate AI response
    if (timeoutRef.current) clearTimeout(timeoutRef.current)

    timeoutRef.current = window.setTimeout(() => {
      setIsTyping(false)
      let responseText = "I'm analyzing that for you..."

      const lower = content.toLowerCase()
      if (lower.includes('density') || lower.includes('gfa')) {
        responseText =
          'Based on the 3.2 Plot Ratio, we can maximize GFA by pushing the tower to the rear setback line. This increases efficiency by ~4%.'
      } else if (lower.includes('height') || lower.includes('tall')) {
        responseText =
          'The z height limit is 120m AMSL here. We can fit approximately 32 residential floors with 3.2m floor-to-floor height.'
      } else if (lower.includes('green') || lower.includes('sus')) {
        responseText =
          "To improve the Green Mark score, consider adding sky terraces on levels 14 and 24. This simulates a 'Vertical Village' approach."
      } else {
        responseText =
          "I've updated the constraints based on your request. The feasibility model will reflect this in the next run."
      }

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseText,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, botMsg])
    }, 1500)
  }, [])

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [])

  return {
    messages,
    isTyping,
    sendMessage,
  }
}
