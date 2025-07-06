import { GetExerciseDetailsTool } from "./workoutdetailstool";
import { GetWorkoutPlanTool } from "./workoutTools";
import { YouTubeSearchTool } from "./youtubeTool";

// Create tool instances
export const fitnessTools = [
    new GetWorkoutPlanTool(),
    new GetExerciseDetailsTool(),
    new YouTubeSearchTool()
];

// Export individual tools for direct imports
export {
    GetWorkoutPlanTool,
    GetExerciseDetailsTool,
    YouTubeSearchTool
};