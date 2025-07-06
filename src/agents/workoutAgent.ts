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
      chat_history: [],
    });

    return result.output;
  } catch (error) {
    console.error('Error in workout agent:', error);
    throw error;
  }
}
