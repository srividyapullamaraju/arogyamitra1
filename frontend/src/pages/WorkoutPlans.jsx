import { useEffect, useState } from 'react'
import { Play, Check, Clock, Flame, ChevronDown, ChevronUp, X, Camera } from 'lucide-react'
import Navbar from '../components/Navbar'
import ExerciseCamera from '../components/ExerciseCamera'
import { workoutApi } from '../services/api'
import { workoutToCalendarUrl, syncWeekToCalendar } from '../utils/calendarUrl'
import toast from 'react-hot-toast'

export default function WorkoutPlans() {
  const [plan, setPlan] = useState(null)
  const [todayWorkout, setTodayWorkout] = useState(null)
  const [todayName, setTodayName] = useState('')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [activeTab, setActiveTab] = useState('today')
  const [expandedDay, setExpandedDay] = useState(null)
  const [completedExercises, setCompletedExercises] = useState(new Set())
  const [playerExercise, setPlayerExercise] = useState(null)
  const [videoData, setVideoData] = useState(null)
  const [videoLoading, setVideoLoading] = useState(false)
  const [showCamera, setShowCamera] = useState(false)

  useEffect(() => {
    loadWorkouts()
  }, [])

  const loadWorkouts = async () => {
    try {
      const [planRes, todayRes] = await Promise.all([
        workoutApi.getCurrent().catch(() => ({ data: null })),
        workoutApi.getToday().catch(() => ({ data: { today: null, day_name: '' } }))
      ])
      setPlan(planRes.data?.plan || null)
      setTodayWorkout(todayRes.data?.today || null)
      setTodayName(todayRes.data?.day_name || '')
    } catch (error) {
      console.error('Error loading workouts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleGeneratePlan = async () => {
    setGenerating(true)
    try {
      toast.loading('Generating your workout plan... 💪', { id: 'gen' })
      await workoutApi.generate()
      toast.success('New workout plan generated! 💪', { id: 'gen' })
      await loadWorkouts()
    } catch (error) {
      toast.error('Failed to generate plan', { id: 'gen' })
    } finally {
      setGenerating(false)
    }
  }

  const handleCompleteExercise = async (exerciseName) => {
    try {
      await workoutApi.complete({ exercise_id: exerciseName, calories_burned: 50, duration_minutes: 5 })
      setCompletedExercises(prev => new Set([...prev, exerciseName]))
      toast.success('Exercise completed! +5 charity points 💚')
    } catch (error) {
      toast.error('Failed to mark as complete')
    }
  }

  const days = plan?.days || plan?.weekly_plan || []

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-[#0d0d14] pt-16 flex items-center justify-center">
          <div className="text-white text-xl">Loading workouts...</div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-[#0d0d14] pt-16">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Workout Plans 🏋️</h1>
              <p className="text-gray-400">Your personalized fitness journey</p>
            </div>
            <button
              onClick={handleGeneratePlan}
              disabled={generating}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition disabled:opacity-50"
            >
              {generating ? 'Generating...' : '✨ Generate New Plan'}
            </button>
          </div>

          {plan ? (
            <>
              {/* Tab Switcher */}
              <div className="flex gap-2 mb-6">
                <button
                  onClick={() => setActiveTab('today')}
                  className={`px-6 py-3 rounded-xl font-medium transition ${activeTab === 'today'
                    ? 'bg-purple-600 text-white'
                    : 'bg-[#1a1a2e] border border-[#2a2a40] text-gray-400 hover:text-white'
                    }`}
                >
                  🌅 Today
                </button>
                <button
                  onClick={() => setActiveTab('week')}
                  className={`px-6 py-3 rounded-xl font-medium transition ${activeTab === 'week'
                    ? 'bg-purple-600 text-white'
                    : 'bg-[#1a1a2e] border border-[#2a2a40] text-gray-400 hover:text-white'
                    }`}
                >
                  📅 This Week
                </button>
                <button
                  onClick={() => { syncWeekToCalendar(days); toast.success('Opening calendar events — approve each one! 📅') }}
                  className="px-6 py-3 rounded-xl font-medium transition bg-green-600/20 border border-green-600/30 text-green-400 hover:text-green-300 hover:border-green-500"
                >
                  🔄 Sync Week to Calendar
                </button>
              </div>

              {/* TODAY TAB */}
              {activeTab === 'today' && todayWorkout && (
                <div className="space-y-4">
                  {/* Today's header card */}
                  <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6">
                    <h2 className="text-2xl font-bold text-white mb-2">
                      {todayName} — {todayWorkout.focus_area}
                    </h2>
                    <div className="flex gap-6 text-white/80 flex-wrap">
                      <span className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        {todayWorkout.duration_minutes || 45} min
                      </span>
                      <span className="flex items-center gap-2">
                        <Flame className="w-4 h-4" />
                        {todayWorkout.exercises?.length || 0} exercises
                      </span>
                      {todayWorkout.rest_day && (
                        <span className="bg-green-500/30 text-green-300 px-3 py-1 rounded-full text-sm">
                          🧘 Rest Day
                        </span>
                      )}
                    </div>
                    <a
                      href={workoutToCalendarUrl(todayWorkout, 0)}
                      target="_blank" rel="noopener noreferrer"
                      className="mt-3 inline-flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg text-sm transition"
                    >
                      📅 Add to Google Calendar
                    </a>
                  </div>

                  {!todayWorkout.rest_day && (
                    <>
                      {/* Warmup */}
                      {todayWorkout.warmup && (
                        <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-4">
                          <h3 className="text-white font-semibold mb-2">🔥 Warmup</h3>
                          <p className="text-gray-400">{todayWorkout.warmup}</p>
                        </div>
                      )}

                      {/* Exercises */}
                      <div className="space-y-3">
                        {todayWorkout.exercises?.map((ex, idx) => {
                          const isCompleted = completedExercises.has(ex.name)
                          return (
                            <div key={idx} className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-5 flex items-center gap-4">
                              {/* Checkbox */}
                              <button
                                onClick={() => !isCompleted && handleCompleteExercise(ex.name)}
                                className={`w-7 h-7 rounded-lg border-2 flex items-center justify-center flex-shrink-0 transition ${isCompleted
                                  ? 'bg-green-600 border-green-500'
                                  : 'border-gray-500 hover:border-purple-500'
                                  }`}
                              >
                                {isCompleted && <Check className="w-4 h-4 text-white" />}
                              </button>

                              {/* Exercise info */}
                              <div className="flex-1">
                                <h4 className="text-white font-semibold">{ex.name}</h4>
                                <p className="text-gray-400 text-sm mt-1">{ex.description}</p>
                                <div className="flex gap-2 mt-2 flex-wrap">
                                  <span className="bg-purple-600/20 text-purple-300 px-3 py-1 rounded-full text-xs">
                                    {ex.sets} sets
                                  </span>
                                  <span className="bg-blue-600/20 text-blue-300 px-3 py-1 rounded-full text-xs">
                                    {ex.reps} reps
                                  </span>
                                  <span className="bg-orange-600/20 text-orange-300 px-3 py-1 rounded-full text-xs">
                                    {ex.rest_seconds}s rest
                                  </span>
                                </div>
                              </div>

                              {/* Play button */}
                              <button
                                onClick={() => setPlayerExercise(ex)}
                                className="bg-purple-600 hover:bg-purple-700 text-white p-3 rounded-xl transition flex-shrink-0"
                              >
                                <Play className="w-5 h-5" />
                              </button>
                            </div>
                          )
                        })}
                      </div>

                      {/* Cooldown */}
                      {todayWorkout.cool_down && (
                        <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-4">
                          <h3 className="text-white font-semibold mb-2">🧊 Cool Down</h3>
                          <p className="text-gray-400">{todayWorkout.cool_down}</p>
                        </div>
                      )}

                      {/* Daily tip */}
                      {todayWorkout.daily_tip && (
                        <div className="bg-green-900/20 border border-green-800/30 rounded-xl p-4">
                          <p className="text-green-300 text-sm">💡 {todayWorkout.daily_tip}</p>
                        </div>
                      )}
                    </>
                  )}

                  {todayWorkout.rest_day && (
                    <div className="text-center py-12 bg-[#1a1a2e] border border-[#2a2a40] rounded-xl">
                      <div className="text-6xl mb-4">🧘</div>
                      <h3 className="text-2xl font-bold text-white mb-2">Rest Day!</h3>
                      <p className="text-gray-400">Your body recovers stronger. Light stretching is great today.</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'today' && !todayWorkout && (
                <div className="text-center py-12 bg-[#1a1a2e] border border-[#2a2a40] rounded-xl">
                  <p className="text-gray-400">Today's workout data not available. Check your plan.</p>
                </div>
              )}

              {/* WEEK TAB */}
              {activeTab === 'week' && (
                <div className="space-y-3">
                  {days.map((day, idx) => (
                    <div key={idx} className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl overflow-hidden">
                      <button
                        onClick={() => setExpandedDay(expandedDay === idx ? null : idx)}
                        className="w-full p-5 flex items-center justify-between text-left"
                      >
                        <div className="flex items-center gap-4">
                          <span className="text-white font-bold text-lg w-28">{day.day}</span>
                          <span className="text-purple-400 font-medium">{day.focus_area}</span>
                          {day.rest_day && (
                            <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-xs">Rest Day</span>
                          )}
                        </div>
                        <div className="flex items-center gap-4">
                          {!day.rest_day && (
                            <>
                              <span className="text-gray-400 text-sm flex items-center gap-1">
                                <Clock className="w-4 h-4" /> {day.duration_minutes} min
                              </span>
                              <span className="text-gray-400 text-sm">
                                {day.exercises?.length || 0} exercises
                              </span>
                            </>
                          )}
                          {expandedDay === idx ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                      </button>

                      {expandedDay === idx && !day.rest_day && (
                        <div className="px-5 pb-5 border-t border-[#2a2a40] pt-4 space-y-3">
                          {day.warmup && (
                            <p className="text-gray-400 text-sm">🔥 Warmup: {day.warmup}</p>
                          )}
                          {day.exercises?.map((ex, i) => (
                            <div key={i} className="bg-[#0d0d14] rounded-lg p-4 flex items-center justify-between">
                              <div>
                                <p className="text-white font-medium">{ex.name}</p>
                                <p className="text-gray-500 text-xs mt-1">{ex.description}</p>
                              </div>
                              <div className="flex gap-2">
                                <span className="bg-purple-600/20 text-purple-300 px-2 py-1 rounded text-xs">{ex.sets}×{ex.reps}</span>
                                <span className="bg-orange-600/20 text-orange-300 px-2 py-1 rounded text-xs">{ex.rest_seconds}s</span>
                              </div>
                            </div>
                          ))}
                          {day.cool_down && (
                            <p className="text-gray-400 text-sm">🧊 Cool Down: {day.cool_down}</p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-16">
              <div className="text-6xl mb-4">🏋️</div>
              <h2 className="text-2xl font-bold text-white mb-2">No Workout Plan Yet</h2>
              <p className="text-gray-400 mb-6">Generate your first personalized workout plan</p>
              <button
                onClick={handleGeneratePlan}
                disabled={generating}
                className="px-8 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition disabled:opacity-50"
              >
                {generating ? 'Generating...' : '✨ Generate Plan'}
              </button>
            </div>
          )}

          {/* Exercise Player Modal */}
          {playerExercise && (
            <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
              <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-[#2a2a40]">
                  <div>
                    <h2 className="text-2xl font-bold text-white">{playerExercise.name}</h2>
                    <p className="text-gray-400 text-sm mt-1">{playerExercise.description}</p>
                  </div>
                  <button onClick={() => setPlayerExercise(null)} className="text-gray-400 hover:text-white p-2">
                    <X className="w-6 h-6" />
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
                  {/* YouTube Video */}
                  <VideoPlayer exerciseName={playerExercise.youtube_search_query || playerExercise.name} />

                  {/* Exercise Details */}
                  <div className="space-y-4">
                    <h3 className="text-white font-semibold">💪 Exercise Details</h3>

                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-purple-600/20 rounded-xl p-4 text-center">
                        <p className="text-2xl font-bold text-purple-300">{playerExercise.sets}</p>
                        <p className="text-gray-400 text-xs">Sets</p>
                      </div>
                      <div className="bg-blue-600/20 rounded-xl p-4 text-center">
                        <p className="text-2xl font-bold text-blue-300">{playerExercise.reps}</p>
                        <p className="text-gray-400 text-xs">Reps</p>
                      </div>
                      <div className="bg-orange-600/20 rounded-xl p-4 text-center">
                        <p className="text-2xl font-bold text-orange-300">{playerExercise.rest_seconds}s</p>
                        <p className="text-gray-400 text-xs">Rest</p>
                      </div>
                    </div>

                    <div className="bg-[#0d0d14] rounded-xl p-4">
                      <h4 className="text-white font-medium mb-2">Pro Tips</h4>
                      <ul className="text-gray-400 text-sm space-y-2">
                        <li>• Focus on proper form over speed</li>
                        <li>• Breathe steadily throughout</li>
                        <li>• Stop if you feel sharp pain</li>
                        <li>• Keep core engaged for stability</li>
                      </ul>
                    </div>

                    <button
                      onClick={() => setShowCamera(true)}
                      className="w-full py-3 bg-gradient-to-r from-purple-600 to-orange-500 hover:from-purple-700 hover:to-orange-600 text-white rounded-xl font-semibold transition flex items-center justify-center gap-2"
                    >
                      <Camera className="w-4 h-4" /> Track with Camera
                    </button>

                    <button
                      onClick={() => {
                        handleCompleteExercise(playerExercise.name)
                        setPlayerExercise(null)
                      }}
                      className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-semibold transition"
                    >
                      ✅ Mark Complete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Camera Motion Tracker */}
      {showCamera && playerExercise && (
        <ExerciseCamera
          exerciseName={playerExercise.name}
          targetReps={parseInt(playerExercise.reps) || 12}
          onComplete={() => {
            handleCompleteExercise(playerExercise.name)
            setShowCamera(false)
            setPlayerExercise(null)
            toast.success('Exercise completed with camera tracking! 🎥💪')
          }}
          onClose={() => setShowCamera(false)}
        />
      )}
    </>
  )
}

function VideoPlayer({ exerciseName }) {
  const [videoId, setVideoId] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    workoutApi.youtubeSearch(exerciseName + ' exercise proper form')
      .then(res => {
        if (!cancelled && res.data?.video_id) {
          setVideoId(res.data.video_id)
        }
      })
      .catch(() => { })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [exerciseName])

  const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(exerciseName + ' exercise proper form')}`

  return (
    <div>
      <h3 className="text-white font-semibold mb-3">📺 Tutorial Video</h3>
      <div className="aspect-video bg-black rounded-xl overflow-hidden">
        {loading ? (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
              <p className="text-sm">Loading video...</p>
            </div>
          </div>
        ) : videoId ? (
          <iframe
            width="100%"
            height="100%"
            src={`https://www.youtube.com/embed/${videoId}`}
            title={exerciseName}
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="rounded-xl"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-lg mb-2">🎥</p>
              <p className="text-sm mb-3">Video preview not available</p>
              <a href={searchUrl} target="_blank" rel="noopener noreferrer"
                className="text-purple-400 hover:text-purple-300 text-sm underline">
                Watch on YouTube →
              </a>
            </div>
          </div>
        )}
      </div>
      <a href={searchUrl} target="_blank" rel="noopener noreferrer"
        className="text-purple-400 hover:text-purple-300 text-sm mt-2 inline-block">
        🔗 Search more videos on YouTube →
      </a>
    </div>
  )
}
