import { createWorkoutAgent } from './agents/workoutAgent';
import dotenv from 'dotenv';
import { parstLLMJSON } from './utils/common.util';

dotenv.config();

async function testYoutubeAgent() {
  try {
    console.log('Testing YouTube Search through Agent...');
    
    // Create the agent with all tools
    const agent = await createWorkoutAgent();
    
    // Test query that should trigger the YouTube tool
    const query = `Find me some videos about proper push up form. Response should be in json from like below
          <json>[
            {
              "title": "The Perfect Push Up!",
              "id": "ba8tr1NzwXU",
              "url": "https://www.youtube.com/watch?v=ba8tr1NzwXU",
              "description": "Learn how to do a perfect push-up in less than a minute, covering scapula position, hand distance, and muscle stabilization."
            },
            {
              "title": "How to do Perfect Push Ups",
              "id": "_YrJc-kTYA0",
              "url": "https://www.youtube.com/watch?v=_YrJc-kTYA0",
              "description": "This video provides step-by-step instructions for achieving proper push-up technique."
            }
          ]
          </json>
    `;
    console.log(`\nQuery: "${query}"`);
    
    // Execute the agent
    const result = await agent.invoke({
      input: query,
      chat_history: []
    });
    
    console.log('\nAgent Response:');
    console.log('==============');
  //  console.log(parstLLMJSON(result.output) );
    
  } catch (error) {
    console.error('Error testing YouTube agent:', error);
  }
}

// Run the test
testYoutubeAgent();
