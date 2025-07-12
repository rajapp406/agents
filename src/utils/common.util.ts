export const parstLLMJSON = (jsonString: string) => {
    try {
        const responseText = jsonString;
        // Try parsing JSON safely
        let jsonStart = responseText.indexOf('[');
        let jsonEnd = responseText.lastIndexOf(']');
        if (jsonStart === -1 || jsonEnd === -1) {
             jsonStart = responseText.indexOf('{');
             jsonEnd = responseText.lastIndexOf('}'); 
        }
        if (jsonStart === -1 || jsonEnd === -1) {
            throw new Error('Failed to find JSON in LLM response');
        }
        const jsonStr = responseText.slice(jsonStart, jsonEnd + 1);
        const workout = JSON.parse(jsonStr);
        return workout;
      } catch (error) {
        console.error('Failed to parse LLM response as JSON:', error);
        return null;
      }
};
    