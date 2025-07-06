import { AzureChatOpenAI } from "@langchain/openai";
import { ChatGPTConfig, ChatModelType } from "./BaseModel";
import dotenv from 'dotenv';

dotenv.config();

const DEFAULT_CONFIG: Omit<ChatGPTConfig, 'azureOpenAIApiKey' | 'azureOpenAIBasePath' | 'azureOpenAIApiDeploymentName'> = {
  model: "gpt-4o",
  azureOpenAIApiVersion: '2023-12-01-preview',
  temperature: 0.7,
  maxTokens: 1000
} as const;

export class ChatGPT {
  private static instance: ChatGPT | null = null;
  public readonly model: AzureChatOpenAI;

  private constructor(config?: Partial<ChatGPTConfig>) {
    const apiKey = process.env.AZURE_OPENAI_API_KEY;
    const endpoint = process.env.AZURE_OPENAI_ENDPOINT;
    const deploymentName = process.env.AZURE_OPENAI_DEPLOYMENT_NAME || "openai/deployments/gpt-4o-2024-11-20";

    if (!apiKey) {
      throw new Error('AZURE_OPENAI_API_KEY environment variable is required');
    }
    if (!endpoint) {
      throw new Error('AZURE_OPENAI_ENDPOINT environment variable is required');
    }

    const mergedConfig: ChatGPTConfig = {
      ...DEFAULT_CONFIG,
      ...config,
      azureOpenAIApiKey: apiKey,
      azureOpenAIBasePath: endpoint,
      azureOpenAIApiDeploymentName: deploymentName,
    };

    this.model = new AzureChatOpenAI({
      ...mergedConfig,
      modelName: mergedConfig.model,
    });
  }

  /**
   * Get the singleton instance of ChatGPT
   * @param config Optional configuration to use when creating the instance
   */
  public static getInstance(config?: Partial<ChatGPTConfig>): ChatGPT {
    if (!ChatGPT.instance) {
      ChatGPT.instance = new ChatGPT(config);
    }
    return ChatGPT.instance;
  }

  /**
   * Reset the singleton instance (useful for testing)
   */
  public static resetInstance(): void {
    ChatGPT.instance = null;
  }

  /**
   * Get the underlying chat model
   */
  public getModel(): ChatModelType {
    return this.model;
  }

  // Implement any required methods from the LLM interface here
  // For example:
  // public async generate(prompt: string): Promise<string> {
  //   const response = await this.model.invoke(prompt);
  //   return response.content.toString();
  // }
}

// Default export for convenience
export default ChatGPT.getInstance();
