import openai
from config import Config

openai.api_key = Config.OPENAI_API_KEY

class AIEngine:
    @staticmethod
    async def get_response(messages, model=None, personality="default"):
        model = model or Config.DEFAULT_MODEL
        
        system_prompt = Config.BOT_PERSONALITIES.get(personality, Config.BOT_PERSONALITIES["default"])
        
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            if model.startswith("gpt"):
                response = openai.chat.completions.create(
                    model=model,
                    messages=full_messages,
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            else:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=full_messages,
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    async def generate_image(prompt, size="1024x1024"):
        try:
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )
            return response.data[0].url
        except Exception as e:
            return None, str(e)