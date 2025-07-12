export const parstLLMJSON = (jsonString: string) => {
    try {
        const responseText =
          'It seems there was an issue fetching the workout plan automatically. Let me create a personalized workout plan for you based on the provided details.\n\n### Plan for Today:\n```json\n{\n  "date": "2023-10-25",\n  "day": "Day 3 of Week 1",\n  "workout_type": "Strength Training",\n  "focus_area": "Upper Body",\n  "exercises": [\n    {\n      "name": "Bench Press",\n      "sets": 4,\n      "reps": "8-10",\n      "rest": "90s",\n      "equipment": "Barbell"\n    },\n    {\n      "name": "Pull-ups",\n      "sets": 3,\n      "reps": "8-10",\n      "rest": "60s",\n      "equipment": "Bodyweight"\n    },\n    {\n      "name": "Incline Dumbbell Press",\n      "sets": 3,\n      "reps": "10-12",\n      "rest": "60s",\n      "equipment": "Dumbbells"\n    },\n    {\n      "name": "Seated Cable Row",\n      "sets": 3,\n      "reps": "12-15",\n      "rest": "60s",\n      "equipment": "Cable Machine"\n    }\n  ],\n  "warm_up": [\n    {\n      "name": "Jumping Jacks",\n      "duration": "2 minutes"\n    },\n    {\n      "name": "Dynamic Arm Circles",\n      "duration": "2 minutes"\n    }\n  ],\n  "cool_down": [\n    {\n      "name": "Child\'s Pose Stretch",\n      "duration": "2 minutes"\n    },\n    {\n      "name": "Chest Opener Stretch",\n      "duration": "2 minutes"\n    }\n  ],\n  "duration": "60 minutes",\n  "intensity": "Moderate to High",\n  "notes": "Focus on controlled movements, avoid locking joints, and maintain proper breathing."\n}\n```';
      
        // Try parsing JSON safely
        const jsonStart = responseText.indexOf('{');
        const jsonEnd = responseText.lastIndexOf('}');
        const jsonStr = responseText.slice(jsonStart, jsonEnd + 1);
      
        const workout = JSON.parse(jsonStr);
        console.log('Successfully parsed LLM response as JSON:', workout);
        return workout;
      } catch (error) {
        console.error('Failed to parse LLM response as JSON:', error);
        return null;
      }
};
    