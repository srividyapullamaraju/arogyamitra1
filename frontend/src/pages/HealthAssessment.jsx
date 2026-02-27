import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { workoutApi, nutritionApi } from '../services/api'
import api from '../services/api'

const questions = [
  { id: 'age', label: 'What is your age?', type: 'number', placeholder: 'e.g. 22' },
  { id: 'gender', label: 'What is your gender?', type: 'choice', options: ['Male', 'Female', 'Other'] },
  { id: 'height', label: 'What is your height (in cm)?', type: 'number', placeholder: 'e.g. 170' },
  { id: 'weight', label: 'What is your weight (in kg)?', type: 'number', placeholder: 'e.g. 70' },
  { id: 'fitness_level', label: 'What is your current fitness level?', type: 'choice', options: ['Beginner', 'Intermediate', 'Advanced'] },
  { id: 'fitness_goal', label: 'What is your primary fitness goal?', type: 'choice', options: ['Weight Loss', 'Muscle Gain', 'General Fitness', 'Strength Training', 'Endurance'] },
  { id: 'workout_preference', label: 'Where do you prefer to work out?', type: 'choice', options: ['Home', 'Gym', 'Outdoor', 'Mixed'] },
  { id: 'workout_time_preference', label: 'When do you prefer to work out?', type: 'choice', options: ['Morning', 'Evening'] },
  { id: 'medical_history', label: 'Any medical history?', type: 'textarea', placeholder: 'e.g. Heart condition (optional)' },
  { id: 'health_conditions', label: 'Any current health conditions?', type: 'textarea', placeholder: 'e.g. Diabetes (optional)' },
  { id: 'injuries', label: 'Any past or present injuries?', type: 'textarea', placeholder: 'e.g. Knee injury (optional)' },
  { id: 'allergies', label: 'Any food allergies?', type: 'textarea', placeholder: 'e.g. Peanuts, Dairy (optional)' },
  { id: 'medications', label: 'Are you taking any medications?', type: 'textarea', placeholder: 'e.g. Blood pressure medication (optional)' },
  { id: 'calendar_sync', label: 'Sync your plan to Google Calendar?', type: 'checkbox' },
]

