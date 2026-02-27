import { useEffect, useState } from 'react'
import { Check, ShoppingCart, ExternalLink } from 'lucide-react'
import Navbar from '../components/Navbar'
import { nutritionApi } from '../services/api'
import toast from 'react-hot-toast'

const mealColors = {
  Breakfast: { bg: 'bg-orange-600/15', border: 'border-orange-600/30', text: 'text-orange-400', icon: '🌅' },
  Lunch: { bg: 'bg-yellow-600/15', border: 'border-yellow-600/30', text: 'text-yellow-400', icon: '☀️' },
  Dinner: { bg: 'bg-blue-600/15', border: 'border-blue-600/30', text: 'text-blue-400', icon: '🌙' },
  Snacks: { bg: 'bg-green-600/15', border: 'border-green-600/30', text: 'text-green-400', icon: '🍎' },
}

export default function NutritionPlans() {
  const [plan, setPlan] = useState(null)
  const [todayMeals, setTodayMeals] = useState(null)
  const [todayName, setTodayName] = useState('')
  const [shoppingList, setShoppingList] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [activeTab, setActiveTab] = useState('today')
  const [completedMeals, setCompletedMeals] = useState(new Set())
  const [expandedDay, setExpandedDay] = useState(null)

  useEffect(() => {
    loadNutrition()
  }, [])

  const loadNutrition = async () => {
    try {
      const [planRes, todayRes, shoppingRes] = await Promise.all([
        nutritionApi.getCurrent().catch(() => ({ data: null })),
        nutritionApi.getToday().catch(() => ({ data: { today: null, day_name: '' } })),
        nutritionApi.getShoppingList().catch(() => ({ data: { shopping_list: [] } }))
      ])
      setPlan(planRes.data?.plan || null)
      setTodayMeals(todayRes.data?.today || null)
      setTodayName(todayRes.data?.day_name || '')
      setShoppingList(shoppingRes.data?.shopping_list || [])
    } catch (error) {
      console.error('Error loading nutrition:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleGeneratePlan = async () => {
    setGenerating(true)
    try {
      toast.loading('Generating nutrition plan... 🥗', { id: 'gen' })
      await nutritionApi.generate({ calorie_target: 1800, diet_type: 'balanced', allergies: '' })
      toast.success('New nutrition plan generated! 🥗', { id: 'gen' })
      await loadNutrition()
    } catch (error) {
      toast.error('Failed to generate plan', { id: 'gen' })
    } finally {
      setGenerating(false)
    }
  }

  const handleCompleteMeal = async (mealType) => {
    try {
      await nutritionApi.completeMeal({ meal_id: mealType, meal_type: mealType })
      setCompletedMeals(prev => new Set([...prev, mealType]))
      toast.success('Meal tracked! +2 charity points 💚')
    } catch (error) {
      toast.error('Failed to log meal')
    }
  }

  const days = plan?.days || []

  const MealCard = ({ mealType, meal }) => {
    if (!meal) return null
    const color = mealColors[mealType] || mealColors.Breakfast
    const isCompleted = completedMeals.has(mealType.toLowerCase())

    return (
      <div className={`${color.bg} border ${color.border} rounded-xl p-5`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xl">{color.icon}</span>
            <div>
              <h3 className={`font-semibold ${color.text}`}>{mealType}</h3>
              <p className="text-gray-400 text-xs">{meal.time}</p>
            </div>
          </div>
          <button
            onClick={() => !isCompleted && handleCompleteMeal(mealType.toLowerCase())}
            className={`w-7 h-7 rounded-lg border-2 flex items-center justify-center transition ${isCompleted ? 'bg-green-600 border-green-500' : 'border-gray-500 hover:border-green-500'
              }`}
          >
            {isCompleted && <Check className="w-4 h-4 text-white" />}
          </button>
        </div>

        <h4 className="text-white font-bold text-lg mb-3">{meal.name}</h4>

        <div className="grid grid-cols-4 gap-2 mb-3">
          <div className="bg-black/20 rounded-lg p-2 text-center">
            <p className="text-orange-300 font-bold text-sm">{meal.calories}</p>
            <p className="text-gray-500 text-xs">Cal</p>
          </div>
          <div className="bg-black/20 rounded-lg p-2 text-center">
            <p className="text-blue-300 font-bold text-sm">{meal.protein_g || meal.protein || 0}g</p>
            <p className="text-gray-500 text-xs">Protein</p>
          </div>
          <div className="bg-black/20 rounded-lg p-2 text-center">
            <p className="text-green-300 font-bold text-sm">{meal.carbs_g || meal.carbs || 0}g</p>
            <p className="text-gray-500 text-xs">Carbs</p>
          </div>
          <div className="bg-black/20 rounded-lg p-2 text-center">
            <p className="text-yellow-300 font-bold text-sm">{meal.fat_g || meal.fats || 0}g</p>
            <p className="text-gray-500 text-xs">Fat</p>
          </div>
        </div>

        {meal.ingredients && (
          <div className="flex flex-wrap gap-1">
            {(Array.isArray(meal.ingredients) ? meal.ingredients : [meal.ingredients]).map((ing, i) => (
              <span key={i} className="bg-black/20 text-gray-300 px-2 py-1 rounded text-xs">
                {ing}
              </span>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-[#0d0d14] pt-16 flex items-center justify-center">
          <div className="text-white text-xl">Loading nutrition plan...</div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-[#0d0d14] pt-16">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">🇮🇳 Indian Nutrition Plans</h1>
              <p className="text-gray-400">AI-powered traditional Indian meal planning for optimal nutrition 💚</p>
            </div>
            <button
              onClick={handleGeneratePlan}
              disabled={generating}
              className="px-6 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition disabled:opacity-50"
            >
              {generating ? 'Generating...' : '✨ Generate New Plan'}
            </button>
          </div>

          {plan ? (
            <>
              {/* Tab Switcher */}
              <div className="flex gap-2 mb-6">
                {[
                  { id: 'today', label: '🌅 Today' },
                  { id: 'week', label: '📅 This Week' },
                  { id: 'shopping', label: '🛒 Shopping List' },
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-6 py-3 rounded-xl font-medium transition ${activeTab === tab.id
                        ? 'bg-orange-600 text-white'
                        : 'bg-[#1a1a2e] border border-[#2a2a40] text-gray-400 hover:text-white'
                      }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* TODAY TAB */}
              {activeTab === 'today' && todayMeals && (
                <div className="space-y-4">
                  <div className="bg-gradient-to-r from-orange-600 to-red-600 rounded-xl p-6 mb-4">
                    <h2 className="text-2xl font-bold text-white">{todayName}'s Meals</h2>
                    <p className="text-white/80">Total: {todayMeals.total_calories || '~1800'} calories</p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <MealCard mealType="Breakfast" meal={todayMeals.breakfast} />
                    <MealCard mealType="Lunch" meal={todayMeals.lunch} />
                    <MealCard mealType="Dinner" meal={todayMeals.dinner} />
                    {todayMeals.snacks && (
                      <div className={`${mealColors.Snacks.bg} border ${mealColors.Snacks.border} rounded-xl p-5`}>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-xl">🍎</span>
                          <h3 className="font-semibold text-green-400">Snacks</h3>
                        </div>
                        <div className="space-y-2">
                          {todayMeals.snacks.map((snack, i) => (
                            <div key={i} className="flex justify-between items-center bg-black/20 rounded-lg p-3">
                              <span className="text-white">{snack.name}</span>
                              <span className="text-green-300 text-sm">{snack.calories} cal</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'today' && !todayMeals && (
                <div className="text-center py-12 bg-[#1a1a2e] border border-[#2a2a40] rounded-xl">
                  <p className="text-gray-400">Today's meal data not available.</p>
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
                        <span className="text-white font-bold text-lg">{day.day}</span>
                        <span className="text-gray-400 text-sm">{day.total_calories} cal</span>
                      </button>
                      {expandedDay === idx && (
                        <div className="px-5 pb-5 border-t border-[#2a2a40] pt-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <MealCard mealType="Breakfast" meal={day.breakfast} />
                            <MealCard mealType="Lunch" meal={day.lunch} />
                            <MealCard mealType="Dinner" meal={day.dinner} />
                            {day.snacks && (
                              <div className="bg-green-600/10 border border-green-600/20 rounded-xl p-4">
                                <h4 className="text-green-400 font-semibold mb-2">🍎 Snacks</h4>
                                {day.snacks.map((s, si) => (
                                  <p key={si} className="text-gray-300 text-sm">{s.name} — {s.calories} cal</p>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* SHOPPING LIST TAB */}
              {activeTab === 'shopping' && (
                <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-6">
                    <ShoppingCart className="w-6 h-6 text-purple-400" />
                    <h2 className="text-2xl font-bold text-white">Weekly Shopping List</h2>
                  </div>
                  {shoppingList.length > 0 ? (
                    <div className="space-y-2">
                      {shoppingList.map((item, idx) => (
                        <div key={idx} className="bg-[#0d0d14] rounded-lg p-4 flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-green-400">✅</span>
                            <span className="text-gray-200 capitalize">{item.ingredient || item.name}</span>
                            <span className="text-gray-500 text-sm">×{item.count || item.quantity || 1}</span>
                          </div>
                          <a
                            href={`https://www.bigbasket.com/ps/?q=${encodeURIComponent(item.ingredient || item.name)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg text-sm transition"
                          >
                            Buy 🛒
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-400 text-center py-8">No items in shopping list. Generate a plan first.</p>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-16">
              <div className="text-6xl mb-4">🥗</div>
              <h2 className="text-2xl font-bold text-white mb-2">No Nutrition Plan Yet</h2>
              <p className="text-gray-400 mb-6">Generate your first personalized Indian meal plan</p>
              <button
                onClick={handleGeneratePlan}
                disabled={generating}
                className="px-8 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition disabled:opacity-50"
              >
                {generating ? 'Generating...' : '✨ Generate Plan'}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
