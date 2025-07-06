import { AzureChatOpenAI } from "@langchain/openai";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { JsonOutputParser } from "@langchain/core/output_parsers";
import { AgentType, UserProfile, AgentState, FitnessAgentConfig, WorkoutPlan } from "../types";
import { runWorkflow } from "../agents/workoutAgent";
import { AzureOpenAI } from "openai";

declare global {
  namespace NodeJS {
    interface ProcessEnv {
      AZURE_OPENAI_MODEL?: string;
      AZURE_OPENAI_API_KEY?: string;
      AZURE_OPENAI_API_VERSION?: string;
      AZURE_OPENAI_ENDPOINT?: string;
    }
  }
}

export class FitnessAgentSystem {
  private config: FitnessAgentConfig;
  private llm: AzureChatOpenAI;

  constructor(config?: Partial<FitnessAgentConfig>) {
    this.config = {
      modelName: process.env.AZURE_OPENAI_MODEL || 'gpt-4',
      apiKey: process.env.AZURE_OPENAI_API_KEY || '',
      apiVersion: process.env.AZURE_OPENAI_API_VERSION || '2023-12-01-preview',
      azureEndpoint: process.env.AZURE_OPENAI_ENDPOINT || '',
      temperature: 0.7,
      maxTokens: 1000,
      timeout: 30000, // 30 seconds
      maxIterations: 5,
      ...config
    };

    if (!this.config.apiKey || !this.config.azureEndpoint) {
      throw new Error('Azure OpenAI API key and endpoint are required');
    }

    try {
      // Ensure the endpoint is properly formatted
      let baseUrl = this.config.azureEndpoint;
      
      // Remove any trailing slashes
      baseUrl = baseUrl.replace(/\/+$/, '');
      
      // If the endpoint doesn't end with /openai, add it
      if (!baseUrl.endsWith('/openai')) {
        baseUrl = `${baseUrl}/openai`;
      }

      console.log('Initializing Azure OpenAI with endpoint:', baseUrl);
      
      this.llm = new AzureChatOpenAI({
        model: "gpt-4o",
      azureOpenAIApiKey: process.env.AZURE_OPENAI_API_KEY,
      azureOpenAIApiVersion: process.env.AZURE_OPENAI_API_VERSION || '2023-12-01-preview',
      azureOpenAIBasePath: process.env.AZURE_OPENAI_ENDPOINT,
      azureOpenAIApiDeploymentName: "openai/deployments/gpt-4o-2024-11-20",
      temperature: 0.7,
      maxTokens: 1000
    });
      
      console.log('Azure OpenAI client initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Azure OpenAI client:', error);
      throw new Error(`Failed to initialize Azure OpenAI client: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async getAgentPrompt(agentType: AgentType): Promise<string> {
    // Define prompts for different agent types
    const prompts: Record<AgentType, string> = {
      [AgentType.WORKOUT_PLANNER]: `You are an expert fitness trainer with over 10 years of experience. 
      Create personalized workout plans based on the user's profile, goals, and limitations. 
      The plan should be safe, effective, and tailored to the user's fitness level.
      
      For each exercise, provide:
      - Name of the exercise
      - Number of sets and reps (or duration for cardio)
      - Rest period between sets
      - Any specific notes or modifications
      
      The plan should include a warm-up and cool-down section.`,
      
      [AgentType.NUTRITION_ADVISOR]: `You are a certified nutritionist. Provide dietary advice based on the user's fitness goals, 
      current stats, and any dietary restrictions. Focus on balanced nutrition and sustainable habits.`,
      
      [AgentType.PROGRESS_ANALYZER]: `You analyze fitness progress and provide data-driven insights and recommendations. 
      Help users understand their progress and suggest adjustments to their routine.`,
      
      [AgentType.MOTIVATIONAL_COACH]: `You are an experienced life coach specializing in fitness motivation. 
      Provide personalized encouragement, tips for staying consistent, and help users overcome challenges.`
    };

    return prompts[agentType] || 'You are a helpful assistant.';
  }

  private getAgentTools(agentType: AgentType): any[] {
    // Define tools available to different agent types
    const tools: Record<AgentType, any[]> = {
      [AgentType.WORKOUT_PLANNER]: [],
      [AgentType.NUTRITION_ADVISOR]: [],
      [AgentType.PROGRESS_ANALYZER]: [],
      [AgentType.MOTIVATIONAL_COACH]: []
    };

    return tools[agentType] || [];
  }

  public async processRequest(
    agentType: AgentType,
    userProfile: UserProfile,
    context: Record<string, any> = {}
  ): Promise<WorkoutPlan | any> {
    try {
      const systemPrompt = await this.getAgentPrompt(agentType);
      
      // Create a simple prompt template
      const userLimitations = userProfile.limitations?.length 
        ? userProfile.limitations.join(', ')
        : 'None';
        
      const prompt = [
        systemPrompt,
        '',
        '### User Profile ###',
        `- Fitness Level: ${userProfile.fitnessLevel}`,
        `- Goals: ${userProfile.goals.join(', ')}`,
        `- Limitations: ${userLimitations}`,
        `- Preferences: ${JSON.stringify(userProfile.preferences, null, 2)}`,
        `- Current Stats: ${JSON.stringify(userProfile.currentStats, null, 2)}`,
        '',
        '### Context ###',
        JSON.stringify(context, null, 2),
        '',
        '### Task ###',
        'Please generate a personalized workout plan in the following JSON format:',
        JSON.stringify({
          name: 'string',
          description: 'string',
          durationWeeks: 'number',
          daysPerWeek: 'number',
          workouts: [{
            day: 'string',
            name: 'string',
            description: 'string',
            exercises: [{
              name: 'string',
              sets: 'number',
              reps: 'string',
              rest: 'string',
              notes: 'string'
            }]
          }]
        }, null, 2)
      ].join('\n');

      // Get the response from the language model
      const response = await this.llm.invoke(prompt);
      
      // Parse the response
      let parsedResponse: any;
      try {
        // The response might already be an object or a string
        if (typeof response === 'string') {
          parsedResponse = JSON.parse(response);
        } else if (response && typeof response === 'object') {
          parsedResponse = response;
        } else {
          throw new Error('Invalid response format');
        }
        
        // If we have a plan in the response, use that
        if (parsedResponse.plan) {
          parsedResponse = parsedResponse.plan;
        }
      } catch (parseError) {
        console.error('Error parsing agent response:', parseError);
        console.error('Raw response content:', response);
        throw new Error('Failed to parse the response from the agent');
      }

      // Ensure the response has the correct structure
      return {
        exercises: Array.isArray(parsedResponse.exercises) 
          ? parsedResponse.exercises.map((ex: any) => ({
              name: ex.name || 'Unnamed Exercise',
              sets: ex.sets || 3,
              reps: ex.reps || 10,
              duration: ex.duration,
              notes: ex.notes || ''
            }))
          : [],
        duration: parsedResponse.duration || 30,
        intensity: parsedResponse.intensity || 'moderate',
        restPeriods: Array.isArray(parsedResponse.restPeriods) 
          ? parsedResponse.restPeriods 
          : [30, 60],
        progressionNotes: parsedResponse.progressionNotes || '',
        status: 'success' as const
      };
      
    } catch (error) {
      console.error('Error processing request:', error);
      return {
        status: 'error',
        error: 'Failed to process request',
        details: error instanceof Error ? error.message : String(error),
        exercises: [],
        duration: 0,
        intensity: 'low',
        restPeriods: [],
        progressionNotes: ''
      };
    }
  }

  // Generate a workout plan using the agent
  public async generateWorkoutPlan(
    userProfile: UserProfile,
    context: Record<string, any> = {}
  ): Promise<WorkoutPlan> {
    try {
      const response = await this.processRequest(AgentType.WORKOUT_PLANNER, userProfile, context);
      return response as WorkoutPlan;
    } catch (error) {
      console.error('Error generating workout plan:', error);
      throw new Error('Failed to generate workout plan');
    }
  }
}
