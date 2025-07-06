import { YouTubeSearchTool } from './agents/tools/youtubeTool';
import dotenv from 'dotenv';

dotenv.config();

async function testYouTubeTool() {
  try {
    console.log('Testing YouTube Search Tool...');
    
    // Initialize the YouTube tool
    const youtubeTool = new YouTubeSearchTool();
    
    // Test search query
    const query = 'beginner push up tutorial';
    console.log(`\nSearching for: "${query}"`);
    
    // Execute the search using the tool's call method with a simple string input
    const result = await youtubeTool.call(query);
    
    console.log('\nSearch Results:');
    console.log('==============');
    console.log(result);
    
  } catch (error) {
    console.error('Error testing YouTube tool:', error);
  }
}

// Run the test
testYouTubeTool();