export default function HealthAssessment() {
  const navigate = useNavigate()
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(false)

  const q = questions[current]
  const total = questions.length                          // 14
  const progress = Math.round((current / (total - 1)) * 100) // 0% → 100%

  /* for choice questions: just save, don't auto-advance */
  const handleChoice = (value) => {
    setAnswers(prev => ({ ...prev, [q.id]: value }))
  }

  const handleNext = () => {
    if (current < total - 1) setCurrent(c => c + 1)
  }

  const handleBack = () => {
    if (current > 0) setCurrent(c => c - 1)
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      // ── build payload ──────────────────────────────
      const goalRaw = (answers.fitness_goal || 'Weight Loss')
      const goalMap = {
        'Weight Loss': 'weight_loss',
        'Muscle Gain': 'muscle_gain',
        'General Fitness': 'maintenance',
        'Strength Training': 'muscle_gain',
        'Endurance': 'endurance',
      }

      const payload = {
        age: parseInt(answers.age) || 22,
        gender: (answers.gender || 'Male').toLowerCase(),
        height: parseFloat(answers.height) || 170,
        weight: parseFloat(answers.weight) || 70,
        fitness_level: (answers.fitness_level || 'Beginner').toLowerCase(),
        fitness_goal: goalMap[goalRaw] || 'weight_loss',
        workout_preference: (answers.workout_preference || 'Home').toLowerCase(),
        workout_time_preference: (answers.workout_time_preference || 'Morning').toLowerCase(),
        medical_history: answers.medical_history || '',
        health_conditions: answers.health_conditions || '',
        injuries: answers.injuries || '',
        allergies: answers.allergies || '',
        medications: answers.medications || '',
        calendar_sync: answers.calendar_sync || false,
      }

      // ── submit assessment ──────────────────────────
      await api.post('/api/health-assessment/assessment/submit', payload)
      toast.success('Assessment saved! ✅')

      // ── generate plans ─────────────────────────────
      toast.loading('Generating workout plan... 💪', { id: 'gen' })
      await workoutApi.generate()

      toast.loading('Generating nutrition plan... 🥗', { id: 'gen' })
      await nutritionApi.generate({
        calorie_target: 1800,
        diet_type: payload.fitness_goal,
        allergies: payload.allergies,
      })

      toast.success('Your plans are ready! 🎉', { id: 'gen' })
      navigate('/dashboard')

    } catch (err) {
      console.error('Submit error:', err.response?.data || err.message)
      toast.error(err.response?.data?.detail || 'Something went wrong — check console')
      toast.dismiss('gen')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0d0d14] flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-lg">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-1">⚡ Smart Fitness Planner</h1>
          <p className="text-gray-400">Answer a few questions to get your personalized plan</p>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Question {current + 1} of {total}</span>
            <span>{progress}% Complete</span>
          </div>
          <div className="w-full bg-[#1a1a2e] rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%`, background: 'linear-gradient(90deg,#7c3aed,#3b82f6)' }}
            />
          </div>
        </div>

        {/* Question Card */}
        <AnimatePresence mode="wait">
          <motion.div
            key={current}
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -40 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="bg-[#1a1a2e] border border-[#2a2a40] rounded-2xl p-8 mb-6"
          >
            <h2 className="text-xl font-semibold text-white mb-6">{q.label}</h2>

            {/* NUMBER */}
            {q.type === 'number' && (
              <input
                type="number"
                placeholder={q.placeholder}
                value={answers[q.id] || ''}
                onChange={e => setAnswers(p => ({ ...p, [q.id]: e.target.value }))}
                className="w-full bg-[#0d0d14] border border-[#2a2a40] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 text-lg"
              />
            )}

            {/* CHOICE — click selects but does NOT advance */}
            {q.type === 'choice' && (
              <div className="grid grid-cols-2 gap-3">
                {q.options.map(opt => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleChoice(opt)}
                    className={`py-3 px-4 rounded-xl border text-sm font-medium transition-all ${answers[q.id] === opt
                      ? 'bg-purple-600 border-purple-500 text-white'
                      : 'bg-[#0d0d14] border-[#2a2a40] text-gray-300 hover:border-purple-500'
                      }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}

            {/* TEXTAREA */}
            {q.type === 'textarea' && (
              <textarea
                placeholder={q.placeholder}
                value={answers[q.id] || ''}
                onChange={e => setAnswers(p => ({ ...p, [q.id]: e.target.value }))}
                rows={3}
                className="w-full bg-[#0d0d14] border border-[#2a2a40] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 resize-none"
              />
            )}

            {/* CHECKBOX */}
            {q.type === 'checkbox' && (
              <div
                onClick={() => setAnswers(p => ({ ...p, [q.id]: !p[q.id] }))}
                className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all ${answers[q.id]
                  ? 'bg-purple-900/30 border-purple-500'
                  : 'bg-[#0d0d14] border-[#2a2a40] hover:border-purple-500'
                  }`}
              >
                <div className={`w-6 h-6 rounded-md border-2 flex items-center justify-center ${answers[q.id] ? 'bg-purple-600 border-purple-500' : 'border-gray-500'
                  }`}>
                  {answers[q.id] && <span className="text-white text-xs">✓</span>}
                </div>
                <div>
                  <p className="text-white font-medium">Yes, sync to Google Calendar</p>
                  <p className="text-gray-400 text-sm">Workouts and meals will appear in your calendar</p>
                </div>
              </div>
            )}

            {/* Nav Buttons */}
            <div className="flex gap-3 mt-6">
              {current > 0 && (
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 py-3 rounded-xl border border-[#2a2a40] text-gray-300 hover:border-purple-500 transition font-medium"
                >
                  ← Back
                </button>
              )}

              {current < total - 1 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="flex-1 py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold transition"
                >
                  Next →
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex-1 py-3 rounded-xl font-semibold transition disabled:opacity-50 text-white"
                  style={{ background: 'linear-gradient(135deg,#7c3aed,#3b82f6)' }}
                >
                  {loading ? '✨ Creating your plan...' : 'Generate Plan ⚡'}
                </button>
              )}
            </div>

          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}