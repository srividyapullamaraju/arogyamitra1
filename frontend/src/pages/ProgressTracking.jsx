import { useEffect, useState } from 'react'
import { TrendingUp, Award, Target } from 'lucide-react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import Navbar from '../components/Navbar'
import { progressApi } from '../services/api'
import toast from 'react-hot-toast'

export default function ProgressTracking() {
  const [summary, setSummary] = useState(null)
  const [achievements, setAchievements] = useState([])
  const [charts, setCharts] = useState({ calories_chart: [], streak_chart: [] })
  const [period, setPeriod] = useState('week')
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [logForm, setLogForm] = useState({ weight: '', notes: '', calories_burned: '' })

  useEffect(() => {
    loadProgress()
  }, [period])

  const loadProgress = async () => {
    try {
      const [summaryRes, achievementsRes, chartsRes] = await Promise.all([
        progressApi.getSummary().catch(() => ({ data: {} })),
        progressApi.getAchievements().catch(() => ({ data: { achievements: [] } })),
        progressApi.getCharts().catch(() => ({ data: { calories_chart: [], streak_chart: [] } }))
      ])
      setSummary(summaryRes.data)
      setAchievements(achievementsRes.data?.achievements || [])
      setCharts(chartsRes.data || { calories_chart: [], streak_chart: [] })
    } catch (error) {
      console.error('Error loading progress:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogProgress = async (e) => {
    e.preventDefault()
    try {
      await progressApi.log({
        weight: logForm.weight ? parseFloat(logForm.weight) : null,
        calories_burned: logForm.calories_burned ? parseFloat(logForm.calories_burned) : 0,
        notes: logForm.notes,
      })
      toast.success('Progress logged! 📊')
      setLogForm({ weight: '', notes: '', calories_burned: '' })
      await loadProgress()
    } catch (error) {
      toast.error('Failed to log progress')
    }
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-[#0d0d14] pt-16 flex items-center justify-center">
          <div className="text-white text-xl">Loading progress...</div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-[#0d0d14] pt-16">
        <div className="max-w-7xl mx-auto px-4 py-8">

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">📈 Progress Tracking</h1>
              <p className="text-gray-400">Monitor your fitness journey</p>
            </div>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="bg-[#1a1a2e] border border-[#2a2a40] text-white rounded-xl px-4 py-2 focus:outline-none focus:border-purple-500"
            >
              <option value="week">Last Week</option>
              <option value="month">Last Month</option>
              <option value="3months">Last 3 Months</option>
              <option value="year">Last Year</option>
            </select>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 flex-wrap">
            {[
              { id: 'overview', label: '📊 Overview' },
              { id: 'achievements', label: '🏆 Achievements' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 rounded-xl font-medium transition ${activeTab === tab.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-[#1a1a2e] border border-[#2a2a40] text-gray-400 hover:text-white'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-white/80" />
                      <span className="text-white/70 text-xs">Total Workouts</span>
                    </div>
                    <p className="text-3xl font-bold text-white">{summary?.total_workouts || 0}</p>
                  </div>
                  <div className="bg-gradient-to-br from-orange-600 to-orange-800 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-4 h-4 text-white/80" />
                      <span className="text-white/70 text-xs">Weight Lost</span>
                    </div>
                    <p className="text-3xl font-bold text-white">{summary?.weight_lost || 0} kg</p>
                  </div>
                  <div className="bg-gradient-to-br from-red-600 to-red-800 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-white/80 text-sm">🔥</span>
                      <span className="text-white/70 text-xs">Calories Burned</span>
                    </div>
                    <p className="text-3xl font-bold text-white">{summary?.total_calories_burned || 0}</p>
                  </div>
                  <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-white/80 text-sm">📊</span>
                      <span className="text-white/70 text-xs">BMI</span>
                    </div>
                    <p className="text-3xl font-bold text-white">{summary?.bmi || '-'}</p>
                  </div>
                </div>

                {/* Calories Chart */}
                <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-6">
                  <h2 className="text-xl font-semibold text-white mb-4">🔥 Calories Burned (Last 7 Days)</h2>
                  {charts.calories_chart?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <AreaChart data={charts.calories_chart}>
                        <defs>
                          <linearGradient id="colorCal" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                        <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                        <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: '8px', color: '#fff' }}
                        />
                        <Area type="monotone" dataKey="calories" stroke="#7c3aed" fillOpacity={1} fill="url(#colorCal)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-gray-400 text-center py-8">No calorie data yet. Complete some workouts!</p>
                  )}
                </div>

                {/* Streak Chart */}
                <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-6">
                  <h2 className="text-xl font-semibold text-white mb-4">📅 Workout Streak (Last 7 Days)</h2>
                  {charts.streak_chart?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={charts.streak_chart}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                        <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 12 }} />
                        <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} domain={[0, 1]} ticks={[0, 1]} tickFormatter={(v) => v === 1 ? '✅' : '❌'} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: '8px', color: '#fff' }}
                          formatter={(value) => [value === 1 ? 'Completed' : 'Missed', 'Status']}
                        />
                        <Bar dataKey="completed" fill="#10b981" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-gray-400 text-center py-8">No streak data yet.</p>
                  )}
                </div>
              </div>

              {/* Log Progress Sidebar */}
              <div className="lg:col-span-1">
                <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-6 sticky top-24">
                  <h3 className="text-xl font-semibold text-white mb-4">📝 Log Progress</h3>
                  <form onSubmit={handleLogProgress} className="space-y-4">
                    <div>
                      <label className="text-gray-400 text-sm mb-2 block">Weight (kg)</label>
                      <input
                        type="number" step="0.1"
                        value={logForm.weight}
                        onChange={(e) => setLogForm({ ...logForm, weight: e.target.value })}
                        className="w-full bg-[#0d0d14] border border-[#2a2a40] rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                        placeholder="e.g. 70.5"
                      />
                    </div>
                    <div>
                      <label className="text-gray-400 text-sm mb-2 block">Calories Burned</label>
                      <input
                        type="number"
                        value={logForm.calories_burned}
                        onChange={(e) => setLogForm({ ...logForm, calories_burned: e.target.value })}
                        className="w-full bg-[#0d0d14] border border-[#2a2a40] rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                        placeholder="e.g. 250"
                      />
                    </div>
                    <div>
                      <label className="text-gray-400 text-sm mb-2 block">Notes</label>
                      <textarea
                        value={logForm.notes}
                        onChange={(e) => setLogForm({ ...logForm, notes: e.target.value })}
                        rows={3}
                        className="w-full bg-[#0d0d14] border border-[#2a2a40] rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500 resize-none"
                        placeholder="How are you feeling?"
                      />
                    </div>
                    <button type="submit" className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition font-medium">
                      Log Progress ✅
                    </button>
                  </form>

                  {/* Quick Stats */}
                  <div className="mt-6 pt-6 border-t border-[#2a2a40]">
                    <h4 className="text-white font-medium mb-3">Quick Stats</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Current Streak</span>
                        <span className="text-purple-400 font-bold">{summary?.current_streak || 0} days</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Meals Tracked</span>
                        <span className="text-orange-400 font-bold">{summary?.meals_tracked || 0}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Charity Donated</span>
                        <span className="text-green-400 font-bold">₹{summary?.charity_donations || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ACHIEVEMENTS TAB */}
          {activeTab === 'achievements' && (
            <div>
              <div className="flex items-center gap-2 mb-6">
                <Award className="w-6 h-6 text-yellow-400" />
                <h2 className="text-2xl font-bold text-white">Achievements</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {achievements.map((achievement, idx) => (
                  <div
                    key={idx}
                    className={`bg-[#1a1a2e] border rounded-xl p-5 text-center transition ${achievement.unlocked
                        ? 'border-purple-500 shadow-lg shadow-purple-500/20'
                        : 'border-[#2a2a40] opacity-70'
                      }`}
                  >
                    <div className="text-4xl mb-3">{achievement.icon}</div>
                    <h3 className="text-white font-bold mb-1">{achievement.name}</h3>
                    <p className="text-gray-400 text-xs mb-3">{achievement.description}</p>

                    {/* Circular progress */}
                    <div className="relative w-16 h-16 mx-auto mb-3">
                      <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 64 64">
                        <circle cx="32" cy="32" r="28" stroke="#2a2a40" strokeWidth="4" fill="none" />
                        <circle
                          cx="32" cy="32" r="28"
                          stroke={achievement.unlocked ? '#7c3aed' : '#4a4a6a'}
                          strokeWidth="4"
                          fill="none"
                          strokeDasharray={`${(achievement.percentage / 100) * 175.93} 175.93`}
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-white text-xs font-bold">
                        {achievement.percentage}%
                      </span>
                    </div>

                    <p className="text-gray-500 text-xs">
                      {achievement.current}/{achievement.target}
                    </p>
                    {achievement.unlocked && (
                      <span className="inline-block mt-2 bg-purple-600/30 text-purple-300 px-3 py-1 rounded-full text-xs font-medium">
                        ✅ Unlocked! +10pts
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
