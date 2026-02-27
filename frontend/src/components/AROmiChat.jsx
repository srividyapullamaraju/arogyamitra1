import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, X, Bot, User, Mic } from 'lucide-react'
import { chatApi } from '../services/api'

export default function AROmiChat({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "🙏 Namaste! I'm AROMI, your personal health companion powered by ArogyaMitra! 💚\n\nTell me about your day, ask about your workouts and meals, or let me know if you're traveling — I'll help adjust your plans!\n\nHow can I assist you today? 💪",
      sender: 'bot',
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Smart detection keywords
  const detectTravelOrInjury = (message) => {
    const lower = message.toLowerCase()
    if (/\b(travel|traveling|travelling|trip|vacation|holiday|going out)\b/.test(lower)) {
      return { reason: 'travel', duration_days: 3 }
    }
    if (/\b(injured|injury|pain|hurt|sprain|broke|broken)\b/.test(lower)) {
      return { reason: 'health_issue', duration_days: 5 }
    }
    return null
  }

  const handleSendMessage = async (e) => {
    e?.preventDefault()
    if (!inputMessage.trim()) return

    const userMsg = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMsg])
    const msgText = inputMessage
    setInputMessage('')
    setIsLoading(true)

    try {
      const conversationHistory = messages.slice(-10).map(m => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }))

      const res = await chatApi.send({
        message: msgText,
        conversation_history: conversationHistory
      })

      const botMsg = {
        id: Date.now() + 1,
        text: res.data.response || 'Sorry, I could not process your request.',
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, botMsg])

      // Smart detection: auto-adjust plan for travel/injury
      const detected = detectTravelOrInjury(msgText)
      if (detected) {
        try {
          await chatApi.adjustPlan(detected)
          const adjustMsg = {
            id: Date.now() + 2,
            text: `✅ I've automatically adjusted your workout plan for ${detected.reason === 'travel' ? 'your travel' : 'your health concern'} for the next ${detected.duration_days} days. Your plan is now lighter and more flexible! 💪`,
            sender: 'bot',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, adjustMsg])
        } catch {
          // Silently fail if no plan exists
        }
      }
    } catch (error) {
      console.error('AROMI error:', error)
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: 'Namaste ji! 🙏 Having a small technical issue. Please make sure you are logged in and try again! 💚',
        sender: 'bot',
        timestamp: new Date()
      }])
    } finally {
      setIsLoading(false)
    }
  }

  // Voice input
  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      return
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.continuous = false

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setInputMessage(transcript)
      setIsListening(false)
    }
    recognition.onerror = () => setIsListening(false)
    recognition.onend = () => setIsListening(false)

    setIsListening(true)
    recognition.start()
  }

  if (!isOpen) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 30, scale: 0.95 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="fixed bottom-24 right-6 w-96 h-[500px] z-50 rounded-2xl overflow-hidden bg-[#13131f] border border-[#2a2a40] shadow-2xl flex flex-col"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-green-600 p-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-green-500/30 flex items-center justify-center">
            <span className="text-lg">🤖</span>
          </div>
          <div>
            <h3 className="text-white font-bold">AROMI</h3>
            <p className="text-white/70 text-xs">Your Health Companion</p>
          </div>
        </div>
        <button onClick={onClose} className="text-white/80 hover:text-white p-1">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, x: msg.sender === 'user' ? 20 : -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25 }}
            className={`flex gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs ${msg.sender === 'bot' ? 'bg-green-600/30 text-green-400' : 'bg-purple-600/30 text-purple-400'
              }`}>
              {msg.sender === 'bot' ? '🤖' : <User className="w-4 h-4" />}
            </div>
            <div className={`max-w-[75%] ${msg.sender === 'user' ? 'text-right' : ''}`}>
              <div className={`inline-block p-3 rounded-xl text-sm whitespace-pre-wrap ${msg.sender === 'bot'
                ? 'bg-[#1a1a2e] text-gray-200 rounded-tl-none'
                : 'bg-purple-600 text-white rounded-tr-none'
                }`}>
                {msg.text}
              </div>
              <p className="text-[10px] text-gray-500 mt-1">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </motion.div>
        ))}
        {isLoading && (
          <div className="flex gap-2">
            <div className="w-7 h-7 rounded-full bg-green-600/30 flex items-center justify-center text-xs">🤖</div>
            <div className="bg-[#1a1a2e] p-3 rounded-xl rounded-tl-none">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSendMessage} className="p-3 border-t border-[#2a2a40] flex gap-2 flex-shrink-0">
        <button
          type="button"
          onClick={handleVoiceInput}
          className={`p-2 rounded-lg transition flex-shrink-0 ${isListening ? 'bg-red-600 text-white' : 'bg-[#1a1a2e] text-gray-400 hover:text-white'
            }`}
        >
          <Mic className="w-4 h-4" />
        </button>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask AROMI anything... 💬"
          className="flex-1 bg-[#1a1a2e] border border-[#2a2a40] rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-purple-500"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !inputMessage.trim()}
          className="bg-purple-600 hover:bg-purple-700 text-white p-2 rounded-lg transition disabled:opacity-50 flex-shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </motion.div>
  )
}
