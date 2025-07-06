import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from openai import AzureOpenAI
from pydantic import BaseModel, Field
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    WORKOUT_PLANNER = "workout_planner"
    FORM_CHECKER = "form_checker"
    NUTRITION_ADVISOR = "nutrition_advisor"
    PROGRESS_ANALYZER = "progress_analyzer"
    MOTIVATIONAL_COACH = "motivational_coach"

@dataclass
class UserProfile:
    user_id: str
    fitness_level: str
    goals: List[str]
    limitations: List[str]
    preferences: Dict[str, Any]
    current_stats: Dict[str, Any]

class WorkoutPlan(BaseModel):
    exercises: List[Dict[str, Any]]
    duration: int
    intensity: str
    rest_periods: List[int]
    progression_notes: str

class FormFeedback(BaseModel):
    exercise: str
    score: float = Field(ge=0, le=10)
    corrections: List[str]
    praise: List[str]

class NutritionAdvice(BaseModel):
    meal_suggestions: List[str]
    calorie_target: int
    macro_breakdown: Dict[str, int]
    hydration_reminder: str

class ProgressAnalysis(BaseModel):
    improvements: List[str]
    areas_to_focus: List[str]
    next_milestone: str
    motivation_level: str

class MotivationalMessage(BaseModel):
    message: str
    tone: str
    call_to_action: str

