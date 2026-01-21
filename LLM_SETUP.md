# LLM Integration with Groq

The summarizer now uses **Groq** for intelligent, LLM-powered memory summaries!

## Setup Instructions

### 1. Get a Free Groq API Key

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to the API Keys section
4. Create a new API key

### 2. Add Your API Key

Create a `.env` file in the project root (or copy from `.env.example`):

```bash
cp .env.example .env
```

Then edit `.env` and add your Groq API key:

```
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 3. Restart the Server

```bash
python3.12 app.py
```

The server will now print:
```
[Summarizer] Groq LLM enabled
```

## Features

- **Smart Summaries**: Uses Mixtral 8x7B model to understand emotional context and generate meaningful 2-3 line summaries
- **Free Tier**: Groq offers generous free tier with high rate limits (1000+ requests/day)
- **Fast Inference**: Groq's platform is optimized for speed, perfect for real-time conversations
- **Fallback Support**: If LLM fails, automatically falls back to simple text extraction
- **Privacy Friendly**: Can be self-hosted or used with your own LLM

## How It Works

When a conversation ends:

1. **LLM Processing**: Sends the conversation transcript to Groq's Mixtral model
2. **Emotional Analysis**: The LLM extracts emotional content and important topics
3. **Memory Generation**: Creates a warm, personal 2-3 line summary
4. **Storage**: The summary is saved to the memory store for future recalls

## Example Summary

**Transcript:**
> "I had such a wonderful time. We talked about my graduation coming up and how nervous I am. But you said something that really stuck with me - you know, we want to see tomorrow M.V."

**Generated Summary:**
> "You talked about your upcoming graduation and shared some concerns about it. Your loved one encouraged you and expressed their desire to support you through this important milestone. There's genuine care and excitement for your future together."

## Troubleshooting

### "GROQ_API_KEY not found"

Make sure:
1. You created a `.env` file in the project root
2. The `.env` file contains `GROQ_API_KEY=your_key`
3. You restarted the server after adding the key

### "LLM error: authentication error"

Your API key might be incorrect or expired:
1. Check your key at [console.groq.com](https://console.groq.com)
2. Delete the old key and create a new one
3. Update `.env` and restart

### Using Without LLM

The system works perfectly fine without an API key:
- Simple text extraction summarization (fallback method)
- No additional costs
- All other features work normally

## Free Tier Limits

Groq's free tier includes:
- **1,000+ API calls per day**
- **High speed inference**
- **Community support**

This is more than enough for typical daily use of the memory assist system.

## Next Steps

1. [Get your free Groq API key](https://console.groq.com)
2. Add it to your `.env` file
3. Restart the server
4. Start having conversations - your summaries will be much more meaningful!
