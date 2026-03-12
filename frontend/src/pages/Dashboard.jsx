import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Activity, Flame, MessageCircle, Heart, BarChart3, Bot, Target, Send } from 'lucide-react'
import Navbar from '../components/Navbar'
import StatCard from '../components/StatCard'
import AROmiChat from '../components/AROmiChat'
import { workoutApi, nutritionApi, progressApi } from '../services/api'
import useAuthStore from '../stores/authStore'

export default function Dashboard() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    workoutsCompleted: 0,
    caloriesBurned: 0,
    currentStreak: 0,
    charityPoints: 0
  })
  const [showChat, setShowChat] = useState(false)
  const [hasCompletedAssessment, setHasCompletedAssessment] = useState(false)
  const [todayWorkout, setTodayWorkout] = useState(null)
  const [todayMeals, setTodayMeals] = useState(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [progressRes, workoutRes, nutritionRes] = await Promise.all([
        progressApi.getSummary().catch(() => ({ data: {} })),
        workoutApi.getToday().catch(() => ({ data: { today: null } })),
        nutritionApi.getToday().catch(() => ({ data: { today: null } })),
      ])

      setStats({
        workoutsCompleted: progressRes.data.total_workouts || 0,
        caloriesBurned: progressRes.data.total_calories_burned || 0,
        currentStreak: progressRes.data.current_streak || 0,
        charityPoints: progressRes.data.charity_donations || user?.charity_donations || 0
      })

      setTodayWorkout(workoutRes.data?.today || null)
      setTodayMeals(nutritionRes.data?.today || null)

      if (user?.age && user?.height && user?.weight) {
        setHasCompletedAssessment(true)
      }
    } catch (error) {
      console.error('Error loading dashboard:', error)
    }
  }

  // Charity level
  const charityLevel = stats.charityPoints >= 500 ? 'Gold 🥇' : stats.charityPoints >= 100 ? 'Silver 🥈' : 'Bronze 🥉'

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-[#0d0d14] pt-16">
        <div className="max-w-7xl mx-auto px-4 py-8">

          {/* Welcome */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">
              Welcome back, {user?.full_name || user?.username}! 🔥
            </h1>
            <p className="text-gray-400 text-lg">Ready to continue your fitness journey? Let's make today count! 👍</p>

            {!hasCompletedAssessment && (
              <div className="mt-4 bg-purple-600/20 border border-purple-500 rounded-xl p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-semibold mb-1">🎯 Complete Your Health Assessment</h3>
                    <p className="text-gray-300 text-sm">Get personalized workout and nutrition plans tailored just for you!</p>
                  </div>
                  <button
                    onClick={() => navigate('/health-assessment')}
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition font-medium whitespace-nowrap"
                  >
                    Start Assessment →
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Stat Cards */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
            initial="hidden" animate="visible"
            variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.1 } } }}
          >
            {[
              { icon: '🏋️', label: 'Workouts Completed', value: stats.workoutsCompleted, color: 'purple' },
              { icon: '🔥', label: 'Calories Burned', value: stats.caloriesBurned, color: 'orange' },
              { icon: '⚡', label: 'Current Streak', value: `${stats.currentStreak} days`, color: 'blue' },
              { icon: '💚', label: 'Charity Points', value: `₹${stats.charityPoints}`, color: 'green' },
            ].map((s, i) => (
              <motion.div key={i} variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
                <StatCard {...s} />
              </motion.div>
            ))}
          </motion.div>

          {/* Two column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

            {/* Left Column — 60% */}
            <div className="lg:col-span-3 space-y-6">
              {/* Quick Actions */}
              <div>
                <h2 className="text-xl font-semibold text-white mb-4">⚡ Quick Actions</h2>
                <div className="grid grid-cols-2 gap-4">
                  <button onClick={() => navigate('/health-assessment')}
                    className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-5 text-left hover:border-purple-500 transition group">
                    <Heart className="w-8 h-8 text-red-400 mb-3 group-hover:scale-110 transition" />
                    <h3 className="text-white font-semibold">Health Assessment</h3>
                    <p className="text-gray-400 text-xs mt-1">Get AI-powered personalized plans</p>
                  </button>
                  <button onClick={() => setShowChat(true)}
                    className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-5 text-left hover:border-green-500 transition group">
                    <Bot className="w-8 h-8 text-green-400 mb-3 group-hover:scale-110 transition" />
                    <h3 className="text-white font-semibold">Ask AROMI Coach</h3>
                    <p className="text-gray-400 text-xs mt-1">Chat with your health companion</p>
                  </button>
                  <button onClick={() => navigate('/progress')}
                    className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-5 text-left hover:border-blue-500 transition group">
                    <BarChart3 className="w-8 h-8 text-blue-400 mb-3 group-hover:scale-110 transition" />
                    <h3 className="text-white font-semibold">Track Progress</h3>
                    <p className="text-gray-400 text-xs mt-1">View charts and achievements</p>
                  </button>
                  <button onClick={() => navigate('/workouts')}
                    className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-5 text-left hover:border-orange-500 transition group">
                    <Target className="w-8 h-8 text-orange-400 mb-3 group-hover:scale-110 transition" />
                    <h3 className="text-white font-semibold">Today's Workout</h3>
                    <p className="text-gray-400 text-xs mt-1">Start your exercises</p>
                  </button>
                </div>
              </div>

              {/* Today's Workout */}
              <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                    <Activity className="w-5 h-5 text-purple-400" />
                    Today's Workout
                  </h2>
                  <button onClick={() => navigate('/workouts')} className="text-purple-400 hover:text-purple-300 text-sm">
                    View All →
                  </button>
                </div>
                {todayWorkout ? (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-white font-bold text-lg">{todayWorkout.focus_area}</h3>
                      {todayWorkout.rest_day ? (
                        <span className="bg-green-600/20 text-green-400 px-3 py-1 rounded-full text-xs">🧘 Rest Day</span>
                      ) : (
                        <span className="text-gray-400 text-sm">{todayWorkout.duration_minutes} min · {todayWorkout.exercises?.length || 0} exercises</span>
                      )}
                    </div>
                    {!todayWorkout.rest_day && todayWorkout.exercises?.slice(0, 3).map((ex, i) => (
                      <div key={i} className="bg-[#0d0d14] rounded-lg p-3 mb-2 flex justify-between items-center">
                        <span className="text-gray-300 text-sm">{ex.name}</span>
                        <span className="text-gray-500 text-xs">{ex.sets}×{ex.reps}</span>
                      </div>
                    ))}
                    {!todayWorkout.rest_day && todayWorkout.exercises?.length > 3 && (
                      <p className="text-gray-500 text-xs mt-1">+{todayWorkout.exercises.length - 3} more exercises</p>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <p className="text-gray-400 mb-3">No workout plan yet</p>
                    <button onClick={() => navigate('/health-assessment')} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition text-sm">
                      Create Your Plan →
                    </button>
                  </div>
                )}
              </div>

              {/* Today's Nutrition */}
              <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                    <Flame className="w-5 h-5 text-orange-400" />
                    Today's Nutrition
                  </h2>
                  <button onClick={() => navigate('/nutrition')} className="text-purple-400 hover:text-purple-300 text-sm">
                    View All →
                  </button>
                </div>
                {todayMeals ? (
                  <div className="grid grid-cols-3 gap-3">
                    {['breakfast', 'lunch', 'dinner'].map(type => {
                      const meal = todayMeals[type]
                      if (!meal) return null
                      return (
                        <div key={type} className="bg-[#0d0d14] rounded-lg p-3">
                          <p className="text-gray-400 text-xs capitalize mb-1">{type}</p>
                          <p className="text-white text-sm font-medium">{meal.name}</p>
                          <p className="text-orange-400 text-xs mt-1">{meal.calories} cal</p>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <p className="text-gray-400 mb-3">No meal plan yet</p>
                    <button onClick={() => navigate('/nutrition')} className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition text-sm">
                      Create Meal Plan →
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column — 40% */}
            <div className="lg:col-span-2 space-y-6">
              {/* Charity Impact */}
              <div className="bg-gradient-to-br from-green-900/40 to-[#1a1a2e] border border-green-800/30 rounded-xl p-6">
                <h2 className="text-xl font-semibold text-white mb-4">💚 Charity Impact</h2>
                <div className="text-center mb-4">
                  <p className="text-4xl font-bold text-green-400">₹{stats.charityPoints}</p>
                  <p className="text-gray-400 text-sm">Total Donated</p>
                  <span className="inline-block mt-2 bg-green-600/20 text-green-300 px-4 py-1 rounded-full text-sm font-medium">
                    {charityLevel}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-black/20 rounded-lg p-3 text-center">
                    <p className="text-white font-bold">{Math.floor(stats.charityPoints / 10)}</p>
                    <p className="text-gray-400 text-xs">People Impacted</p>
                  </div>
                  <div className="bg-black/20 rounded-lg p-3 text-center">
                    <p className="text-white font-bold">{stats.caloriesBurned}</p>
                    <p className="text-gray-400 text-xs">Calories Burned</p>
                  </div>
                  <div className="bg-black/20 rounded-lg p-3 text-center">
                    <p className="text-white font-bold">{stats.workoutsCompleted}</p>
                    <p className="text-gray-400 text-xs">Workouts Done</p>
                  </div>
                  <div className="bg-black/20 rounded-lg p-3 text-center">
                    <p className="text-white font-bold">{stats.currentStreak}</p>
                    <p className="text-gray-400 text-xs">Day Streak</p>
                  </div>
                </div>
                <div className="bg-black/20 rounded-lg p-3 text-center">
                  <p className="text-gray-400 text-xs">
                    🏋️ +5 per workout · 🥗 +2 per meal · 🔥 +1 per 10 cal burned
                  </p>
                </div>
                <p className="text-green-300/70 text-xs text-center mt-3 italic">
                  Keep going! Every calorie brings hope to someone in need! 💚
                </p>
              </div>

              {/* Telegram Bot Card */}
              <div className="bg-gradient-to-br from-[#1a1a2e] to-[#0d1b2a] border border-[#2a2a40] rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Send className="w-5 h-5 text-[#2AABEE]" />
                  <h2 className="text-lg font-semibold text-white">DoctorGenie Bot</h2>
                </div>
                <p className="text-gray-400 text-xs mb-4">Your AI medical assistant on Telegram — scan prescriptions, find hospitals & more.</p>
                <div className="flex items-center gap-4">
                  <div className="bg-white p-2 rounded-xl flex-shrink-0">
                    <img src="/telegram-qr.png" alt="QR Code" className="w-24 h-24" />
                  </div>
                  <div className="space-y-2">
                    <div className="text-gray-300 text-xs flex items-center gap-1.5">📸 Prescription Scanner</div>
                    <div className="text-gray-300 text-xs flex items-center gap-1.5">🏥 Hospital Finder</div>
                    <div className="text-gray-300 text-xs flex items-center gap-1.5">💊 Med Reminders</div>
                    <a
                      href="https://t.me/DoctorGenie_bot"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 bg-[#2AABEE] hover:bg-[#229ED9] text-white px-3 py-1.5 rounded-lg text-xs font-medium transition mt-1"
                    >
                      <Send className="w-3 h-3" />
                      Open Bot
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AROMI Floating Button */}
          <div className="fixed bottom-6 right-6 z-50">
            <AROmiChat isOpen={showChat} onClose={() => setShowChat(false)} />
            {!showChat && (
              <button
                onClick={() => setShowChat(true)}
                className="bg-gradient-to-r from-purple-600 to-green-600 text-white p-4 rounded-full shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
              >
                <MessageCircle className="w-6 h-6" />
                <span className="font-medium">Chat with AROMI</span>
              </button>
            )}
          </div>

        </div>
      </div>
    </>
  )
}
