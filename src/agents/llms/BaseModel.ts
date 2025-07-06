import { AzureChatOpenAI, AzureOpenAIInput } from "@langchain/openai";

export interface ChatGPTConfig extends Omit<AzureOpenAIInput, 'modelName'> {
    model: string;
    temperature?: number;
    maxTokens?: number;
  }
  
export type ChatModelType = InstanceType<typeof AzureChatOpenAI>;