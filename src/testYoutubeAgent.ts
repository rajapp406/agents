import { createWorkoutAgent } from './agents/workoutAgent';
import dotenv from 'dotenv';

dotenv.config();

async function testYoutubeAgent() {
  try {
    console.log('Testing YouTube Search through Agent...');
    
    // Create the agent with all tools
    const agent = await createWorkoutAgent();
    
    // Test query that should trigger the YouTube tool
    const query = 'Find me some videos about proper push up form';
    console.log(`\nQuery: "${query}"`);
    
    // Execute the agent
    const result = await agent.invoke({
      input: query,
      chat_history: []
    });
    
    console.log('\nAgent Response:');
    console.log('==============');
    console.log(result.output);
    
  } catch (error) {
    console.error('Error testing YouTube agent:', error);
  }
}

// Run the test
testYoutubeAgent();
