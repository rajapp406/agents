import { createWorkoutAgent } from './agents/workoutAgent';

async function testAgent() {
  try {
    console.log('Starting fitness agent test...');
    
    // Test 1: Get a workout plan
    console.log('\n--- Testing Workout Plan ---');
    const workoutPlanInput = {
      fitnessLevel: 'intermediate',
      goals: ['weight loss', 'muscle tone'],
      preferences: {
        workoutDays: ['monday', 'wednesday', 'friday'],
        workoutDuration: 60,
        equipment: ['dumbbells', 'yoga mat']
      }
    };
    
    const workoutPlanResult = await testAgentWithInput(
      `Get me a workout plan with these details: ${JSON.stringify(workoutPlanInput)}`
    );
    console.log('Workout Plan Result:', workoutPlanResult);
    
    // Test 2: Get exercise details
    console.log('\n--- Testing Exercise Details ---');
    const exerciseDetailsResult = await testAgentWithInput(
      'Tell me about push-ups and show variations'
    );
    console.log('Exercise Details Result:', exerciseDetailsResult);
    
  } catch (error) {
    console.error('Error during agent test:', error);
  }
}

async function testAgentWithInput(input: string): Promise<string> {
  try {
    const executor = await createWorkoutAgent();
    const result = await executor.invoke({
      input,
      chat_history: []
    });
    return result.output;
  } catch (error) {
    return `Error: ${error instanceof Error ? error.message : String(error)}`;
  }
}

// Run the test
testAgent()
  .then(() => console.log('Test completed'))
  .catch(console.error);
