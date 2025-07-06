"""
LangChain and LangGraph-based Agent Handler for Fitness Application

This module implements a stateful, graph-based agent system using LangChain and LangGraph.
It follows SOLID principles and clean code practices for maintainability and extensibility.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, TypedDict, Annotated, Sequence, Literal
from enum import Enum, auto
from dataclasses import dataclass, asdict, field
import json
import dotenv
from pydantic import BaseModel, Field, field_serializer

dotenv.load_dotenv()

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    """Enumeration of available agent types."""
    WORKOUT_PLANNER = "workout_planner"
    NUTRITION_ADVISOR = "nutrition_advisor"
    PROGRESS_ANALYZER = "progress_analyzer"
    MOTIVATIONAL_COACH = "motivational_coach"
    
    def __str__(self):
        return self.value

@dataclass
class UserProfile:
    """Data class representing user profile information."""
    user_id: str
    fitness_level: str
    goals: List[str]
    limitations: List[str]
    preferences: Dict[str, Any]
    current_stats: Dict[str, Any]

class AgentState(TypedDict):
    """State definition for the agent workflow."""
    messages: Annotated[List[BaseMessage], lambda x, _: x]
    user_profile: UserProfile
    context: Dict[str, Any]
    response: Optional[Dict[str, Any]] = None
    agent_type: Optional[AgentType] = None

class WorkoutPlan(BaseModel):
    """Pydantic model for workout plan response."""
    exercises: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of exercises with details like name, sets, reps, and notes"
    )
    duration: int = Field(
        default=30,
        description="Duration of the workout in minutes"
    )
    intensity: str = Field(
        default="moderate",
        description="Intensity level of the workout"
    )
    rest_periods: List[int] = Field(
        default_factory=lambda: [30, 60],
        description="Rest periods between exercises in seconds"
    )
    progression_notes: str = Field(
        default="",
        description="Notes on how to progress the workout over time"
    )
    status: str = Field(
        default="success",
        description="Status of the response (success/error)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the request failed"
    )
    
    class Config:
        json_encoders = {
            # Add any custom JSON encoders if needed
        }
    
    @classmethod
    def create_error(cls, message: str) -> 'WorkoutPlan':
        """Create an error response."""
        return cls(
            exercises=[],
            duration=0,
            intensity="",
            status="error",
            error=message
        )

class FitnessAgentConfig:
    """Configuration for the fitness agent system."""
    
    def __init__(self, config_path: str = None):
        """Initialize with optional config file path."""
        self.config = {
            "model_name": os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 60,
            "max_iterations": 5
        }
        
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                self.config.update(json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")

    def _create_agent(self, agent_type: AgentType) -> Any:
        """Create an agent of the specified type."""
        try:
            logger.info("Creating %s agent", agent_type.value)
            
            # Get environment variables with fallbacks
            model_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            
            if not all([endpoint, api_key]):
                raise ValueError("Missing required environment variables (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY)")
            
            logger.debug("Initializing AzureChatOpenAI with model: %s", model_name)
            
            # Create the LLM with error handling
            llm = AzureChatOpenAI(
                azure_deployment=model_name,
                openai_api_version=api_version,
                azure_endpoint=endpoint,
                api_key=api_key,
                temperature=0.7,
                max_tokens=1000,
                request_timeout=30,
                streaming=False
            )
            
            # Define the prompt based on agent type
            if agent_type == AgentType.WORKOUT_PLANNER:
                # Create a more structured prompt template
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are an expert fitness trainer. Generate a personalized workout plan 
based on the user's profile and context. 

Your response MUST be a valid JSON object with the following structure:
{{
  "exercises": [
    {{
      "name": "string",
      "sets": number,
      "reps": "string",
      "notes": "string"
    }}
  ],
  "duration": number,  // in minutes
  "intensity": "string",  // low, moderate, high
  "rest_periods": [number],  // rest times in seconds between exercises
  "progression_notes": "string"
}}

Example:
{{
  "exercises": [
    {{
      "name": "Push-ups",
      "sets": 3,
      "reps": "10-12",
      "notes": "Keep back straight and lower until elbows are at 90 degrees"
    }}
  ],
  "duration": 45,
  "intensity": "moderate",
  "rest_periods": [45, 60],
  "progression_notes": "Increase reps by 1-2 each week"
}}
"""),
                    ("human", """User profile and context:
{input}

Please generate a personalized workout plan based on the above information. Include 4-6 exercises with appropriate sets, reps, and notes.""")
                ])
                
                # Create a parser for the response
                output_parser = JsonOutputParser()
                
                # Create the agent chain
                chain = prompt | llm | output_parser
                
            else:
                # Default agent for other types
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant."),
                    ("human", "{input}")
                ])
                chain = prompt | llm
            
            logger.debug("Created %s agent successfully", agent_type.value)
            return chain
            
        except Exception as e:
            logger.error("Error creating %s agent: %s", agent_type.value, str(e), exc_info=True)
            raise RuntimeError(f"Failed to create {agent_type.value} agent: {str(e)}")

