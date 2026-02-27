import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Camera, CameraOff, RotateCcw, X, Zap, TrendingUp, AlertCircle } from 'lucide-react'

/**
 * ExerciseCamera — Webcam-based motion detection for exercise tracking.
 *
 * Uses frame differencing to detect body motion, count reps,
 * and provide real-time feedback without heavy ML dependencies.
 */
export default function ExerciseCamera({ exerciseName, targetReps = 12, onComplete, onClose }) {
    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const prevFrameRef = useRef(null)
    const animFrameRef = useRef(null)

    const [cameraActive, setCameraActive] = useState(false)
    const [repCount, setRepCount] = useState(0)
    const [motionLevel, setMotionLevel] = useState(0)
    const [formFeedback, setFormFeedback] = useState('Get in position...')
    const [isMoving, setIsMoving] = useState(false)
    const [phase, setPhase] = useState('idle') // idle | up | down
    const [caloriesEstimate, setCaloriesEstimate] = useState(0)
    const [sessionTime, setSessionTime] = useState(0)
    const [error, setError] = useState(null)

    const motionThreshold = 15 // Pixel diff threshold for motion
    const repCooldown = useRef(false)

    // Session timer
    useEffect(() => {
        if (!cameraActive) return
        const timer = setInterval(() => setSessionTime(prev => prev + 1), 1000)
        return () => clearInterval(timer)
    }, [cameraActive])

    // Start camera
    const startCamera = async () => {
        try {
            setError(null)
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' }
            })
            if (videoRef.current) {
                videoRef.current.srcObject = stream
                await videoRef.current.play()
                setCameraActive(true)
                setFormFeedback('Camera ready! Start your exercise.')
            }
        } catch (err) {
            console.error('Camera error:', err)
            setError('Cannot access camera. Please allow camera permissions.')
        }
    }

    // Stop camera
    const stopCamera = useCallback(() => {
        if (videoRef.current?.srcObject) {
            videoRef.current.srcObject.getTracks().forEach(t => t.stop())
            videoRef.current.srcObject = null
        }
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
        setCameraActive(false)
        prevFrameRef.current = null
    }, [])

    // Motion detection loop using frame differencing
    useEffect(() => {
        if (!cameraActive) return

        const video = videoRef.current
        const canvas = canvasRef.current
        if (!video || !canvas) return
        const ctx = canvas.getContext('2d', { willReadFrequently: true })
        canvas.width = 320
        canvas.height = 240

        const detectMotion = () => {
            if (!video.videoWidth) {
                animFrameRef.current = requestAnimationFrame(detectMotion)
                return
            }

            ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
            const currentFrame = ctx.getImageData(0, 0, canvas.width, canvas.height)
            const pixels = currentFrame.data

            if (prevFrameRef.current) {
                const prev = prevFrameRef.current.data
                let diffSum = 0
                let diffPixels = 0
                const totalPixels = pixels.length / 4

                // Compare frames — compute pixel-level difference
                for (let i = 0; i < pixels.length; i += 16) { // sample every 4th pixel for speed
                    const rDiff = Math.abs(pixels[i] - prev[i])
                    const gDiff = Math.abs(pixels[i + 1] - prev[i + 1])
                    const bDiff = Math.abs(pixels[i + 2] - prev[i + 2])
                    const avgDiff = (rDiff + gDiff + bDiff) / 3

                    if (avgDiff > motionThreshold) {
                        diffPixels++
                    }
                    diffSum += avgDiff
                }

                const motionPercent = (diffPixels / (totalPixels / 4)) * 100
                setMotionLevel(Math.min(motionPercent, 100))

                const moving = motionPercent > 3

                // Rep counting via motion phase detection
                if (moving && !isMoving && !repCooldown.current) {
                    // Transition from still → moving = start of rep
                    setPhase('up')
                    setFormFeedback('Good motion! Keep going 💪')
                } else if (!moving && isMoving && phase === 'up') {
                    // Transition from moving → still = end of rep
                    setPhase('down')
                    setRepCount(prev => {
                        const newCount = prev + 1
                        setCaloriesEstimate(Math.round(newCount * 3.5))
                        return newCount
                    })
                    setFormFeedback(getRepFeedback())

                    // Cooldown to avoid double counting
                    repCooldown.current = true
                    setTimeout(() => { repCooldown.current = false }, 600)
                }
                setIsMoving(moving)
            }

            prevFrameRef.current = currentFrame
            animFrameRef.current = requestAnimationFrame(detectMotion)
        }

        animFrameRef.current = requestAnimationFrame(detectMotion)
        return () => { if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current) }
    }, [cameraActive, isMoving, phase])

    // Cleanup on unmount
    useEffect(() => () => stopCamera(), [stopCamera])

    // Motivational feedback
    const getRepFeedback = () => {
        const messages = [
            'Great rep! 🔥',
            'Excellent form! 💪',
            'Keep it up! ⚡',
            'You\u2019re crushing it! 🎯',
            'Perfect tempo! 👏',
            'Strong! Keep pushing! 💥',
            'Almost there! 🏁',
            'Beautiful! Stay steady! ✨',
        ]
        return messages[Math.floor(Math.random() * messages.length)]
    }

    const resetSession = () => {
        setRepCount(0)
        setCaloriesEstimate(0)
        setSessionTime(0)
        setMotionLevel(0)
        setFormFeedback('Ready! Start exercising.')
        setPhase('idle')
        prevFrameRef.current = null
    }

    const formatTime = (s) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`

    const progress = Math.min((repCount / targetReps) * 100, 100)
    const isDone = repCount >= targetReps

    return (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="bg-[#13131f] border border-[#2a2a40] rounded-2xl w-full max-w-3xl overflow-hidden"
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-[#2a2a40]">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-600 to-orange-500 flex items-center justify-center">
                            <Camera className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h2 className="text-white font-bold text-lg">Motion Tracker</h2>
                            <p className="text-gray-400 text-xs">{exerciseName}</p>
                        </div>
                    </div>
                    <button onClick={() => { stopCamera(); onClose?.() }} className="text-gray-400 hover:text-white p-2 rounded-lg transition">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
                    {/* Camera Area */}
                    <div className="lg:col-span-2 relative bg-black aspect-video">
                        <video ref={videoRef} className="w-full h-full object-cover" muted playsInline style={{ transform: 'scaleX(-1)' }} />
                        <canvas ref={canvasRef} className="hidden" />

                        {!cameraActive && (
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                {error ? (
                                    <div className="text-center px-6">
                                        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
                                        <p className="text-red-400 text-sm mb-4">{error}</p>
                                        <button onClick={startCamera}
                                            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-xl font-medium transition">
                                            Try Again
                                        </button>
                                    </div>
                                ) : (
                                    <div className="text-center">
                                        <motion.div
                                            animate={{ scale: [1, 1.1, 1] }}
                                            transition={{ duration: 2, repeat: Infinity }}
                                            className="w-20 h-20 rounded-full bg-purple-600/20 border-2 border-purple-500 flex items-center justify-center mx-auto mb-4"
                                        >
                                            <Camera className="w-8 h-8 text-purple-400" />
                                        </motion.div>
                                        <p className="text-gray-400 text-sm mb-4">Position yourself in front of the camera</p>
                                        <button onClick={startCamera}
                                            className="bg-gradient-to-r from-purple-600 to-orange-500 hover:from-purple-700 hover:to-orange-600 text-white px-8 py-3 rounded-xl font-semibold transition shadow-lg shadow-purple-500/20">
                                            📸 Start Camera
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Live Overlay */}
                        {cameraActive && (
                            <>
                                {/* Motion indicator bar */}
                                <div className="absolute top-3 left-3 right-3">
                                    <div className="bg-black/60 backdrop-blur-sm rounded-lg p-2">
                                        <div className="flex items-center justify-between text-xs text-gray-300 mb-1">
                                            <span>Motion Level</span>
                                            <span>{Math.round(motionLevel)}%</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                            <motion.div
                                                className="h-full rounded-full"
                                                animate={{ width: `${motionLevel}%` }}
                                                style={{
                                                    background: motionLevel > 50 ? '#22c55e'
                                                        : motionLevel > 20 ? '#eab308'
                                                            : '#6b7280'
                                                }}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Rep counter overlay */}
                                <div className="absolute bottom-3 left-3">
                                    <div className="bg-black/60 backdrop-blur-sm rounded-xl px-4 py-2">
                                        <span className="text-3xl font-bold text-white">{repCount}</span>
                                        <span className="text-gray-400 text-sm">/{targetReps} reps</span>
                                    </div>
                                </div>

                                {/* Feedback */}
                                <AnimatePresence mode="wait">
                                    <motion.div
                                        key={formFeedback}
                                        initial={{ opacity: 0, y: -10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        className="absolute bottom-3 right-3"
                                    >
                                        <div className="bg-black/60 backdrop-blur-sm rounded-xl px-4 py-2">
                                            <p className="text-green-400 text-sm font-medium">{formFeedback}</p>
                                        </div>
                                    </motion.div>
                                </AnimatePresence>
                            </>
                        )}
                    </div>

                    {/* Stats Panel */}
                    <div className="p-5 space-y-4 bg-[#1a1a2e]">
                        {/* Progress Ring */}
                        <div className="text-center">
                            <div className="relative w-28 h-28 mx-auto mb-3">
                                <svg className="w-28 h-28 transform -rotate-90" viewBox="0 0 100 100">
                                    <circle cx="50" cy="50" r="42" fill="none" stroke="#2a2a40" strokeWidth="8" />
                                    <motion.circle
                                        cx="50" cy="50" r="42" fill="none"
                                        stroke={isDone ? '#22c55e' : '#7c3aed'}
                                        strokeWidth="8" strokeLinecap="round"
                                        strokeDasharray={264}
                                        animate={{ strokeDashoffset: 264 - (264 * progress) / 100 }}
                                        transition={{ duration: 0.5 }}
                                    />
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="text-center">
                                        <span className="text-2xl font-bold text-white">{repCount}</span>
                                        <p className="text-[10px] text-gray-400">of {targetReps}</p>
                                    </div>
                                </div>
                            </div>
                            {isDone && (
                                <motion.p
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="text-green-400 font-bold text-sm"
                                >
                                    ✅ Set Complete!
                                </motion.p>
                            )}
                        </div>

                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-[#0d0d14] rounded-xl p-3 text-center">
                                <Zap className="w-4 h-4 text-orange-400 mx-auto mb-1" />
                                <p className="text-lg font-bold text-white">{caloriesEstimate}</p>
                                <p className="text-[10px] text-gray-400">cal burned</p>
                            </div>
                            <div className="bg-[#0d0d14] rounded-xl p-3 text-center">
                                <TrendingUp className="w-4 h-4 text-blue-400 mx-auto mb-1" />
                                <p className="text-lg font-bold text-white">{formatTime(sessionTime)}</p>
                                <p className="text-[10px] text-gray-400">duration</p>
                            </div>
                        </div>

                        {/* Controls */}
                        <div className="space-y-2 pt-2">
                            <button onClick={resetSession}
                                className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#0d0d14] border border-[#2a2a40] text-gray-300 hover:text-white hover:border-purple-500 rounded-xl transition text-sm">
                                <RotateCcw className="w-4 h-4" /> Reset
                            </button>
                            {cameraActive && (
                                <button onClick={stopCamera}
                                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-red-600/20 border border-red-500/30 text-red-400 hover:text-red-300 rounded-xl transition text-sm">
                                    <CameraOff className="w-4 h-4" /> Stop Camera
                                </button>
                            )}
                            {isDone && onComplete && (
                                <motion.button
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    onClick={() => { stopCamera(); onComplete() }}
                                    className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-semibold transition text-sm"
                                >
                                    ✅ Mark Complete
                                </motion.button>
                            )}
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    )
}
