import { AgentExecutor, createOpenAIToolsAgent } from 'langchain/agents';
import { ChatPromptTemplate, MessagesPlaceholder } from '@langchain/core/prompts';
import { fitnessTools } from './tools';
import LLMFactory from './llms';
import type { BaseChatModel } from '@langchain/core/language_models/chat_models';
import type { DynamicStructuredTool } from '@langchain/core/tools';

// Initialize the language model with explicit type
const model: BaseChatModel = LLMFactory.createLLM({ type: 'chatgpt' }) as BaseChatModel;

// Create a prompt template
const prompt = ChatPromptTemplate.fromMessages([
  ['system', 'You are a helpful fitness assistant.'],
  new MessagesPlaceholder('chat_history'),
  ['human', '{input}'],
  new MessagesPlaceholder('agent_scratchpad'),
]);

// Create the agent
export async function createWorkoutAgent() {
  // Create the agent with explicit types
  const agent = await createOpenAIToolsAgent({
    llm: model,
    tools: fitnessTools as unknown as DynamicStructuredTool[],
    prompt,
  });

  // Create an executor
  const executor = new AgentExecutor({
    agent,
    tools: fitnessTools as unknown as DynamicStructuredTool[],
    verbose: true,
  });

  return executor;
}

export async function runWorkflow(input: string): Promise<string> {
  try {
    const executor = await createWorkoutAgent();
    const result = await executor.invoke({
      input,
      chat_history: [
        {
          "role": "system",
          "content": "You are a certified fitness coach and nutrition expert. Based on the following user profile, generate a personalized and progressive fitness plan that evolves weekly. The plan should include daily workouts, rest days, and recommendations for intensity, types of exercises, and brief rationale behind the progression. Adjust the plan weekly based on fitness goals and performance metrics. Generate a personalized workout plan for today. Include warm-up and cool-down if necessary. Ensure the plan is progressive and considers the weekly goal split. Output in the JSON format as shown below:\n\n{\n  \"date\": \"2025-07-12\",\n  \"day\": \"Day 3 of Week 2\",\n  \"workout_type\": \"Strength Training\",\n  \"focus_area\": \"Upper Body\",\n  \"exercises\": [\n    {\n      \"name\": \"Shoulder Press\",\n      \"sets\": 3,\n      \"reps\": \"10-12\",\n      \"rest\": \"60s\",\n      \"equipment\": \"Dumbbells\"\n    },\n    {\n      \"name\": \"Bent-over Row\",\n      \"sets\": 3,\n      \"reps\": \"12-15\",\n      \"rest\": \"60s\",\n      \"equipment\": \"Dumbbells\"\n    }\n  ],\n  \"duration\": \"40 minutes\",\n  \"intensity\": \"Moderate\",\n  \"notes\": \"Focus on form, keep core engaged\"\n}"
      },
      {
          "role": "user",
          "content": "User Profile: Age: 40 Gender: Male Fitness Level: Intermediate Fitness Goals: weight loss, muscle gain, strength Preferred Workouts: gym Workout Frequency: 5 days/week Include: Weekly plan with daily breakdown Progressive overload strategy (if applicable) Rest and recovery days Optional: nutrition tips aligned with fitness goals Adjustments or checkpoints after each week"
      }
    ],
    });

    return result.output;
  } catch (error) {
    console.error('Error in workout agent:', error);
    throw error;
  }
}
