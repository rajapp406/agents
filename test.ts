import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { AzureChatOpenAI } from "@langchain/openai";
import * as dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

// Verify required environment variables
const requiredEnvVars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT'];
const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingVars.length > 0) {
  console.error(`Error: Missing required environment variables: ${missingVars.join(', ')}`);
  console.log('Please make sure your .env file contains these variables:');
  console.log('AZURE_OPENAI_API_KEY=your_api_key_here');
  console.log('AZURE_OPENAI_ENDPOINT=your_endpoint_here');
  console.log('AZURE_OPENAI_MODEL=your_model_name_here (optional, defaults to gpt-4o)');
  console.log('AZURE_OPENAI_API_VERSION=your_api_version_here (optional, defaults to 2023-12-01-preview)');
  process.exit(1);
}

console.log('Environment variables loaded successfully');

async function testAzureOpenAI() {
  try {
    console.log('Initializing Azure OpenAI client...');
    
    const llm = new AzureChatOpenAI({
        model: "gpt-4o",
      azureOpenAIApiKey: process.env.AZURE_OPENAI_API_KEY,
      azureOpenAIApiVersion: process.env.AZURE_OPENAI_API_VERSION || '2023-12-01-preview',
      azureOpenAIBasePath: process.env.AZURE_OPENAI_ENDPOINT,
      azureOpenAIApiDeploymentName: "openai/deployments/gpt-4o-2024-11-20",
      temperature: 0.7,
      maxTokens: 1000
    });
    console.log('Sending test message...');
    
    const messages = [
      new SystemMessage("You are a helpful assistant."),
      new HumanMessage("Hello, how are you?")
    ];

    const response = await llm.invoke(messages);
    console.log('Response received:');
    console.log(JSON.stringify(response, null, 2));
    
    return response;
  } catch (error) {
    console.error('Error in testAzureOpenAI:', error);
    throw error;
  }
}

// Run the test
testAzureOpenAI()
  .then(() => console.log('Test completed successfully'))
  .catch(err => console.error('Test failed:', err));