class LLMAgentHandler:

    def __init__(self):
        self.client = AzureOpenAI(
            api_key="f166d10f343c4c9987b8724c2763e7ff",
            azure_endpoint="https://ai-proxy.lab.epam.com",
            api_version="2023-12-01-preview",
        )
        self.model = "gpt-4o"  # Store model name as a class variable
        self.agents = {
            AgentType.WORKOUT_PLANNER: self._create_workout_planner_agent(),
            AgentType.FORM_CHECKER: self._create_form_checker_agent(),
            AgentType.NUTRITION_ADVISOR: self._create_nutrition_advisor_agent(),
            AgentType.PROGRESS_ANALYZER: self._create_progress_analyzer_agent(),
            AgentType.MOTIVATIONAL_COACH: self._create_motivational_coach_agent()
        }
    def _create_workout_planner_agent(self):
        return {
            "system_prompt": """You are an expert fitness trainer specializing in creating personalized workout plans. 
            You create progressive, safe, and effective workouts based on user profiles. 
            Always respond in valid JSON format matching the WorkoutPlan schema.""",
            "output_parser": self._parse_workout_plan,
            "validation_schema": WorkoutPlan
        }
    
    def _create_form_checker_agent(self):
        return {
            "system_prompt": """You are a form analysis expert who provides constructive feedback on exercise form.
            Focus on safety, effectiveness, and encouragement. 
            Always respond in valid JSON format matching the FormFeedback schema.""",
            "output_parser": self._parse_form_feedback,
            "validation_schema": FormFeedback
        }
    
    def _create_nutrition_advisor_agent(self):
        return {
            "system_prompt": """You are a certified nutritionist providing personalized meal guidance.
            Focus on balanced, sustainable nutrition that supports fitness goals.
            Always respond in valid JSON format matching the NutritionAdvice schema.""",
            "output_parser": self._parse_nutrition_advice,
            "validation_schema": NutritionAdvice
        }
    
    def _create_progress_analyzer_agent(self):
        return {
            "system_prompt": """You are a fitness progress analyst who reviews user data and provides insights.
            Focus on celebrating achievements and identifying areas for improvement.
            Always respond in valid JSON format matching the ProgressAnalysis schema.""",
            "output_parser": self._parse_progress_analysis,
            "validation_schema": ProgressAnalysis
        }
    
    def _create_motivational_coach_agent(self):
        return {
            "system_prompt": """You are an encouraging fitness coach who provides motivation and support.
            Adapt your tone to the user's current state and provide actionable encouragement.
            Always respond in valid JSON format matching the MotivationalMessage schema.""",
            "output_parser": self._parse_motivational_message,
            "validation_schema": MotivationalMessage
        }

    async def process_agent_request(
        self, 
        agent_type: AgentType, 
        user_profile: UserProfile,
        context: Dict[str, Any],
        max_retries: int = 3,
        timeout: int = 60
    ) -> Optional[Union[WorkoutPlan, FormFeedback, NutritionAdvice, ProgressAnalysis, MotivationalMessage]]:
        """
        Process a request through a specific agent with retry logic and validation
        """
        agent = self.agents[agent_type]
        
        for attempt in range(max_retries):
            try:
                # Construct the prompt
                prompt = self._build_prompt(agent_type, user_profile, context)
                
                # Make LLM request with timeout
                response = await self._make_llm_request(
                    system_prompt=agent["system_prompt"],
                    user_prompt=prompt,
                    timeout=timeout
                )
                
                # Parse and validate output
                parsed_output = agent["output_parser"](response)
                validated_output = agent["validation_schema"](**parsed_output)
                
                logger.info(f"Successfully processed {agent_type.value} request")
                return validated_output
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {agent_type.value}: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts failed for {agent_type.value}")
                    return None
                await asyncio.sleep(1)  # Brief delay before retry
        
        return None

    async def _make_llm_request(self, system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
        """Make request to OpenAI API with error handling and timeout"""
        try:
            logger.info(f"Making LLM request with model: {self.model}")
            logger.info(f"System prompt: {system_prompt[:200]}...")
            logger.info(f"User prompt: {user_prompt[:200]}...")
            
            # Create a sync function to make the API call
            def make_api_call():
                try:
                    logger.info("Starting API call...")
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1500,
                        response_format={"type": "json_object"}
                    )
                    logger.info("API call completed successfully")
                    return response
                except Exception as e:
                    logger.error(f"Error in API call: {str(e)}", exc_info=True)
                    raise
            
            try:
                # Make the API call in a separate thread with timeout
                logger.info(f"Setting timeout of {timeout} seconds for API call")
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, make_api_call),
                    timeout=timeout
                )
                
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("Empty response from LLM")
                    
                content = response.choices[0].message.content
                logger.info(f"Received response (first 200 chars): {content[:200]}...")
                return content
                
            except asyncio.TimeoutError:
                logger.error(f"API call timed out after {timeout} seconds")
                raise TimeoutError(f"API call timed out after {timeout} seconds")
                
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}", exc_info=True)
            raise

    def _build_prompt(self, agent_type: AgentType, user_profile: UserProfile, context: Dict[str, Any]) -> str:
        """Build agent-specific prompts"""
        base_user_info = f"""
        You are a helpful fitness assistant. Please generate a response in valid JSON format.
        
        User Profile:
        - ID: {user_profile.user_id}
        - Fitness Level: {user_profile.fitness_level}
        - Goals: {', '.join(user_profile.goals)}
        - Limitations: {', '.join(user_profile.limitations)}
        - Preferences: {json.dumps(user_profile.preferences, indent=2)}
        - Current Stats: {json.dumps(user_profile.current_stats, indent=2)}
        
        Context: {json.dumps(context, indent=2)}
        
        Please provide your response in valid JSON format that matches the expected schema.
        """
        
        if agent_type == AgentType.WORKOUT_PLANNER:
            return f"""
            {base_user_info}
            
            Context: {json.dumps(context)}
            
            Create a personalized workout plan for today. Consider the user's available time, 
            equipment, and current fitness level. Make it progressive and engaging.
            """
        
        elif agent_type == AgentType.FORM_CHECKER:
            return f"""
            {base_user_info}
            
            Exercise Analysis Data: {json.dumps(context)}
            
            Analyze the user's form for the given exercise. Provide specific, actionable feedback
            while being encouraging and supportive.
            """
        
        elif agent_type == AgentType.NUTRITION_ADVISOR:
            return f"""
            {base_user_info}
            
            Current Dietary Context: {json.dumps(context)}
            
            Provide personalized nutrition advice that supports their fitness goals.
            Consider their preferences and any dietary restrictions.
            """
        
        elif agent_type == AgentType.PROGRESS_ANALYZER:
            return f"""
            {base_user_info}
            
            Progress Data: {json.dumps(context)}
            
            Analyze the user's fitness progress and provide insights. Focus on achievements
            and areas for improvement.
            """
        
        elif agent_type == AgentType.MOTIVATIONAL_COACH:
            return f"""
            {base_user_info}
            
            Current Situation: {json.dumps(context)}
            
            Provide motivational support tailored to the user's current state and goals.
            Be encouraging and provide actionable motivation.
            """

    def _parse_workout_plan(self, response: str) -> dict:
        """Parse and validate workout plan response"""
        try:
            data = json.loads(response)
            logger.debug(f"Raw response data: {json.dumps(data, indent=2)}")
            
            # Initialize default values
            exercises = []
            duration = 30
            intensity = 'moderate'
            rest_periods = [30, 60]
            progression_notes = ''
            
            # Extract data from WorkoutPlan wrapper if it exists
            workout_data = data.get('WorkoutPlan', data)
            
            # Extract exercises from different possible locations/structures
            if 'structure' in workout_data and isinstance(workout_data['structure'], list):
                # Handle structure array format
                for item in workout_data['structure']:
                    if isinstance(item, dict):
                        exercise = {
                            'name': item.get('exercise', 'Unknown Exercise'),
                            'sets': item.get('sets', 3),
                            'reps': item.get('reps', '8-12'),
                            'notes': item.get('notes', '')
                        }
                        exercises.append(exercise)
            elif 'exercises' in workout_data and isinstance(workout_data['exercises'], list):
                # Handle direct exercises array
                for ex in workout_data['exercises']:
                    if isinstance(ex, str):
                        exercises.append({'name': ex})
                    elif isinstance(ex, dict):
                        exercises.append({
                            'name': ex.get('name', 'Unknown Exercise'),
                            'sets': ex.get('sets', 3),
                            'reps': ex.get('reps', '8-12'),
                            'notes': ex.get('notes', '')
                        })
            
            # Extract other fields with fallbacks
            duration = workout_data.get('duration_minutes', 
                                     workout_data.get('duration', 30))
            
            intensity = str(workout_data.get('intensity', 'moderate')).lower()
            
            if 'rest_periods' in workout_data:
                rest_periods = workout_data['rest_periods']
            
            if 'progression_notes' in workout_data:
                progression_notes = workout_data['progression_notes']
            elif 'notes' in workout_data:
                progression_notes = workout_data['notes']
            
            # If no exercises were found, add some default ones based on the context
            if not exercises and 'workout_type' in workout_data:
                workout_type = workout_data['workout_type'].lower()
                if 'strength' in workout_type:
                    exercises = [
                        {'name': 'Bodyweight Squats', 'sets': 3, 'reps': '10-12'},
                        {'name': 'Push-ups', 'sets': 3, 'reps': '8-10'},
                        {'name': 'Bent-over Rows', 'sets': 3, 'reps': '10-12'}
                    ]
                else:
                    exercises = [
                        {'name': 'Brisk Walking', 'duration': '30 minutes'},
                        {'name': 'Bodyweight Exercises', 'sets': 3, 'reps': '10-12'}
                    ]
            
            return {
                'exercises': exercises,
                'duration': int(duration),
                'intensity': intensity,
                'rest_periods': rest_periods,
                'progression_notes': progression_notes
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse workout plan: {e}")
            logger.error(f"Response content: {response[:500]}...")
            raise

    def _parse_form_feedback(self, response: str) -> dict:
        """Parse and validate form feedback response"""
        try:
            data = json.loads(response)
            return {
                'exercise': data.get('exercise', ''),
                'score': data.get('score', 5.0),
                'corrections': data.get('corrections', []),
                'praise': data.get('praise', [])
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse form feedback: {e}")
            raise

    def _parse_nutrition_advice(self, response: str) -> dict:
        """Parse and validate nutrition advice response"""
        try:
            data = json.loads(response)
            return {
                'meal_suggestions': data.get('meal_suggestions', []),
                'calorie_target': data.get('calorie_target', 2000),
                'macro_breakdown': data.get('macro_breakdown', {
                    'protein': 30,
                    'carbs': 40,
                    'fats': 30
                }),
                'hydration_reminder': data.get('hydration_reminder', "Remember to drink water!")
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse nutrition advice: {e}")
            raise

    def _parse_progress_analysis(self, response: str) -> dict:
        """Parse and validate progress analysis response"""
        try:
            data = json.loads(response)
            return {
                'improvements': data.get('improvements', []),
                'areas_to_focus': data.get('areas_to_focus', []),
                'next_milestone': data.get('next_milestone', ''),
                'motivation_level': data.get('motivation_level', 'good')
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse progress analysis: {e}")
            raise

    def _parse_motivational_message(self, response: str) -> dict:
        """Parse and validate motivational message response"""
        try:
            data = json.loads(response)
            return {
                'message': data.get('message', 'Keep up the great work!'),
                'tone': data.get('tone', 'encouraging'),
                'call_to_action': data.get('call_to_action', 'You got this!')
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse motivational message: {e}")
            raise

    async def batch_process_agents(
        self, 
        requests: List[Dict[str, Any]], 
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """Process multiple agent requests concurrently"""
        tasks = []
        
        for request in requests:
            task = self.process_agent_request(
                agent_type=AgentType(request['agent_type']),
                user_profile=user_profile,
                context=request['context']
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results by agent type
        processed_results = {}
        for i, result in enumerate(results):
            agent_type = requests[i]['agent_type']
            if isinstance(result, Exception):
                processed_results[agent_type] = {"error": str(result)}
            else:
                processed_results[agent_type] = result
        
        return processed_results

# Example usage
async def main():
    try:
        logger.info("Starting LLM Agent Handler...")
        
        # Initialize the handler
        logger.info("Initializing LLMAgentHandler...")
        handler = LLMAgentHandler()
        
        # Example user profile
        logger.info("Creating example user profile...")
        user_profile = UserProfile(
            user_id="123",
            fitness_level="intermediate",
            goals=["lose weight", "build muscle"],
            limitations=["bad knee"],
            preferences={"workout_type": "strength training"},
            current_stats={"weight_kg": 75, "height_cm": 175}
        )
        
        # Single agent request
        logger.info("Sending single agent request...")
        try:
            workout_plan = await handler.process_agent_request(
                agent_type=AgentType.WORKOUT_PLANNER,
                user_profile=user_profile,
                context={"available_time": 30, "equipment": "Gym"}
            )
            logger.info("Successfully received workout plan")
            print("\n=== Workout Plan ===")
            print(json.dumps(workout_plan.dict(), indent=2))
            
        except Exception as e:
            logger.error(f"Error in single agent request: {str(e)}", exc_info=True)
        
        # Uncomment the following section to enable batch processing
        '''
        # Batch processing
        logger.info("\nSending batch requests...")
        try:
            batch_requests = [
                {
                    "agent_type": "workout_planner",
                    "context": {"available_time": 30, "equipment": "none"}
                },
                {
                    "agent_type": "motivational_coach",
                    "context": {"mood": "tired", "last_workout": "yesterday"}
                }
            ]
            
            batch_results = await handler.batch_process_agents(
                requests=batch_requests,
                user_profile=user_profile
            )
            
            logger.info("Successfully processed batch requests")
            print("\n=== Batch Results ===")
            for agent_type, result in batch_results.items():
                print(f"\n{agent_type.upper()}:")
                if isinstance(result, dict) and 'error' in result:
                    print(f"Error: {result['error']}")
                else:
                    print(json.dumps(result.dict() if hasattr(result, 'dict') else result, indent=2))
                    
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}", exc_info=True)
        '''
            
    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())