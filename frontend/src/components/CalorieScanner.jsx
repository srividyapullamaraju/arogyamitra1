import { useState, useRef } from 'react'
import { Camera, X, Upload, Loader2 } from 'lucide-react'
import api from '../services/api'

export default function CalorieScanner({ isOpen, onClose }) {
    const [image, setImage] = useState(null)
    const [preview, setPreview] = useState(null)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const fileRef = useRef(null)

    const handleFile = (e) => {
        const file = e.target.files?.[0]
        if (!file) return
        setImage(file)
        setPreview(URL.createObjectURL(file))
        setResult(null)
    }

    const handleAnalyze = async () => {
        if (!image) return
        setLoading(true)
        try {
            const formData = new FormData()
            formData.append('image', image)
            const res = await api.post('/api/calories/scan', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            setResult(res.data)
        } catch (err) {
            setResult({ food_name: 'Error', total_calories: 0, health_tip: 'Could not analyze. Try again.', items: [] })
        } finally {
            setLoading(false)
        }
    }

    const handleReset = () => {
        setImage(null)
        setPreview(null)
        setResult(null)
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-[#1a1a2e] border border-[#2a2a40] rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b border-[#2a2a40]">
                    <div className="flex items-center gap-2">
                        <Camera className="w-5 h-5 text-orange-400" />
                        <h2 className="text-lg font-bold text-white">Calorie Scanner</h2>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="p-5 space-y-4">
                    {/* Upload area */}
                    {!preview ? (
                        <div
                            onClick={() => fileRef.current?.click()}
                            className="border-2 border-dashed border-[#3a3a50] rounded-xl p-8 text-center cursor-pointer hover:border-orange-500/50 transition group"
                        >
                            <Upload className="w-10 h-10 text-gray-500 mx-auto mb-3 group-hover:text-orange-400 transition" />
                            <p className="text-gray-400 text-sm mb-1">Tap to upload a food photo</p>
                            <p className="text-gray-500 text-xs">JPG, PNG — Max 10MB</p>
                            <input
                                ref={fileRef}
                                type="file"
                                accept="image/*"
                                capture="environment"
                                onChange={handleFile}
                                className="hidden"
                            />
                        </div>
                    ) : (
                        <div className="relative">
                            <img src={preview} alt="Food" className="w-full rounded-xl object-cover max-h-64" />
                            {!loading && !result && (
                                <button
                                    onClick={handleReset}
                                    className="absolute top-2 right-2 bg-black/60 p-1.5 rounded-full hover:bg-red-600/80 transition"
                                >
                                    <X className="w-4 h-4 text-white" />
                                </button>
                            )}
                        </div>
                    )}

                    {/* Analyze button */}
                    {preview && !result && (
                        <button
                            onClick={handleAnalyze}
                            disabled={loading}
                            className="w-full py-3 bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white rounded-xl font-semibold transition disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Analyzing...
                                </>
                            ) : (
                                '🔍 Analyze Calories'
                            )}
                        </button>
                    )}

                    {/* Results */}
                    {result && (
                        <div className="space-y-3 animate-in fade-in">
                            {/* Total */}
                            <div className="bg-gradient-to-r from-orange-600/20 to-red-600/20 border border-orange-500/30 rounded-xl p-4 text-center">
                                <p className="text-orange-300 text-sm mb-1">{result.food_name}</p>
                                <p className="text-4xl font-bold text-white">{result.total_calories}</p>
                                <p className="text-gray-400 text-sm">calories</p>
                            </div>

                            {/* Macros grid */}
                            <div className="grid grid-cols-3 gap-2">
                                <div className="bg-[#0d0d14] rounded-lg p-3 text-center">
                                    <p className="text-blue-400 font-bold">{result.total_protein_g || 0}g</p>
                                    <p className="text-gray-500 text-xs">Protein</p>
                                </div>
                                <div className="bg-[#0d0d14] rounded-lg p-3 text-center">
                                    <p className="text-green-400 font-bold">{result.total_carbs_g || 0}g</p>
                                    <p className="text-gray-500 text-xs">Carbs</p>
                                </div>
                                <div className="bg-[#0d0d14] rounded-lg p-3 text-center">
                                    <p className="text-yellow-400 font-bold">{result.total_fat_g || 0}g</p>
                                    <p className="text-gray-500 text-xs">Fat</p>
                                </div>
                            </div>

                            {/* Individual items */}
                            {result.items?.length > 0 && (
                                <div className="space-y-1.5">
                                    <p className="text-gray-400 text-xs font-medium uppercase tracking-wider">Breakdown</p>
                                    {result.items.map((item, i) => (
                                        <div key={i} className="bg-[#0d0d14] rounded-lg px-3 py-2 flex justify-between items-center">
                                            <span className="text-gray-300 text-sm">{item.name}</span>
                                            <span className="text-orange-300 text-sm font-medium">{item.calories} cal</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Health tip */}
                            {result.health_tip && (
                                <div className="bg-green-600/10 border border-green-600/20 rounded-lg p-3">
                                    <p className="text-green-300 text-sm">💡 {result.health_tip}</p>
                                </div>
                            )}

                            {/* Scan again */}
                            <button
                                onClick={handleReset}
                                className="w-full py-2.5 bg-[#2a2a40] hover:bg-[#3a3a50] text-white rounded-xl text-sm font-medium transition"
                            >
                                📸 Scan Another Meal
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
