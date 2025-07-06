import { Tool, type ToolParams } from '@langchain/core/tools';
import { z } from 'zod';
import { CallbackManagerForToolRun } from '@langchain/core/callbacks/manager';

// Helper type to extract input type from a Zod schema
type InferSchemaType<T extends z.ZodType> = T extends z.ZodType<infer U> ? U : never;

export interface BaseFitnessToolParams extends ToolParams {
  name: string;
  description: string;
  returnDirect?: boolean;
}

// Base schema that LangChain's Tool expects
export const baseSchema = z.object({
  input: z.string().optional()
});

export type BaseFitnessToolInput = z.infer<typeof baseSchema>;

export abstract class BaseFitnessTool<T extends z.ZodType = typeof baseSchema> extends Tool {
  // Store the actual schema for the tool's input
  protected abstract _inputSchema: T;
  
  // Required by Tool interface
  name: string;
  description: string;
  returnDirect: boolean;

  // Getter for the input schema
  get inputSchema(): T {
    return this._inputSchema;
  }
  
  // The actual implementation that subclasses must provide
  protected abstract _call(
    input: InferSchemaType<T>,
    runManager?: CallbackManagerForToolRun
  ): Promise<string>;

  constructor(params: BaseFitnessToolParams) {
    super(params);
    this.name = params.name;
    this.description = params.description;
    this.returnDirect = params.returnDirect || false;
  }
  
  // This is the method that implements the Tool interface
  async call(
    arg: string | object | undefined,
    configArg?: any,
    _?: any
  ): Promise<string> {
    try {
      // Parse the input
      let parsedInput: any = typeof arg === 'string' ? JSON.parse(arg) : arg || {};
      
      // Ensure the input matches the expected schema
      if (this.inputSchema) {
        const validated = this.inputSchema.safeParse(parsedInput);
        if (!validated.success) {
          throw new Error(`Invalid arguments: ${validated.error.message}`);
        }
        parsedInput = validated.data;
      }
      
      // Call the implementation with the parsed input
      return this._call(parsedInput, configArg?.runManager);
    } catch (error) {
      console.error(`Error in ${this.name}:`, error);
      return `Error: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
}
