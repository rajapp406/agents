import { ChatGPT } from "./chatgpt";
import { ChatGPTConfig, type ChatModelType } from "./BaseModel";

export type LLMType = 'chatgpt' | 'anthropic' | 'openai';

export interface LLMConfig {
  type: LLMType;
  config?: ChatGPTConfig; // Extend this with other model configs as needed
}

/**
 * Factory class for creating language model instances
 */
class LLMFactory {
  /**
   * Create a language model instance based on the provided configuration
   * @param config Configuration for the language model
   * @returns An instance of the specified language model
   */
  public static createLLM(config: LLMConfig): ChatModelType {
    switch (config.type) {
      case 'chatgpt':
        return ChatGPT.getInstance(config.config).getModel();
      // Add cases for other model types as needed
      // case 'anthropic':
      //   return new AnthropicModel(config.config).getModel();
      // case 'openai':
      //   return new OpenAIModel(config.config).getModel();
      default:
        throw new Error(`Unsupported model type: ${config.type}`);
    }
  }

  /**
   * Get the default configuration for a specific model type
   * @param type The type of language model
   * @returns Default configuration for the specified model type
   */
  public static getDefaultConfig(type: LLMType): LLMConfig {
    switch (type) {
      case 'chatgpt':
        return {
          type: 'chatgpt',
          config: {
            model: 'gpt-4o',
            temperature: 0.7
          }
        };
      // Add default configs for other model types
      default:
        return { type };
    }
  }
}

export default LLMFactory;