#!/bin/bash

curl -X 'POST' \
  'http://localhost:4201/api/workout-plan' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "userId": "user123",
  "fitnessLevel": "intermediate",
  "goals": ["weight_loss", "strength"],
  "limitations": ["knee pain"],
  "preferences": {
    "workoutDays": ["monday", "wednesday", "friday"],
    "workoutDuration": 45,
    "equipment": ["dumbbells", "yoga mat"]
  },
  "currentStats": {
    "weight": 75,
    "height": 175,
    "age": 30
  }
}' | jq
