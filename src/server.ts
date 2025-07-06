import express, { Request, Response, NextFunction, RequestHandler, ErrorRequestHandler } from 'express';
import { body, validationResult } from 'express-validator';
import { FitnessAgentSystem } from './services/FitnessAgentSystem';
import { AgentType, UserProfile, WorkoutPlan } from './types';
import { createWorkoutAgent } from './agents/workoutAgent';
import dotenv from 'dotenv';
import winston from 'winston';
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

declare module 'express-serve-static-core' {
  interface Request {
    user?: any;
  }
}

// Load environment variables
dotenv.config();

// Configure logging
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// Swagger configuration
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Fitness Agents API',
      version: '1.0.0',
      description: 'API for fitness-related AI agents',
    },
    servers: [
      {
        url: `http://localhost:${process.env.PORT || 3000}`,
        description: 'Development server',
      },
    ],
    components: {
      schemas: {
        WorkoutPlan: {
          type: 'object',
          properties: {
            exercises: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  name: { type: 'string' },
                  sets: { type: 'number' },
                  reps: { type: ['number', 'string'] },
                  duration: { type: 'number' },
                  notes: { type: 'string' }
                }
              }
            },
            duration: { type: 'number' },
            intensity: { type: 'string' },
            restPeriods: {
              type: 'array',
              items: { type: 'number' }
            },
            progressionNotes: { type: 'string' },
            status: { type: 'string', enum: ['success', 'error'] },
            error: { type: 'string' }
          }
        }
      }
    }
  },
  apis: ['./src/**/*.ts'],
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);

// Initialize Express app
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use((req: Request, res: Response, next: NextFunction) => {
  logger.info(`${req.method} ${req.path}`);
  next();
});

// Initialize the agent system
let agentSystem: FitnessAgentSystem;

try {
  agentSystem = new FitnessAgentSystem();
  logger.info('Fitness Agent System initialized successfully');
} catch (error) {
  logger.error('Failed to initialize Fitness Agent System:', error);
  process.exit(1);
}

// Routes
/**
 * @openapi
 * /api/workout-plan:
 *   post:
 *     summary: Generate a personalized workout plan
 *     description: Creates a customized workout plan based on user profile and preferences
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - userId
 *               - fitnessLevel
 *               - goals
 *               - limitations
 *               - preferences
 *               - currentStats
 *             properties:
 *               userId:
 *                 type: string
 *                 description: Unique identifier for the user
 *               fitnessLevel:
 *                 type: string
 *                 enum: [beginner, intermediate, advanced]
 *                 description: User's fitness level
 *               goals:
 *                 type: array
 *                 items:
 *                   type: string
 *                   enum: [weight_loss, muscle_gain, endurance, strength, flexibility, general_fitness]
 *                 description: User's fitness goals
 *               limitations:
 *                 type: array
 *                 items:
 *                   type: string
 *                 description: Any physical limitations or injuries
 *               preferences:
 *                 type: object
 *                 properties:
 *                   workoutDays:
 *                     type: array
 *                     items:
 *                       type: string
 *                       enum: [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
 *                   workoutDuration:
 *                     type: number
 *                     description: Preferred workout duration in minutes
 *                   equipment:
 *                     type: array
 *                     items:
 *                       type: string
 *               currentStats:
 *                 type: object
 *                 properties:
 *                   weight:
 *                     type: number
 *                     description: User's weight in kg
 *                   height:
 *                     type: number
 *                     description: User's height in cm
 *                   age:
 *                     type: number
 *     responses:
 *       200:
 *         description: Successfully generated workout plan
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/WorkoutPlan'
 *       400:
 *         description: Invalid input
 *       500:
 *         description: Server error
 */
// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'fitness-agents',
    version: '1.0.0'
  });
});

// Workout plan endpoint
app.post(
  '/api/workout-plan',
  [
    body('userId').isString().notEmpty().withMessage('User ID is required'),
    body('fitnessLevel')
      .isString()
      .isIn(['beginner', 'intermediate', 'advanced'])
      .withMessage('Invalid fitness level'),
    body('goals')
      .isArray()
      .withMessage('Goals must be an array'),
    body('limitations')
      .isArray()
      .withMessage('Limitations must be an array'),
    body('preferences')
      .isObject()
      .withMessage('Preferences must be an object')
      .custom((value) => {
        if (!value.workoutDays || !Array.isArray(value.workoutDays)) {
          throw new Error('workoutDays is required in preferences');
        }
        return true;
      }),
    body('currentStats')
      .isObject()
      .withMessage('Current stats must be an object')
      .custom((value) => {
        if (value.weight === undefined || value.height === undefined || value.age === undefined) {
          throw new Error('weight, height, and age are required in currentStats');
        }
        return true;
      })
  ],
  (async (req: Request, res: Response) => {
    try {
      // Validate request
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const userProfile: UserProfile = {
        userId: req.body.userId,
        fitnessLevel: req.body.fitnessLevel,
        goals: req.body.goals,
        limitations: req.body.limitations,
        preferences: req.body.preferences,
        currentStats: req.body.currentStats
      };

      const context = req.body.context || {};
      
      // Generate workout plan
      const workoutPlan = await agentSystem.generateWorkoutPlan(userProfile, context);
      
      res.json(workoutPlan);
    } catch (error) {
      logger.error('Error generating workout plan:', error);
      res.status(500).json({
        status: 'error',
        error: 'Failed to generate workout plan',
        details: error instanceof Error ? error.message : 'Unknown error'
      });
      return;
    }
  }) as RequestHandler
);

// Serve Swagger documentation
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

/**
 * @openapi
 * /health:
 *   get:
 *     summary: Health check endpoint
 *     description: Returns the health status of the API
 *     responses:
 *       200:
 *         description: API is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: ok
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 */
app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling middleware
const errorHandler: ErrorRequestHandler = (err: Error, _req: Request, res: Response, _next: NextFunction) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({
    status: 'error',
    error: 'Internal server error',
    message: err.message
  });
};

/**
 * @openapi
 * /api/chat:
 *   post:
 *     summary: Chat with the fitness agent
 *     description: Send a message to the fitness agent and get a response
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - message
 *             properties:
 *               message:
 *                 type: string
 *                 description: The message to send to the agent
 *               chatHistory:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     role:
 *                       type: string
 *                       enum: [user, assistant]
 *                     content:
 *                       type: string
 *     responses:
 *       200:
 *         description: The agent's response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 response:
 *                   type: string
 *       400:
 *         description: Invalid input
 *       500:
 *         description: Server error
 */
app.post('/api/chat', async (req: Request, res: Response) => {
  try {
    const { message, chatHistory = [] } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const executor = await createWorkoutAgent();
    const result = await executor.invoke({
      input: message,
      chat_history: chatHistory,
    });

    res.json({ 
      response: result.output,
      chatHistory: [
        ...chatHistory,
        { role: 'user', content: message },
        { role: 'assistant', content: result.output }
      ]
    });
  } catch (error) {
    logger.error('Error in chat endpoint:', error);
    res.status(500).json({ error: 'Failed to process chat message' });
  }
});

app.use(errorHandler);

// Start server
app.listen(port, () => {
  logger.info(`Server running on port ${port}`);
  console.log(`Server is running on http://localhost:${port}`);
});

export default app;
