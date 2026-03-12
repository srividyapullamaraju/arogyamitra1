import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Home, Dumbbell, Apple, TrendingUp, LogOut, Sparkles, Camera } from 'lucide-react'
import useAuthStore from '../stores/authStore'
import CalorieScanner from './CalorieScanner'

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [showScanner, setShowScanner] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (!isAuthenticated) return null

  const links = [
    { to: '/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/workouts', icon: Dumbbell, label: 'Workouts' },
    { to: '/nutrition', icon: Apple, label: 'Nutrition' },
    { to: '/progress', icon: TrendingUp, label: 'Progress' },
  ]

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#1a1a2e]/95 backdrop-blur-sm border-b border-[#2a2a40]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/dashboard" className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-400" />
              <span className="text-xl font-bold text-white">ArogyaMitra</span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {links.map(({ to, icon: Icon, label }) => {
                const isActive = location.pathname === to
                return (
                  <Link
                    key={to}
                    to={to}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${isActive
                        ? 'bg-purple-600 text-white'
                        : 'text-gray-300 hover:bg-[#2a2a40] hover:text-white'
                      }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{label}</span>
                  </Link>
                )
              })}
            </div>

            <div className="flex items-center gap-3">
              {/* Calorie Scanner Button */}
              <button
                onClick={() => setShowScanner(true)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-orange-600/20 border border-orange-500/30 text-orange-400 hover:bg-orange-600/30 hover:text-orange-300 transition"
                title="Scan food for calories"
              >
                <Camera className="w-4 h-4" />
                <span className="text-xs font-medium hidden sm:inline">Calorie Scan</span>
              </button>

              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-white">{user?.full_name || user?.username}</p>
                <p className="text-xs text-gray-400">💚 {user?.charity_donations || 0} points</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-300 hover:bg-red-900/30 hover:text-red-400 transition"
              >
                <LogOut className="w-4 h-4" />
                <span className="text-sm hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>

          {/* Mobile nav */}
          <div className="md:hidden flex items-center gap-1 pb-3 overflow-x-auto">
            {links.map(({ to, icon: Icon, label }) => {
              const isActive = location.pathname === to
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg transition whitespace-nowrap ${isActive
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-300 hover:bg-[#2a2a40]'
                    }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-xs">{label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Calorie Scanner Modal */}
      <CalorieScanner isOpen={showScanner} onClose={() => setShowScanner(false)} />
    </>
  )
}
