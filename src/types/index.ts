export enum AgentType {
  WORKOUT_PLANNER = "workout_planner",
  NUTRITION_ADVISOR = "nutrition_advisor",
  PROGRESS_ANALYZER = "progress_analyzer",
  MOTIVATIONAL_COACH = "motivational_coach"
}

export interface UserProfile {
  userId: string;
  fitnessLevel: string;
  goals: string[];
  limitations: string[];
  preferences: Record<string, any>;
  currentStats: Record<string, any>;
}

export interface AgentState {
  messages: any[]; // Will be replaced with proper message types
  userProfile: UserProfile;
  context: Record<string, any>;
  response?: Record<string, any>;
  agentType?: AgentType;
}

export interface WorkoutPlan {
  exercises: Array<{
    name: string;
    sets: number;
    reps: number | string;
    notes?: string;
    [key: string]: any;
  }>;
  duration: number;
  intensity: string;
  restPeriods: number[];
  progressionNotes: string;
  status: 'success' | 'error';
  error?: string;
}

export interface FitnessAgentConfig {
  modelName: string;
  apiKey: string;
  apiVersion: string;
  azureEndpoint: string;
  temperature: number;
  maxTokens: number;
  timeout: number;
  maxIterations: number;
}

export interface AgentTool {
  name: string;
  description: string;
  func: (...args: any[]) => Promise<any>;
}
