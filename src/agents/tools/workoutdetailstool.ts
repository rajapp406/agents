import { BaseFitnessTool } from "./base";
import { z } from 'zod';
// Exercise Details Tool
const exerciseDetailsSchema = z.object({
  exerciseName: z.string(),
  includeVariations: z.boolean().optional().default(false)
});

type ExerciseDetailsInput = z.infer<typeof exerciseDetailsSchema>;


export class GetExerciseDetailsTool extends BaseFitnessTool<typeof exerciseDetailsSchema> {
    protected _inputSchema = exerciseDetailsSchema;
    
    get inputSchema() {
      return this._inputSchema;
    }
  
    constructor() {
      super({
        name: 'get_exercise_details',
        description: 'Get detailed information about a specific exercise',
        returnDirect: false
      });
    }
  
    protected async _call(input: ExerciseDetailsInput): Promise<string> {
      // In a real implementation, this would fetch from a database or API
      return JSON.stringify({
        name: input.exerciseName,
        description: `Detailed information about ${input.exerciseName}`,
        muscleGroups: [],
        equipment: [],
        instructions: [],
        variations: input.includeVariations ? [] : undefined
      });
    }
  }