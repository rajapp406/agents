# Fitness Agents Service

A TypeScript-based service for fitness-related AI agents using LangChain and Express.

## Features

- Workout plan generation
- Nutrition advice
- Progress analysis
- Motivational coaching
- RESTful API

## Prerequisites

- Node.js 18+
- npm or yarn
- Azure OpenAI API credentials

## Setup

1. Copy `.env.example` to `.env` and fill in your Azure OpenAI credentials:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Development

To run in development mode with auto-reload:
```bash
npm run dev
```

## Building for Production

1. Build the application:
   ```bash
   npm run build
   ```

2. Start the server:
   ```bash
   npm start
   ```

## API Endpoints

- `POST /api/workout-plan` - Generate a personalized workout plan
- `GET /health` - Health check endpoint

## Testing

To run tests:
```bash
npm test
```

## Environment Variables

- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_VERSION` - API version (default: 2023-05-15)
- `AZURE_OPENAI_MODEL` - Model name (default: gpt-4)
- `PORT` - Server port (default: 3000)
- `NODE_ENV` - Environment (development/production)
- `LOG_LEVEL` - Logging level (default: info)

## Project Structure

```
src/
  services/
    FitnessAgentSystem.ts  # Main agent system implementation
  types/                  # TypeScript type definitions
  server.ts               # Express server setup
  index.ts                # Application entry point
```
