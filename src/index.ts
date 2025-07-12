import { startServer } from './server';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

console.log('Fitness Agents Service starting...');

// Start the server
startServer();
