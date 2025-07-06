import { z } from 'zod';
import { BaseFitnessTool, baseSchema } from './base';
import dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

// Type for the YouTube search input
type YouTubeSearchInput = { input?: string };

interface YouTubeVideo {
  videoId: string;
  title: string;
  description: string;
  channelTitle: string;
  thumbnailUrl: string;
  url: string;
}

export class YouTubeSearchTool extends BaseFitnessTool<typeof baseSchema> {
  private readonly apiKey: string;
  private readonly baseUrl = 'https://www.googleapis.com/youtube/v3/search';
  
  // Schema for the tool's input - must match base schema with optional input
  protected _inputSchema = z.object({
    input: z.string().optional().describe('The search query for YouTube videos')
  });

  constructor() {
    super({
      name: 'search_youtube_videos',
      description: 'Search for fitness-related YouTube videos based on the given query',
      returnDirect: false
    });

    this.apiKey = process.env.YOUTUBE_API_KEY || '';
    if (!this.apiKey) {
      throw new Error('YOUTUBE_API_KEY environment variable is required');
    }
  }

  get inputSchema() {
    return this._inputSchema;
  }

  protected async _call(input: YouTubeSearchInput): Promise<string> {
    try {
      // Extract the query from the input
      const query = input?.input;
      
      if (!query) {
        throw new Error('Search query is required');
      }
      
      if (!query) {
        throw new Error('Search query cannot be empty');
      }
      
      const maxResults = 3; // Default value
      
      const params = {
        part: 'snippet',
        q: query,
        type: 'video',
        maxResults,
        key: this.apiKey,
        videoEmbeddable: 'true',
        relevanceLanguage: 'en',
        safeSearch: 'moderate'
      };

      console.log('Searching YouTube with params:', { ...params, key: '***' });
      
      const response = await axios.get(this.baseUrl, { 
        params,
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (!response.data.items || response.data.items.length === 0) {
        return 'No videos found for the given query.';
      }

      const videos: YouTubeVideo[] = response.data.items.map((item: any) => ({
        videoId: item.id.videoId,
        title: item.snippet.title,
        description: item.snippet.description,
        channelTitle: item.snippet.channelTitle,
        thumbnailUrl: item.snippet.thumbnails?.high?.url || item.snippet.thumbnails?.default?.url || '',
        url: `https://www.youtube.com/watch?v=${item.id.videoId}`
      }));

      // Format the response as markdown for better readability
      const formattedVideos = videos.map((video, index) => 
        `### ${index + 1}. [${video.title}](${video.url})\n` +
        `**Channel:** ${video.channelTitle}\n` +
        `${video.description.substring(0, 150)}...\n`
      ).join('\n');

      return `Here are some YouTube videos that might help with "${query}":\n\n${formattedVideos}`;
      
    } catch (error) {
      console.error('Error searching YouTube videos:', error);
      if (axios.isAxiosError(error)) {
        console.error('YouTube API Error:', {
          status: error.response?.status,
          data: error.response?.data,
          headers: error.response?.headers
        });
      }
      return 'Sorry, I encountered an error while searching for YouTube videos. Please try again later.';
    }
  }
}
