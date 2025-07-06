async function getExercises(apiKey) {
    const response = await fetch('https://wger.de/api/v2/exercise/?limit=0', {
      headers: {
        'Authorization': `Token ${apiKey}`
      }
    });
    const data = await response.json();
    console.log(data.results.filter((item, index) => index < 10));
  }
async function createExercise(apiKey) {
  const headers = {
    'Authorization': `Token ${apiKey}`,
}

const data = {
    "name": "Crunch",
    "category": 10,
    "muscles": [6],
    "muscles_secondary": [4],
    "equipment": [7],
    "description": "The crunch is a popular core exercise...",
    "license_author": "raj"
}

const response = await fetch("https://wger.de/api/v2/exercise/", {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data)
})
console.log(response.status, await response.json())

}
  // Replace 'your_api_key' with your actual API key
  //getExercises('eb7b95c919a65fa311b7219f48621becb441f460');
  getExercises('eb7b95c919a65fa311b7219f48621becb441f460').then(() => console.log('Exercise created successfully')).catch(error => console.error('Error creating exercise:', error));