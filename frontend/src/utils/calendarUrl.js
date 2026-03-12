/**
 * Google Calendar URL generator — no API keys needed!
 * Opens Google Calendar with pre-filled event details.
 * User clicks "Save" to add it to their calendar.
 */

/**
 * Generate a Google Calendar event URL
 * @param {Object} opts
 * @param {string} opts.title - Event title
 * @param {string} opts.details - Event description
 * @param {Date} opts.start - Start date/time
 * @param {Date} opts.end - End date/time
 * @param {string} [opts.location] - Optional location
 * @returns {string} Google Calendar URL
 */
export function createCalendarUrl({ title, details, start, end, location = '' }) {
    const fmt = (d) => d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')

    const params = new URLSearchParams({
        action: 'TEMPLATE',
        text: title,
        dates: `${fmt(start)}/${fmt(end)}`,
        details: details,
    })

    if (location) params.set('location', location)

    return `https://calendar.google.com/calendar/render?${params.toString()}`
}

/**
 * Generate calendar URL for a workout day
 */
export function workoutToCalendarUrl(day, dateOffset = 0) {
    const date = new Date()
    date.setDate(date.getDate() + dateOffset)

    const start = new Date(date)
    start.setHours(7, 0, 0, 0) // default 7 AM

    const end = new Date(date)
    end.setHours(7, (day.duration_minutes || 45), 0, 0)

    const exercises = day.exercises?.map(e => `• ${e.name} — ${e.sets}×${e.reps}`).join('\n') || ''

    return createCalendarUrl({
        title: `🏋️ ${day.focus_area || 'Workout'} — ArogyaMitra`,
        details: `${day.warmup ? `Warmup: ${day.warmup}\n\n` : ''}Exercises:\n${exercises}${day.cool_down ? `\n\nCool Down: ${day.cool_down}` : ''}${day.daily_tip ? `\n\n💡 ${day.daily_tip}` : ''}`,
        start,
        end,
        location: 'Home / Gym',
    })
}

/**
 * Generate calendar URL for a nutrition/meal day
 */
export function mealToCalendarUrl(mealName, meal, dateOffset = 0) {
    const date = new Date()
    date.setDate(date.getDate() + dateOffset)

    const hours = { breakfast: 8, lunch: 13, snack: 16, dinner: 20 }
    const h = hours[mealName.toLowerCase()] || 12

    const start = new Date(date)
    start.setHours(h, 0, 0, 0)

    const end = new Date(date)
    end.setHours(h, 30, 0, 0)

    const items = Array.isArray(meal.items)
        ? meal.items.join(', ')
        : typeof meal === 'string' ? meal : meal.name || mealName

    return createCalendarUrl({
        title: `🥗 ${mealName} — ArogyaMitra`,
        details: `${items}\n\n${meal.calories ? `Calories: ${meal.calories} kcal` : ''}${meal.protein_g ? ` | Protein: ${meal.protein_g}g` : ''}`,
        start,
        end,
    })
}

/**
 * Sync entire week — opens multiple tabs (user approves each)
 */
export function syncWeekToCalendar(days) {
    days.forEach((day, idx) => {
        if (!day.rest_day) {
            setTimeout(() => {
                window.open(workoutToCalendarUrl(day, idx), '_blank')
            }, idx * 500) // stagger to avoid popup blocker
        }
    })
}