class FitnessAgentSystem:
    """Main class for the fitness agent system using LangGraph."""
    
    def __init__(self, config: FitnessAgentConfig = None):
        """Initialize the fitness agent system."""
        self.config = config or FitnessAgentConfig()
        self.llm = self._initialize_llm()
        self.workflow = self._build_workflow()
        
    def _initialize_llm(self):
        """Initialize the language model."""
        return AzureChatOpenAI(
            model=self.config.config["model_name"],
            api_key=self.config.config["api_key"],
            api_version=self.config.config["api_version"],
            azure_endpoint=self.config.config["azure_endpoint"],
            temperature=self.config.config["temperature"],
            max_tokens=self.config.config["max_tokens"],
            request_timeout=self.config.config["timeout"]
        )
    
    def _create_agent(self, agent_type: AgentType):
        """Create an agent of the specified type."""
        # Define the prompt template
        prompt = self._get_agent_prompt(agent_type)
        
        # Define the tools the agent can use
        tools = self._get_agent_tools(agent_type)
        
        # Create the agent
        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
            }
            | prompt
            | self.llm.bind(stop=["\nObservation"])
            | ReActSingleInputOutputParser()
        )
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            handle_parsing_errors=True,
            max_iterations=self.config.config["max_iterations"]
        )
    
    def _get_agent_prompt(self, agent_type: AgentType) -> ChatPromptTemplate:
        """Get the prompt template for the specified agent type."""
        system_message = {
            AgentType.WORKOUT_PLANNER: """You are an expert fitness trainer specializing in creating personalized workout plans. 
            Create progressive, safe, and effective workouts based on user profiles.
            Always respond with valid JSON matching the required schema.""",
            AgentType.NUTRITION_ADVISOR: """You are a certified nutritionist providing personalized meal guidance.
            Focus on balanced, sustainable nutrition that supports fitness goals.
            Always respond with valid JSON.""",
            AgentType.PROGRESS_ANALYZER: """You analyze fitness progress data and provide insights.
            Focus on trends, achievements, and areas for improvement.
            Always respond with valid JSON.""",
            AgentType.MOTIVATIONAL_COACH: """You are an encouraging fitness coach who provides motivation and support.
            Adapt your tone to the user's current state and provide actionable encouragement.
            Always respond with valid JSON."""
        }.get(agent_type, "You are a helpful assistant. Always respond with valid JSON.")
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def _get_agent_tools(self, agent_type: AgentType) -> list:
        """Get the tools available to the specified agent type."""
        base_tools = [
            self._create_tool("get_user_profile", "Get the user's profile information", self._get_user_profile),
            self._create_tool("get_workout_history", "Get the user's workout history", self._get_workout_history)
        ]
        
        if agent_type == AgentType.WORKOUT_PLANNER:
            base_tools.extend([
                self._create_tool("generate_workout_plan", "Generate a workout plan", self._generate_workout_plan)
            ])
        
        return base_tools
    
    def _create_tool(self, name: str, description: str, func: callable) -> Tool:
        """Create a LangChain tool."""
        return Tool(
            name=name,
            description=description,
            func=func
        )
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Define the workflow with proper state typing
        workflow = StateGraph(AgentState)
        
        # Define nodes with proper state handling
        workflow.add_node("start", self._start_node)
        workflow.add_node("generate_response", self._generate_response_node)
        
        # Define edges
        workflow.add_edge("start", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Set the entry point
        workflow.set_entry_point("start")
        
        # Compile the workflow
        logger.info("Compiling workflow...")
        compiled_workflow = workflow.compile()
        logger.info("Workflow compiled successfully")
        return compiled_workflow
    
    # Node implementations
    def _start_node(self, state: AgentState) -> AgentState:
        """Start node of the workflow."""
        try:
            logger.debug("Starting workflow with state keys: %s", list(state.keys()))
            
            # Ensure we have the required state
            user_profile = state.get("user_profile")
            if not isinstance(user_profile, UserProfile):
                raise ValueError("Invalid or missing user_profile in state")
                
            context = state.get("context", {})
            if not isinstance(context, dict):
                raise ValueError("Invalid context in state")
            
            agent_type = state.get("agent_type", AgentType.WORKOUT_PLANNER)
            
            # Create system message with clear instructions
            system_message = SystemMessage(
                content=(
                    "You are an expert fitness trainer. Generate a personalized workout plan "
                    "based on the user's profile and context. \n\n"
                    "Your response MUST be a valid JSON object with the following structure:\n"
                    "{\n"
                    "  \"exercises\": [\n"
                    "    {\n"
                    "      \"name\": \"string\",\n"
                    "      \"sets\": number,\n"
                    "      \"reps\": \"string\",\n"
                    "      \"notes\": \"string\"\n"
                    "    }\n"
                    "  ],\n"
                    "  \"duration\": number,\n"
                    "  \"intensity\": \"string\",\n"
                    "  \"rest_periods\": [number],\n"
                    "  \"progression_notes\": \"string\"\n"
                    "}"
                )
            )
            
            # Create a structured prompt for the LLM
            prompt_content = {
                "task": "Generate a personalized workout plan",
                "user_profile": asdict(user_profile),
                "context": context,
                "instructions": (
                    "Please generate a workout plan based on the user's profile and context. "
                    "Include 4-6 exercises with appropriate sets, reps, and notes. "
                    "Specify the workout duration in minutes, intensity level (low/medium/high), "
                    "and rest periods between exercises in seconds."
                )
            }
            
            human_message = HumanMessage(
                content=json.dumps(prompt_content, default=str, indent=2)
            )
            
            # Log the messages being created
            logger.debug("Created system message: %s", system_message.content)
            logger.debug("Created human message: %s", human_message.content)
            
            # Return only the messages - the workflow will handle the rest of the state
            # This is a key change - we're only updating the messages in the state
            return {
                "messages": [system_message, human_message],
                "user_profile": user_profile,
                "context": context,
                "agent_type": agent_type
            }
            
        except Exception as e:
            logger.error(f"Error in start node: {e}", exc_info=True)
            return {
                **state,
                "response": {
                    "status": "error",
                    "error": f"Failed to initialize workflow: {str(e)}"
                }
            }
    
    # Removed _process_request_node as we simplified the workflow
    
    def _generate_response_node(self, state: AgentState) -> AgentState:
        """Generate a response using the appropriate agent."""
        try:
            logger.debug("Generating response with state keys: %s", list(state.keys()))
            
            # Get agent type and create agent
            agent_type = state.get("agent_type", AgentType.WORKOUT_PLANNER)
            logger.debug("Creating agent of type: %s", agent_type)
            
            agent = self._create_agent(agent_type)
            
            # Get messages from state - ensure we have messages
            messages = state.get("messages", [])
            if not messages:
                logger.error("No messages found in state")
                # Instead of failing, we'll create a default message
                messages = [
                    SystemMessage(content="You are a helpful fitness assistant."),
                    HumanMessage(content="Please generate a workout plan.")
                ]
                logger.warning("Created default messages for empty state")
            
            # Log the messages we're processing
            logger.debug("Processing %d messages in generate_response_node", len(messages))
            for i, msg in enumerate(messages):
                logger.debug("Message %d: %s - %s", i, type(msg).__name__, 
                           str(msg.content)[:100] + ("..." if len(str(msg.content)) > 100 else ""))
            
            # Get the last human message to use as input
            last_human_message = None
            system_message = None
            
            # Separate system and human messages
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    last_human_message = msg
                elif isinstance(msg, SystemMessage):
                    system_message = msg
            
            # If no human message, use a default one
            if not last_human_message:
                logger.warning("No human message found, using default")
                last_human_message = HumanMessage(content="Please generate a workout plan.")
            
            # Prepare the input for the agent
            try:
                # Get the content from the human message
                message_content = last_human_message.content
                
                # If it's a string that looks like JSON, parse it
                if isinstance(message_content, str) and message_content.strip().startswith('{'):
                    try:
                        message_content = json.loads(message_content)
                    except json.JSONDecodeError:
                        pass  # Use as-is if not valid JSON
                
                # Create the input for the agent
                agent_input = {
                    "input": message_content,
                    "system_message": system_message.content if system_message else ""
                }
                
                logger.debug("Invoking agent with input: %s", json.dumps(agent_input, default=str)[:500])
                
                # Invoke the agent with a timeout
                response = agent.invoke(agent_input)
                
                if response is None:
                    raise ValueError("Agent returned None response")
                
                logger.debug("Agent response type: %s", type(response))
                logger.debug("Agent response: %s", str(response)[:500])
                
                # Process the response
                output = response
                if hasattr(response, "output"):
                    output = response.output
                elif hasattr(response, "content"):
                    output = response.content
                
                # Ensure output is a dictionary
                if isinstance(output, str):
                    try:
                        output = json.loads(output)
                    except json.JSONDecodeError:
                        output = {"message": output}
                
                if not isinstance(output, dict):
                    output = {"message": str(output)}
                
                # Add status if not present
                if "status" not in output:
                    output["status"] = "success"
                
                # Log the output
                logger.debug("Processed output: %s", json.dumps(output, default=str)[:500])
                
                # Create the updated state with the response
                # This is a key change - we're preserving the original state and adding the response
                return {
                    **state,
                    "response": output,
                    "messages": messages + [AIMessage(content=json.dumps(output, default=str))]
                }
                
                
            except Exception as e:
                logger.error(f"Error in agent invocation: {str(e)}", exc_info=True)
                return {
                    "response": {
                        "error": f"Agent invocation failed: {str(e)}",
                        "status": "error"
                    },
                    **state
                }
                
        except Exception as e:
            logger.error(f"Error in response generation: {str(e)}", exc_info=True)
            return {
                "response": {
                    "error": f"Failed to generate response: {str(e)}",
                    "status": "error"
                },
                **state
            }
    
    # Removed _route_request as we simplified the workflow
    
    # Tool implementations
    def _get_user_profile(self, user_id: str) -> str:
        """Get the user's profile."""
        # In a real implementation, this would fetch from a database
        return json.dumps({
            "user_id": user_id,
            "fitness_level": "intermediate",
            "goals": ["lose weight", "build muscle"],
            "limitations": ["bad knee"],
            "preferences": {"workout_type": "strength training"},
            "current_stats": {"weight_kg": 75, "height_cm": 175}
        })
    
    def _get_workout_history(self, user_id: str, limit: int = 5) -> str:
        """Get the user's workout history.
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of historical workouts to return (default: 5)
            
        Returns:
            JSON string containing the user's workout history
        """
        try:
            logger.debug("Fetching workout history for user %s (limit: %d)", user_id, limit)
            
            # In a real implementation, this would query a database
            # For now, return mock data
            history = [
                {
                    "date": "2023-10-01",
                    "workout_type": "strength",
                    "duration_minutes": 45,
                    "exercises": [
                        {"name": "Push-ups", "sets": 3, "reps": "10-12", "weight_kg": "bodyweight"},
                        {"name": "Squats", "sets": 3, "reps": "12-15", "weight_kg": 60}
                    ]
                },
                {
                    "date": "2023-10-03",
                    "workout_type": "cardio",
                    "duration_minutes": 30,
                    "exercises": [
                        {"name": "Running", "distance_km": 5.0, "duration_minutes": 30, "avg_pace": "6:00/km"}
                    ]
                }
            ]
            
            # Limit the number of results
            history = history[:limit]
            
            return json.dumps({"workout_history": history}, indent=2)
            
        except Exception as e:
            error_msg = f"Error fetching workout history: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg, "status": "error"})
        # In a real implementation, this would fetch from a database
        return "Workout history here"
    
    def _generate_workout_plan(self, user_profile: str, context: str) -> str:
        """Generate a workout plan."""
        # This would be handled by the workflow
        return "Workout plan generation in progress..."
    
    def _get_exercise_library(self, muscle_group: str = None, equipment: str = None) -> str:
        """Get a list of exercises filtered by muscle group and/or equipment.
        
        Args:
            muscle_group: Optional muscle group to filter by (e.g., 'chest', 'legs')
            equipment: Optional equipment to filter by (e.g., 'dumbbell', 'barbell')
            
        Returns:
            JSON string containing the filtered list of exercises
        """
        try:
            logger.debug("Fetching exercise library with filters - muscle_group: %s, equipment: %s", 
                        muscle_group, equipment)
            
            # Mock exercise database
            exercises = [
                {
                    "name": "Push-up",
                    "muscle_groups": ["chest", "triceps", "shoulders"],
                    "equipment": ["bodyweight"],
                    "difficulty": "beginner"
                },
                {
                    "name": "Barbell Squat",
                    "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
                    "equipment": ["barbell", "power rack"],
                    "difficulty": "intermediate"
                },
                {
                    "name": "Dumbbell Shoulder Press",
                    "muscle_groups": ["shoulders", "triceps"],
                    "equipment": ["dumbbells", "bench"],
                    "difficulty": "beginner"
                },
                {
                    "name": "Pull-up",
                    "muscle_groups": ["back", "biceps"],
                    "equipment": ["pull-up bar"],
                    "difficulty": "intermediate"
                },
                {
                    "name": "Deadlift",
                    "muscle_groups": ["posterior chain", "back", "glutes"],
                    "equipment": ["barbell", "weights"],
                    "difficulty": "advanced"
                }
            ]
            
            # Apply filters
            if muscle_group:
                muscle_group = muscle_group.lower()
                exercises = [e for e in exercises if any(mg.lower() == muscle_group for mg in e["muscle_groups"])]
                
            if equipment:
                equipment = equipment.lower()
                exercises = [e for e in exercises if any(eq.lower() == equipment for eq in e["equipment"])]
            
            return json.dumps({"exercises": exercises}, indent=2)
            
        except Exception as e:
            error_msg = f"Error fetching exercise library: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg, "status": "error"})
    
    def _get_nutrition_guidance(self, user_id: str, goal: str = None) -> str:
        """Get personalized nutrition guidance based on user's goals.
        
        Args:
            user_id: The ID of the user
            goal: Optional specific goal to get guidance for (e.g., 'weight_loss', 'muscle_gain')
            
        Returns:
            JSON string containing nutrition guidance
        """
        try:
            logger.debug("Fetching nutrition guidance for user %s with goal: %s", user_id, goal)
            
            # In a real implementation, this would be personalized based on user data
            guidance = {
                "general_recommendations": {
                    "protein": "1.6-2.2g per kg of body weight for muscle gain",
                    "carbs": "3-5g per kg of body weight for moderate activity",
                    "fats": "20-35% of total calories",
                    "hydration": "At least 2-3 liters of water per day"
                },
                "meal_timing": {
                    "pre_workout": "Eat a balanced meal 2-3 hours before workout",
                    "post_workout": "Consume protein and carbs within 30-60 minutes after workout"
                },
                "food_sources": {
                    "protein": ["Chicken breast", "Fish", "Eggs", "Tofu", "Legumes"],
                    "carbs": ["Brown rice", "Quinoa", "Sweet potatoes", "Oats", "Fruits"],
                    "fats": ["Avocados", "Nuts", "Seeds", "Olive oil", "Fatty fish"]
                }
            }
            
            # Add goal-specific guidance if provided
            if goal == "weight_loss":
                guidance["goal_specific"] = {
                    "caloric_deficit": "Aim for a 300-500 calorie deficit per day",
                    "protein_intake": "Higher end of protein range to preserve muscle mass",
                    "fiber_intake": "30-40g per day to promote satiety"
                }
            elif goal == "muscle_gain":
                guidance["goal_specific"] = {
                    "caloric_surplus": "Aim for a 200-300 calorie surplus per day",
                    "protein_timing": "Distribute protein intake evenly across meals",
                    "recovery_nutrition": "Focus on post-workout nutrition for recovery"
                }
            
            return json.dumps(guidance, indent=2)
            
        except Exception as e:
            error_msg = f"Error fetching nutrition guidance: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg, "status": "error"})
    
    def _save_workout(self, user_id: str, workout_data: dict) -> str:
        """Save a completed workout.
        
        Args:
            user_id: The ID of the user
            workout_data: Dictionary containing workout details
            
        Returns:
            JSON string with status of the operation
        """
        try:
            logger.debug("Saving workout for user %s: %s", user_id, json.dumps(workout_data, indent=2))
            
            # In a real implementation, this would save to a database
            # For now, just return a success message
            return json.dumps({
                "status": "success",
                "message": "Workout saved successfully",
                "user_id": user_id,
                "workout_id": f"workout_{int(time.time())}",
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            error_msg = f"Error saving workout: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg, "status": "error"})
    
    # Public API
    async def process_request(
        self,
        agent_type: AgentType,
        user_profile: UserProfile,
        context: Dict[str, Any],
        response_model: type = dict
    ) -> dict:
        """Process a request using the agent system.
        
        Args:
            agent_type: The type of agent to use for processing
            user_profile: The user's profile information
            context: Additional context for the request
            response_model: The Pydantic model to validate the response against
            
        Returns:
            A dictionary containing the agent's response
        """
        logger.info("Processing %s request for user %s", agent_type.value, user_profile.user_id)
        
        # Create initial state with all required fields
        initial_state: AgentState = {
            "user_profile": user_profile,
            "context": context,
            "messages": [],  # Will be populated in start_node
            "agent_type": agent_type,
            "response": None
        }
        
        logger.debug("Initial state before workflow: %s", json.dumps(initial_state, default=str, indent=2))
        
        try:
            # Run the workflow
            logger.info("Starting workflow execution")
            result = await self.workflow.ainvoke(initial_state)
            
            # Process the response
            if not result or "response" not in result:
                raise ValueError("No response generated by the workflow")
            
            response_data = result["response"]
            logger.debug("Workflow completed with response: %s", json.dumps(response_data, default=str, indent=2))
            
            # If a response model is provided, validate the response
            if response_model and response_model != dict:
                logger.debug("Validating response against %s", response_model.__name__)
                try:
                    if isinstance(response_data, str):
                        response_data = json.loads(response_data)
                    elif response_data is None:
                        raise ValueError("Response data is None")
                        
                    if not isinstance(response_data, dict):
                        raise ValueError(f"Expected dict response, got {type(response_data).__name__}")
                        
                    return response_model(**response_data)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error("Failed to parse response: %s", str(e))
                    raise ValueError(f"Invalid response format: {e}")
                except Exception as e:
                    logger.error("Validation error: %s", str(e))
                    raise ValueError(f"Response validation failed: {e}")
            
            return response_data if response_data is not None else {}
            
        except Exception as e:
            logger.error("Error in process_request: %s", str(e), exc_info=True)
            
            # Create an error response
            error_response = {
                "status": "error",
                "message": str(e),
                "agent_type": agent_type.value,
                "user_id": user_profile.user_id
            }
            
            # If we have a response model, try to create a valid instance with error info
            if response_model and response_model != dict:
                try:
                    if hasattr(response_model, "model_fields"):
                        defaults = {}
                        for field_name, field in response_model.model_fields.items():
                            if field_name == "error":
                                defaults[field_name] = str(e)
                            elif field_name == "status":
                                defaults[field_name] = "error"
                            elif field.default is not None:
                                defaults[field_name] = field.default
                            elif hasattr(field, "default_factory") and field.default_factory is not None:
                                defaults[field_name] = field.default_factory()
                        
                        # Create the response model instance with error info
                        return response_model(**defaults)
                except Exception as model_err:
                    logger.error("Failed to create error response model: %s", str(model_err))
            
            return error_response
        """Process a request using the agent system.
        
        Args:
            agent_type: The type of agent to use for processing
            user_profile: The user's profile information
            context: Additional context for the request
            response_model: The Pydantic model to validate the response against
            
        Returns:
            A dictionary containing the agent's response
        """
        logger.info(f"Processing {agent_type.value} request for user {user_profile.user_id}")
        
        try:
            # Create initial state with user profile and context
            state: AgentState = {
                "user_profile": user_profile,
                "context": context,
                "messages": [],
                "agent_type": agent_type,
                "response": None
            }
            
            # Run the workflow
            logger.debug("Starting workflow execution")
            result = await self.workflow.ainvoke(state)
            
            # Process the response
            if not result or "response" not in result:
                raise ValueError("No response generated by the workflow")
            
            response_data = result["response"]
            logger.debug(f"Workflow completed with response: {response_data}")
            
            # If a response model is provided, validate the response
            if response_model and response_model != dict:
                logger.debug(f"Validating response against {response_model.__name__}")
                try:
                    if isinstance(response_data, str):
                        response_data = json.loads(response_data)
                    return response_model(**response_data)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse response: {e}")
                    raise ValueError(f"Invalid response format: {e}")
                except Exception as e:
                    logger.error(f"Validation error: {e}")
                    raise ValueError(f"Response validation failed: {e}")
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error in process_request: {e}", exc_info=True)
            
            # Create an error response
            error_response = {
                "status": "error",
                "message": str(e),
                "agent_type": agent_type.value,
                "user_id": user_profile.user_id
            }
            
            # If we have a response model, try to create a valid instance with error info
            if response_model and response_model != dict:
                try:
                    if hasattr(response_model, "model_fields"):
                        defaults = {}
                        for field_name, field in response_model.model_fields.items():
                            if field_name == "error":
                                defaults[field_name] = str(e)
                            elif field_name == "status":
                                defaults[field_name] = "error"
                            elif field.default is not None:
                                defaults[field_name] = field.default
                            elif hasattr(field, "default_factory") and field.default_factory is not None:
                                defaults[field_name] = field.default_factory()
                        
                        # Create the response model instance with error info
                        return response_model(**defaults)
                except Exception as model_err:
                    logger.error(f"Failed to create error response model: {model_err}")
            
            return error_response
            
            # Set up the initial state with proper typing
            state: AgentState = {
                "user_profile": user_profile,
                "context": {
                    **context,
                    "agent_type": agent_type.value
                },
                "messages": [
                    SystemMessage(content="You are a helpful fitness assistant."),
                    HumanMessage(content=f"User profile: {json.dumps(asdict(user_profile), default=str)}\n\nContext: {json.dumps(context, default=str)}")
                ],
                "agent_type": agent_type,
                "response": None
            }
            
            logger.debug(f"Initial state: {json.dumps(state, default=str, indent=2)}")
            
            try:
                # Run the workflow
                result = await self.workflow.ainvoke(state)
                logger.debug(f"Workflow result: {json.dumps(result, default=str, indent=2)}")
                
                # Process the response
                if "response" not in result or result["response"] is None:
                    raise ValueError("No response generated by the workflow")
                
                response_data = result["response"]
                
                # If there was an error in the response, raise it
                if isinstance(response_data, dict) and "error" in response_data:
                    raise ValueError(response_data["error"])
                
                # If a response model is provided, validate against it
                if response_model and response_model != dict:
                    logger.debug(f"Validating response against {response_model.__name__}")
                    try:
                        if isinstance(response_data, str):
                            response_data = json.loads(response_data)
                        return response_model(**response_data)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Failed to parse response as {response_model.__name__}: {e}")
                        raise ValueError(f"Invalid response format: {e}")
                    except Exception as e:
                        logger.error(f"Validation error: {e}")
                        raise ValueError(f"Response validation failed: {e}")
                
                return response_data
                
            except Exception as e:
                logger.error(f"Error in workflow execution: {str(e)}", exc_info=True)
                raise ValueError(f"Failed to process request: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in process_request: {str(e)}", exc_info=True)
            # Return a default response with error information
            error_response = {
                "status": "error",
                "message": str(e),
                "agent_type": agent_type.value,
                "user_id": user_profile.user_id
            }
            
            # If we have a response model, try to return a valid instance with error info
            if response_model and response_model != dict:
                try:
                    # Create a minimal valid instance with error info
                    if hasattr(response_model, "__fields__"):
                        defaults = {}
                        for field_name, field in response_model.__fields__.items():
                            if field_name == "error":
                                defaults[field_name] = str(e)
                            elif field_name == "status":
                                defaults[field_name] = "error"
                            elif field.default is not None:
                                defaults[field_name] = field.default
                            elif field.default_factory is not None:
                                defaults[field_name] = field.default_factory()
                        return response_model(**defaults)
                except Exception as model_err:
                    logger.error(f"Failed to create error response model: {model_err}")
            
            return error_response
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise

# Example usage
if __name__ == "__main__":
    # Set up environment variables or load from .env
    
    
    # Initialize the agent system
    agent_system = FitnessAgentSystem()
    
    # Example user profile
    user_profile = UserProfile(
        user_id="123",
        fitness_level="intermediate",
        goals=["lose weight", "build muscle"],
        limitations=["bad knee"],
        preferences={"workout_type": "strength training"},
        current_stats={"weight_kg": 75, "height_cm": 175}
    )
    
    # Example context
    context = {
        "available_time": 30,
        "equipment": "Gym",
        "last_workout": "2 days ago",
        "energy_level": "medium",
        "query": "Create a workout plan"
    }
    
    # Process a request
    import asyncio
    
    async def main():
        try:
            response = await agent_system.process_request(
                agent_type=AgentType.WORKOUT_PLANNER,
                user_profile=user_profile,
                context=context,
                response_model=WorkoutPlan
            )
            
            print("\n=== Workout Plan ===")
            print(json.dumps(response.dict(), indent=2))
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(main())
