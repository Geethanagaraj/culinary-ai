from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import time
import random
from datetime import datetime, timedelta
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # Required for session

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY not found in environment variables")

print(f"GEMINI_API_KEY loaded: {GEMINI_API_KEY[:10]}...")  # Print first 10 chars for verification

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # List available models
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model: {m.name}")
    # Use the correct model
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("Gemini model initialized successfully")
except Exception as e:
    print(f"Error initializing Gemini model: {str(e)}")
    raise

# Store previously generated dishes
previously_generated_dishes = {}

@app.route('/')
def index():
    return render_template('index.html') 
                         
@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/recipe-details')
def recipe_details():
    food_name = request.args.get('food')
    mood = request.args.get('mood')
    
    if not food_name:
        return render_template('recipe_details.html', error="Missing food parameter")
    
    try:
        # Construct a more specific prompt for the single recipe
        if mood:
            recipe_prompt = f"""You are a food recommendation system. For someone feeling {mood}, provide detailed information about {food_name}."""
        else:
            recipe_prompt = f"""You are a food recommendation system. Provide detailed information about {food_name}."""

        recipe_prompt += """

Provide the following information in EXACTLY this JSON format:

{
    "name": "Food Item Name",
    "description": "Brief description of the dish and its cultural significance",
    "benefits": [
        "Benefit 1",
        "Benefit 2",
        "Benefit 3",
        "Benefit 4"
    ],
    "recipe_details": {
        "ingredients": [
            "Ingredient 1 with exact measurement (e.g., 2 cups flour)",
            "Ingredient 2 with exact measurement (e.g., 1 tablespoon sugar)",
            "Ingredient 3 with exact measurement (e.g., 3 cloves garlic, minced)"
        ],
        "instructions": [
            "Step 1: Start by preparing all ingredients. Make sure everything is measured and ready to use. This will make the cooking process smoother and more enjoyable.",
            "Step 2: Begin with the base preparation. Take your time to do this correctly as it forms the foundation of the dish. Follow the measurements exactly for best results.",
            "Step 3: Move on to the main cooking process. Keep the heat at the recommended temperature and stir frequently to prevent burning. This step is crucial for the dish's flavor development.",
            "Step 4: Add the finishing touches. This is where you can add your personal touch while still following the basic guidelines. Make sure to taste and adjust seasoning if needed.",
            "Step 5: Let the dish rest before serving. This allows the flavors to meld together and ensures the best possible taste experience."
        ],
        "preparation_time": "XX minutes (include prep and marination time)",
        "cooking_time": "XX minutes (include actual cooking time)",
        "difficulty": "Easy/Medium/Hard",
        "servings": "Number of servings",
        "nutritional_info": {
            "calories": "per serving",
            "protein": "per serving",
            "carbs": "per serving",
            "fat": "per serving"
        },
        "tips": [
            "Tip 1: Read through all instructions before starting to ensure you have everything you need",
            "Tip 2: Keep your workspace clean and organized for better efficiency",
            "Tip 3: Taste as you go and adjust seasoning gradually",
            "Tip 4: Don't rush the cooking process - good food takes time",
            "Tip 5: Use fresh ingredients whenever possible for the best flavor"
        ],
        "equipment": [
            "Required equipment 1",
            "Required equipment 2"
        ]
    }
}

Important:
1. Return ONLY the JSON object, no other text
2. The food item must have exactly 4 benefits
3. The response must be valid JSON that can be parsed
4. Use double quotes for all strings
5. Do not include any markdown formatting or additional text
6. Provide exact measurements for ingredients
7. Include timing and temperature in instructions where applicable
8. Add nutritional information per serving
9. Include practical tips for best results
10. Make instructions detailed but easy to follow
11. Break down complex steps into simpler sub-steps
12. Include helpful hints within the instructions
13. Use clear, everyday language that anyone can understand"""
        
        print(f"\nGenerating recipe details for: {food_name}" + (f" (Mood: {mood})" if mood else ""))
        response = model.generate_content(recipe_prompt)
        
        if not response or not hasattr(response, 'text'):
            print("Error: Invalid response from Gemini API")
            return render_template('recipe_details.html', error="Failed to get recipe details from the AI service")
            
        recipe_text = response.text.strip()
        print(f"\nGemini Response Text:\n{recipe_text}")
        
        if not recipe_text:
            print("Error: Empty response from Gemini API")
            return render_template('recipe_details.html', error="No recipe details received from the AI service")
        
        # Clean up the response to ensure it's valid JSON
        recipe_text = recipe_text.replace('```json', '').replace('```', '').strip()
        
        try:
            recipe_data = json.loads(recipe_text)
            
            # Validate the structure
            required_fields = ['name', 'description', 'benefits', 'recipe_details']
            if not all(field in recipe_data for field in required_fields):
                raise ValueError("Missing required fields in recipe data")
                
            if not isinstance(recipe_data['benefits'], list) or len(recipe_data['benefits']) != 4:
                raise ValueError("Invalid benefits format")
                
            required_recipe_fields = ['ingredients', 'instructions', 'preparation_time', 'cooking_time', 
                                    'difficulty', 'servings', 'nutritional_info', 'tips', 'equipment']
            if not all(field in recipe_data['recipe_details'] for field in required_recipe_fields):
                raise ValueError("Missing required fields in recipe details")
            
            return render_template('recipe_details.html', 
                                food_name=recipe_data['name'],
                                description=recipe_data['description'],
                                benefits=recipe_data['benefits'],
                                recipe_details=recipe_data['recipe_details'])
            
        except json.JSONDecodeError as e:
            print(f"Error parsing recipe JSON: {str(e)}")
            print(f"Raw response: {recipe_text}")
            return render_template('recipe_details.html', error="Failed to parse recipe details")
        except ValueError as e:
            print(f"Error validating recipe data: {str(e)}")
            return render_template('recipe_details.html', error="Invalid recipe data format")
            
    except Exception as e:
        print(f"Error getting recipe details: {str(e)}")
        return render_template('recipe_details.html', error="An unexpected error occurred while getting recipe details")

@app.route('/recipe-generator')
def recipe_generator():
    return render_template('recipe-generator.html')

@app.route('/mood-based')
def mood_based():
    return render_template('mood-based.html')

@app.route('/generate_mood_recipe', methods=['POST'])
def generate_mood_recipe():
    try:
        data = request.get_json()
        if not data or 'mood' not in data:
            return jsonify({'error': 'No mood provided'}), 400
            
        mood = data['mood']
        print(f"\nGenerating recipe for mood: {mood}")
        
        # Get previously generated dishes for this mood
        previous_dishes = previously_generated_dishes.get(mood, [])
        
        # Add timestamp and random seed to ensure different responses
        timestamp = int(time.time())
        random_seed = random.randint(1, 1000)
        
        # Construct the mood-based recipe prompt for Gemini with emphasis on familiar dishes and regional diversity
        mood_prompt = f"""You are a food recommendation system. For someone feeling {mood}, suggest 4 specific food items with the following regional distribution:
- 2 South Indian dishes (from Tamil Nadu, Kerala, Karnataka, Andhra Pradesh, or Telangana)
- 1 North Indian dish (from Punjab, Delhi, Uttar Pradesh, or Rajasthan)
- 1 dish from any other region of India (Maharashtra, Gujarat, West Bengal, etc.)

IMPORTANT: 
1. Each food item must be completely different and unique
2. Do not suggest variations of the same dish
3. Specify the region of origin for each dish
4. Include traditional preparation methods
5. Ensure diversity in cooking techniques and ingredients
6. Generate completely different food items than previous suggestions
7. Use this seed ({timestamp}{random_seed}) to generate unique combinations
8. Focus on popular and familiar dishes that most people would recognize
9. Choose dishes that are commonly available in restaurants and homes
10. Ensure each dish has distinct ingredients and preparation methods
11. Select dishes that are well-known in their respective regions
12. Avoid very rare or obscure dishes
13. Include dishes that are commonly prepared in households
14. Choose dishes that are popular in both urban and rural areas
15. Select dishes that are frequently featured in Indian cuisine
16. DO NOT suggest any of these previously suggested dishes: {', '.join(previous_dishes) if previous_dishes else 'None'}
17. Ensure each dish is significantly different from the previous suggestions
18. Include a mix of breakfast, lunch, dinner, and snack items
19. Vary the cooking methods (steamed, fried, baked, etc.)
20. Include both vegetarian and non-vegetarian options

For each food item, provide the following information in EXACTLY this JSON format:

[
    {{
        "name": "Food Item Name (must be a well-known dish)",
        "region": "Region of origin (e.g., Tamil Nadu, Punjab, etc.)",
        "description": "Brief description of why this food is suitable for this mood and its cultural significance",
        "benefits": [
            "Benefit 1",
            "Benefit 2",
            "Benefit 3",
            "Benefit 4"
        ],
        "recipe_details": {{
            "ingredients": [
                "Ingredient 1 with exact measurement (e.g., 2 cups rice flour)",
                "Ingredient 2 with exact measurement (e.g., 1 tablespoon mustard seeds)",
                "Ingredient 3 with exact measurement (e.g., 3 cloves garlic, minced)"
            ],
            "instructions": [
                "Step 1: Detailed instruction with timing and temperature if applicable",
                "Step 2: Detailed instruction with timing and temperature if applicable",
                "Step 3: Detailed instruction with timing and temperature if applicable"
            ],
            "preparation_time": "XX minutes (include prep and marination time)",
            "cooking_time": "XX minutes (include actual cooking time)",
            "difficulty": "Easy/Medium/Hard",
            "servings": "Number of servings",
            "nutritional_info": {{
                "calories": "per serving",
                "protein": "per serving",
                "carbs": "per serving",
                "fat": "per serving"
            }},
            "tips": [
                "Tip 1 for best results",
                "Tip 2 for variations",
                "Tip 3 for storage"
            ],
            "equipment": [
                "Required equipment 1",
                "Required equipment 2"
            ]
        }}
    }}
]

Important:
1. Return ONLY the JSON array, no other text
2. Each food item must have exactly 4 benefits
3. The response must be valid JSON that can be parsed
4. Use double quotes for all strings
5. Do not include any markdown formatting or additional text
6. Suggest only popular and familiar regional dishes
7. Include traditional cooking methods and ingredients
8. Keep the instructions simple and easy to follow
9. Provide exact measurements for ingredients
10. Include timing and temperature in instructions where applicable
11. Add nutritional information per serving
12. Include practical tips for best results
13. Each food item must be completely unique and different from the others
14. Do not suggest variations of the same dish
15. Ensure diversity in cuisine types and cooking methods
16. Specify the region of origin for each dish
17. Include traditional preparation methods
18. Use authentic regional ingredients where possible
19. Focus on dishes that are commonly known and prepared
20. Choose dishes that are popular in their respective regions
21. Ensure each dish is significantly different from previous suggestions
22. Include a mix of meal types (breakfast, lunch, dinner, snacks)
23. Vary the cooking methods for each dish
24. Include both vegetarian and non-vegetarian options"""
        
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                print(f"\nAttempt {attempt + 1} of {max_attempts}")
                print("Sending request to Gemini API...")
                response = model.generate_content(mood_prompt)
                
                if not response or not hasattr(response, 'text'):
                    print("Error: Invalid response from Gemini API")
                    return jsonify({'error': 'Invalid response from recipe generation service'}), 500
                    
                suggestions = response.text.strip()
                print(f"\nGemini Response Text:\n{suggestions}")
                
                if not suggestions:
                    print("Error: Empty response from Gemini API")
                    return jsonify({'error': 'Empty response from recipe generation service'}), 500
                
                # Clean up the response to ensure it's valid JSON
                suggestions = suggestions.replace('```json', '').replace('```', '').strip()
                suggestions_data = json.loads(suggestions)
                
                # Validate the structure and check for uniqueness
                if not isinstance(suggestions_data, list) or len(suggestions_data) != 4:
                    raise ValueError("Invalid response format")
                
                # Check for unique food items
                food_names = [item['name'].lower().strip() for item in suggestions_data]
                if len(set(food_names)) != len(food_names):
                    print("Warning: Duplicate food items found. Regenerating...")
                    attempt += 1
                    continue
                
                # Check against previous dishes
                if any(name in previous_dishes for name in food_names):
                    print("Warning: Some dishes were previously suggested. Regenerating...")
                    attempt += 1
                    continue
                
                # Validate each item
                for item in suggestions_data:
                    if not all(key in item for key in ['name', 'region', 'description', 'benefits', 'recipe_details']):
                        raise ValueError("Missing required fields")
                    if not isinstance(item['benefits'], list) or len(item['benefits']) != 4:
                        raise ValueError("Invalid benefits format")
                
                # Update previously generated dishes
                previously_generated_dishes[mood] = previous_dishes + food_names
                
                print("Successfully generated unique food items")
                return jsonify(suggestions_data)
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing response: {str(e)}")
                print(f"Raw response: {suggestions}")
                attempt += 1
                if attempt == max_attempts:
                    return jsonify({'error': f'Failed to generate unique recipe suggestions after {max_attempts} attempts'}), 500
                continue
                
        return jsonify({'error': f'Failed to generate unique recipe suggestions after {max_attempts} attempts'}), 500
            
    except Exception as e:
        print(f"\nServer Error: {str(e)}")
        return jsonify({'error': f'Server Error: {str(e)}'}), 500

@app.route('/generate_recipe', methods=['POST'])
def generate_recipe():
    try:
        print("\n=== Starting Recipe Generation ===")
        data = request.get_json()
        print(f"Received request data: {data}")
        
        if not data:
            print("Error: No data received in request")
            return jsonify({'error': 'No data provided'}), 400
            
        if 'ingredients' not in data:
            print("Error: No ingredients provided in request")
            return jsonify({'error': 'No ingredients provided'}), 400
            
        ingredients = ', '.join(data['ingredients'])
        print(f"\nGenerating recipe for ingredients: {ingredients}")
        
        # Construct the recipe generation prompt for Gemini
        recipe_prompt = f"""Create a detailed recipe using these ingredients: {ingredients}

IMPORTANT: You MUST follow this EXACT structure in your response. Each section must be clearly separated by two newlines and start with the section header exactly as shown:

1. Recipe Title:
[Your recipe title here]

2. Basic Info:
- Preparation time: [time]
- Cooking time: [time]
- Total time: [time]
- Number of servings: [number]
- Difficulty level: [Easy/Medium/Hard]
- Estimated cost per serving: [amount]

3. Ingredients:
- [Ingredient 1 with measurement]
- [Ingredient 2 with measurement]
- [Additional ingredients...]

4. Substitutions:
- [Original Ingredient]: [Substitution Option]
- [Additional substitutions...]

5. Instructions:
1. [Step 1]
2. [Step 2]
3. [Additional steps...]

6. Pro Tips:
- [Tip 1]
- [Tip 2]
- [Additional tips...]

7. Nutritional Information (per serving):
- Calories: [number]
- Protein: [amount]
- Carbohydrates: [amount]
- Fat: [amount]
- Fiber: [amount]
- Sodium: [amount]
- Sugar: [amount]
- Cholesterol: [amount]

8. Dietary Information:
- Diet Categories: [list applicable categories]
- Allergen Information: [list allergens]
- Health Benefits: [list benefits]
- Medical Considerations: [list considerations]
- Who should avoid: [list if applicable]
- Religious/Cultural Considerations: [list if applicable]

9. Additional Information:
- Required Kitchen Equipment: [list equipment]
- Storage Instructions: [instructions]
- Reheating Instructions: [instructions]
- Meal Prep Tips: [tips]
- Wine/Beverage Pairing: [suggestions]
- Side Dish Recommendations: [suggestions]
- Presentation Tips: [tips]
- Cost-saving Tips: [tips]

Make sure to:
1. Use exact measurements
2. Provide clear, step-by-step instructions
3. Include all sections, even if some are marked as "N/A"
4. Format each section exactly as shown above
5. Separate sections with two newlines
6. Use bullet points and numbered lists where indicated."""
        
        try:
            print("\nSending request to Gemini API...")
            # Get recipe from Gemini
            response = model.generate_content(recipe_prompt)
            print(f"\nGemini API Raw Response: {response}")
            
            if not response or not hasattr(response, 'text'):
                print("Error: Invalid response from Gemini API")
                return jsonify({'error': 'Invalid response from recipe generation service'}), 500
                
            recipe_text = response.text
            print(f"\nGemini Response Text:\n{recipe_text}")
            
            if not recipe_text:
                print("Error: Empty response from Gemini API")
                return jsonify({'error': 'Empty response from recipe generation service'}), 500
            
            # Parse the recipe text into structured format
            print("\nParsing recipe text into structured format...")
            sections = recipe_text.split('\n\n')
            recipe = {
                'title': '',
                'prepTime': '',
                'cookTime': '',
                'totalTime': '',
                'servings': '',
                'difficulty': '',
                'costPerServing': '',
                'ingredients': [],
                'substitutions': {},
                'instructions': [],
                'proTips': [],
                'nutrition': {},
                'dietary': [],
                'equipment': [],
                'storage': [],
                'pairings': [],
                'presentation': [],
                'costSavingTips': []
            }
            
            print("\nProcessing sections...")
            for section in sections:
                if not section.strip():
                    continue
                    
                lines = section.strip().split('\n')
                first_line = lines[0].lower()
                print(f"\nProcessing section starting with: {first_line}")
                
                if 'recipe title' in first_line:
                    recipe['title'] = lines[-1].strip()
                    print(f"Found title: {recipe['title']}")
                elif 'basic info' in first_line:
                    for line in lines[1:]:
                        line_lower = line.lower()
                        if 'preparation time' in line_lower:
                            recipe['prepTime'] = line.split(':')[-1].strip()
                        elif 'cooking time' in line_lower:
                            recipe['cookTime'] = line.split(':')[-1].strip()
                        elif 'total time' in line_lower:
                            recipe['totalTime'] = line.split(':')[-1].strip()
                        elif 'servings' in line_lower:
                            recipe['servings'] = line.split(':')[-1].strip()
                        elif 'difficulty' in line_lower:
                            recipe['difficulty'] = line.split(':')[-1].strip()
                        elif 'cost' in line_lower:
                            recipe['costPerServing'] = line.split(':')[-1].strip()
                    print(f"Processed basic info: {recipe['prepTime']}, {recipe['cookTime']}, {recipe['totalTime']}")
                elif 'ingredients' in first_line:
                    current_ingredients = []
                    current_substitutions = {}
                    for line in lines[1:]:
                        if line.strip('- '):
                            if 'substitution' in line.lower() or 'substitute' in line.lower():
                                parts = line.split(':')
                                if len(parts) > 1:
                                    ingredient = parts[0].strip('- ').strip()
                                    subs = parts[1].strip()
                                    current_substitutions[ingredient] = subs
                            else:
                                current_ingredients.append(line.strip('- '))
                    recipe['ingredients'] = current_ingredients
                    recipe['substitutions'] = current_substitutions
                    print(f"Found {len(current_ingredients)} ingredients")
                elif 'instructions' in first_line:
                    instructions = []
                    pro_tips = []
                    for line in lines[1:]:
                        if line.strip():
                            if 'pro tip' in line.lower() or 'tip:' in line.lower():
                                pro_tips.append(line.strip('- '))
                            elif line[0].isdigit():
                                instructions.append(line.split('.', 1)[-1].strip())
                    recipe['instructions'] = instructions
                    recipe['proTips'] = pro_tips
                    print(f"Found {len(instructions)} instructions and {len(pro_tips)} pro tips")
                elif 'nutritional' in first_line:
                    for line in lines[1:]:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            recipe['nutrition'][key.strip()] = value.strip()
                    print(f"Found {len(recipe['nutrition'])} nutrition facts")
                elif 'dietary' in first_line:
                    dietary_info = []
                    for line in lines[1:]:
                        if line.strip('- '):
                            info_type = ''
                            icon = 'fa-info-circle'
                            
                            line_lower = line.lower()
                            if any(category in line_lower for category in ['vegetarian', 'vegan', 'gluten-free', 'keto', 'paleo']):
                                info_type = 'diet'
                                icon = 'fa-leaf'
                            elif 'allerg' in line_lower:
                                info_type = 'allergen'
                                icon = 'fa-exclamation-triangle'
                            elif 'benefit' in line_lower:
                                info_type = 'benefit'
                                icon = 'fa-heart'
                            elif 'medical' in line_lower:
                                info_type = 'medical'
                                icon = 'fa-notes-medical'
                            elif 'avoid' in line_lower:
                                info_type = 'avoid'
                                icon = 'fa-ban'
                            elif any(term in line_lower for term in ['halal', 'kosher', 'religious', 'cultural']):
                                info_type = 'cultural'
                                icon = 'fa-globe'
                                
                            dietary_info.append({
                                'type': info_type,
                                'text': line.strip('- '),
                                'icon': icon
                            })
                    recipe['dietary'] = dietary_info
                    print(f"Found {len(dietary_info)} dietary information items")
                elif 'equipment' in first_line:
                    recipe['equipment'] = [line.strip('- ') for line in lines[1:] if line.strip('- ')]
                    print(f"Found {len(recipe['equipment'])} equipment items")
                elif 'storage' in first_line or 'reheating' in first_line:
                    recipe['storage'].extend([line.strip('- ') for line in lines[1:] if line.strip('- ')])
                    print(f"Found {len(recipe['storage'])} storage instructions")
                elif 'pairing' in first_line:
                    recipe['pairings'] = [line.strip('- ') for line in lines[1:] if line.strip('- ')]
                    print(f"Found {len(recipe['pairings'])} pairing suggestions")
                elif 'presentation' in first_line:
                    recipe['presentation'] = [line.strip('- ') for line in lines[1:] if line.strip('- ')]
                    print(f"Found {len(recipe['presentation'])} presentation tips")
                elif 'cost-saving' in first_line:
                    recipe['costSavingTips'] = [line.strip('- ') for line in lines[1:] if line.strip('- ')]
                    print(f"Found {len(recipe['costSavingTips'])} cost-saving tips")
            
            print("\nFinished processing recipe")
            print(f"Final recipe structure: {recipe}")
            return jsonify(recipe)
            
        except Exception as e:
            print(f"\nError in Gemini API or parsing: {str(e)}")
            return jsonify({'error': f'Failed to generate recipe: {str(e)}'}), 500
            
    except Exception as e:
        print(f"\nServer Error: {str(e)}")
        return jsonify({'error': f'Server Error: {str(e)}'}), 500

@app.route('/ar-food')
def ar_food():
    return render_template('ar-food.html')

@app.route('/analyze_food', methods=['POST'])
def analyze_food():
    try:
        if 'image' not in request.files:
            print("Error: No image file in request")
            return jsonify({'error': 'No image file provided'}), 400
            
        image_file = request.files['image']
        if not image_file.filename:
            print("Error: Empty filename")
            return jsonify({'error': 'No image selected'}), 400
            
        # Check file type
        if not image_file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            print(f"Error: Invalid file type - {image_file.filename}")
            return jsonify({'error': 'Please upload a valid image file (PNG, JPG, JPEG, GIF)'}), 400
            
        try:
            # Read the image file
            image_data = image_file.read()
            if not image_data:
                print("Error: Empty image data")
                return jsonify({'error': 'The uploaded file appears to be empty'}), 400
                
            # Check image size (max 5MB)
            if len(image_data) > 5 * 1024 * 1024:
                print("Error: Image too large")
                return jsonify({'error': 'Image size should be less than 5MB'}), 400

            # Convert image data to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Construct the prompt for Gemini with emphasis on image analysis
            food_prompt = """You are a food recognition expert. Analyze this food image carefully and identify the exact dish shown.

IMPORTANT:
1. Look at the image carefully and identify the specific dish shown
2. Consider the ingredients, presentation, and cooking style visible in the image
3. If the dish is a specific regional variation, identify it
4. If the dish has a specific name in the local cuisine, use that name
5. Be precise in identifying the dish - don't generalize
6. If you're not confident about the dish, describe what you see and make an educated guess
7. Focus on the visual characteristics of the dish in the image

Provide the following information in EXACTLY this JSON format:

{
    "name": "Exact name of the dish shown in the image",
    "description": "Detailed description of what you see in the image and its cultural significance",
    "benefits": [
        "Benefit 1 specific to this dish",
        "Benefit 2 specific to this dish",
        "Benefit 3 specific to this dish",
        "Benefit 4 specific to this dish"
    ],
    "recipe_details": {
        "ingredients": [
            "Ingredient 1 with exact measurement as shown in the image",
            "Ingredient 2 with exact measurement as shown in the image",
            "Ingredient 3 with exact measurement as shown in the image"
        ],
        "instructions": [
            "Step 1: Detailed instruction based on what you see in the image",
            "Step 2: Detailed instruction based on what you see in the image",
            "Step 3: Detailed instruction based on what you see in the image"
        ],
        "preparation_time": "XX minutes (based on the complexity shown in the image)",
        "cooking_time": "XX minutes (based on the cooking method shown in the image)",
        "difficulty": "Easy/Medium/Hard (based on the complexity shown in the image)",
        "servings": "Number of servings (based on the portion shown in the image)",
        "nutritional_info": {
            "calories": "per serving (estimated based on visible ingredients)",
            "protein": "per serving (estimated based on visible ingredients)",
            "carbs": "per serving (estimated based on visible ingredients)",
            "fat": "per serving (estimated based on visible ingredients)"
        },
        "tips": [
            "Tip 1 based on what you see in the image",
            "Tip 2 based on what you see in the image",
            "Tip 3 based on what you see in the image"
        ],
        "equipment": [
            "Required equipment 1 (based on the cooking method shown)",
            "Required equipment 2 (based on the cooking method shown)"
        ]
    }
}

Important:
1. Return ONLY the JSON object, no other text
2. The food item must have exactly 4 benefits
3. The response must be valid JSON that can be parsed
4. Use double quotes for all strings
5. Do not include any markdown formatting or additional text
6. Base all information on what you actually see in the image
7. Be specific about the dish shown, not generic
8. If you're unsure about any aspect, make an educated guess based on the image
9. Focus on the visual characteristics and presentation of the dish
10. Consider the cooking method, ingredients, and presentation style visible in the image"""
            
            print("Sending request to Gemini API...")
            # Generate content using Gemini with the image
            try:
                response = model.generate_content([
                    food_prompt,
                    {
                        'mime_type': 'image/jpeg',
                        'data': image_base64
                    }
                ])
            except Exception as e:
                print(f"Error calling Gemini API: {str(e)}")
                return jsonify({'error': 'Failed to process image with AI service'}), 500
            
            if not response or not hasattr(response, 'text'):
                print("Error: Invalid response from Gemini API")
                return jsonify({'error': 'Invalid response from AI service'}), 500
                
            food_text = response.text.strip()
            print(f"Received response from Gemini API: {food_text[:100]}...")  # Print first 100 chars
            
            if not food_text:
                print("Error: Empty response from Gemini API")
                return jsonify({'error': 'Empty response from AI service'}), 500
            
            # Clean up the response to ensure it's valid JSON
            food_text = food_text.replace('```json', '').replace('```', '').strip()
            
            try:
                food_data = json.loads(food_text)
                
                # Validate the structure
                required_fields = ['name', 'description', 'benefits', 'recipe_details']
                if not all(field in food_data for field in required_fields):
                    print(f"Error: Missing required fields. Found: {list(food_data.keys())}")
                    raise ValueError("Missing required fields in food data")
                    
                if not isinstance(food_data['benefits'], list) or len(food_data['benefits']) != 4:
                    print(f"Error: Invalid benefits format. Found: {food_data['benefits']}")
                    raise ValueError("Invalid benefits format")
                    
                required_recipe_fields = ['ingredients', 'instructions', 'preparation_time', 'cooking_time', 
                                        'difficulty', 'servings', 'nutritional_info', 'tips', 'equipment']
                if not all(field in food_data['recipe_details'] for field in required_recipe_fields):
                    print(f"Error: Missing recipe fields. Found: {list(food_data['recipe_details'].keys())}")
                    raise ValueError("Missing required fields in recipe details")
                
                print("Successfully processed food data")
                return jsonify(food_data)
                
            except json.JSONDecodeError as e:
                print(f"Error parsing food JSON: {str(e)}")
                print(f"Raw response: {food_text}")
                return jsonify({'error': 'Failed to parse food details'}), 500
            except ValueError as e:
                print(f"Error validating food data: {str(e)}")
                return jsonify({'error': 'Invalid food data format'}), 500
                
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return jsonify({'error': 'Error processing the image file'}), 500
            
    except Exception as e:
        print(f"Unexpected error in analyze_food: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred while analyzing the food image'}), 500

@app.route('/voice-input')
def voice_input():
    return render_template('voice-input.html')

@app.route('/generate_voice_recipe', methods=['POST'])
def generate_voice_recipe():
    try:
        data = request.get_json()
        if not data or 'request' not in data:
            return jsonify({'error': 'No voice request provided'}), 400

        request_text = data['request']
        if not request_text.strip():
            return jsonify({'error': 'Empty voice request'}), 400
            
        print(f"\nGenerating recipe from voice request: {request_text}")
        
        # Create a more focused prompt for Gemini
        prompt = f"""You are a culinary expert. Based on the following voice request, create a detailed recipe:
        "{request_text}"

        IMPORTANT INSTRUCTIONS:
        1. Focus on the specific food item or dish mentioned in the request
        2. If multiple items are mentioned, choose the most prominent one
        3. If no specific food is mentioned, ask for clarification
        4. Create a recipe that closely matches the requested food item
        5. Use authentic ingredients and preparation methods for the specific dish
        6. Consider regional variations if mentioned
        7. Include traditional cooking techniques
        8. Provide accurate measurements and timings
        9. Suggest appropriate accompaniments
        10. Include tips for authentic preparation

        Provide the following information in EXACTLY this JSON format:

        {{
            "name": "Exact name of the requested dish",
            "description": "Brief description of the dish and its cultural significance",
            "benefits": [
                "Benefit 1 specific to this dish",
                "Benefit 2 specific to this dish",
                "Benefit 3 specific to this dish",
                "Benefit 4 specific to this dish"
            ],
            "recipe_details": {{
                "ingredients": [
                    "Ingredient 1 with exact measurement",
                    "Ingredient 2 with exact measurement",
                    "Ingredient 3 with exact measurement"
                ],
                "instructions": [
                    "Step 1: Detailed instruction with timing and temperature",
                    "Step 2: Detailed instruction with timing and temperature",
                    "Step 3: Detailed instruction with timing and temperature"
                ],
                "preparation_time": "XX minutes (include prep and marination time)",
                "cooking_time": "XX minutes (include actual cooking time)",
                "difficulty": "Easy/Medium/Hard",
                "servings": "Number of servings",
                "nutritional_info": {{
                    "calories": "per serving",
                    "protein": "per serving",
                    "carbs": "per serving",
                    "fat": "per serving"
                }},
                "tips": [
                    "Tip 1 for authentic preparation",
                    "Tip 2 for best results",
                    "Tip 3 for variations"
                ],
                "equipment": [
                    "Required equipment 1",
                    "Required equipment 2"
                ],
                "accompaniments": [
                    "Suggested side dish 1",
                    "Suggested side dish 2"
                ],
                "variations": [
                    "Regional variation 1",
                    "Regional variation 2"
                ]
            }}
        }}

        Important:
        1. Return ONLY the JSON object, no other text
        2. The food item must have exactly 4 benefits
        3. The response must be valid JSON that can be parsed
        4. Use double quotes for all strings
        5. Do not include any markdown formatting or additional text
        6. Provide exact measurements for ingredients
        7. Include timing and temperature in instructions where applicable
        8. Add nutritional information per serving
        9. Include practical tips for best results
        10. Make instructions detailed but easy to follow
        11. Focus on the specific dish requested
        12. Use authentic ingredients and methods
        13. Include traditional accompaniments
        14. Consider regional variations if applicable"""

        try:
            print("\nSending request to Gemini API...")
            response = model.generate_content(prompt)
            
            if not response or not hasattr(response, 'text'):
                print("Error: Invalid response from Gemini API")
                return jsonify({'error': 'Invalid response from recipe generation service'}), 500
                
            recipe_text = response.text.strip()
            print(f"\nGemini Response Text:\n{recipe_text}")
            
            if not recipe_text:
                print("Error: Empty response from Gemini API")
                return jsonify({'error': 'Empty response from recipe generation service'}), 500
            
            # Clean up the response to ensure it's valid JSON
            recipe_text = recipe_text.replace('```json', '').replace('```', '').strip()
            
            try:
                recipe_data = json.loads(recipe_text)
                
                # Validate the structure
                required_fields = ['name', 'description', 'benefits', 'recipe_details']
                if not all(field in recipe_data for field in required_fields):
                    print(f"Error: Missing required fields. Found: {list(recipe_data.keys())}")
                    raise ValueError("Missing required fields in recipe data")
                    
                if not isinstance(recipe_data['benefits'], list) or len(recipe_data['benefits']) != 4:
                    print(f"Error: Invalid benefits format. Found: {recipe_data['benefits']}")
                    raise ValueError("Invalid benefits format")
                    
                required_recipe_fields = ['ingredients', 'instructions', 'preparation_time', 'cooking_time', 
                                        'difficulty', 'servings', 'nutritional_info', 'tips', 'equipment',
                                        'accompaniments', 'variations']
                if not all(field in recipe_data['recipe_details'] for field in required_recipe_fields):
                    print(f"Error: Missing recipe fields. Found: {list(recipe_data['recipe_details'].keys())}")
                    raise ValueError("Missing required fields in recipe details")
                
                print("Successfully generated recipe from voice request")
                return jsonify(recipe_data)
                
            except json.JSONDecodeError as e:
                print(f"Error parsing recipe JSON: {str(e)}")
                print(f"Raw response: {recipe_text}")
                return jsonify({'error': 'Failed to parse recipe details'}), 500
            except ValueError as e:
                print(f"Error validating recipe data: {str(e)}")
                return jsonify({'error': 'Invalid recipe data format'}), 500
                
        except Exception as e:
            print(f"Error in Gemini API: {str(e)}")
            return jsonify({'error': 'Failed to generate recipe from voice request'}), 500
            
    except Exception as e:
        print(f"Unexpected error in generate_voice_recipe: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred while generating the recipe'}), 500

@app.route('/meal-planning')
def meal_planning():
    return render_template('meal_planning.html')

@app.route('/generate_meal_plan', methods=['POST'])
def generate_meal_plan():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('dateRange'):
            return jsonify({'error': 'Date range is required'}), 400
            
        # Validate date range format and generate list of dates
        try:
            start_date, end_date = data['dateRange'].split(' to ')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            if end_date <= start_date:
                return jsonify({'error': 'End date must be after start date'}), 400
                
            if (end_date - start_date).days > 14:
                return jsonify({'error': 'Date range cannot exceed 14 days'}), 400

            # Generate list of dates for the meal plan
            date_list = []
            current_date = start_date
            while current_date <= end_date:
                date_list.append(current_date.strftime('%Y-%m-%d'))
                current_date = current_date + timedelta(days=1)
            days = len(date_list)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD to YYYY-MM-DD'}), 400

        # Validate numeric inputs
        try:
            people_count = int(data.get('peopleCount', 1))
            if not 1 <= people_count <= 10:
                return jsonify({'error': 'Number of people must be between 1 and 10'}), 400
                
            budget = int(data.get('budget', 0))
            if budget < 100:
                return jsonify({'error': 'Budget must be at least ₹100'}), 400
                
            cooking_time = int(data.get('cookingTime', 30))
            if not 15 <= cooking_time <= 120:
                return jsonify({'error': 'Cooking time must be between 15 and 120 minutes'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid numeric input'}), 400

        # Calculate number of days
        days = (end_date - start_date).days + 1
        meal_types = data.get('mealTypes', ['breakfast', 'lunch', 'dinner'])

        # Construct detailed prompt for Gemini with example structure
        prompt = f"""Generate a {days}-day meal plan for {people_count} people with a budget of ₹{budget} per day.

Dietary Requirements:
- Diet Type: {data.get('dietType', 'omnivore')}
- Dietary Goals: {', '.join(data.get('dietaryGoals', []))}
- Dietary Restrictions: {', '.join(data.get('dietaryRestrictions', []))}
- Allergies: {data.get('allergies', 'none')}
- Cuisine Preference: {data.get('cuisinePreference', 'any')}
- Maximum Cooking Time: {cooking_time} minutes
- Meal Types: {', '.join(meal_types)}
- Dates: {', '.join(date_list)}

FOLLOW THIS EXACT STRUCTURE. DO NOT DEVIATE FROM IT:

{{
    "mealPlan": [
        {{
            "date": "{date_list[0]}",
            "meals": [
                {{
                    "mealType": "breakfast",
                    "name": "Masala Dosa",
                    "description": "Crispy rice and lentil crepe served with potato filling",
                    "ingredients": [
                        {{
                            "name": "Rice",
                            "quantity": "2 cups",
                            "price": 40
                        }},
                        {{
                            "name": "Urad Dal",
                            "quantity": "1 cup",
                            "price": 30
                        }}
                    ],
                    "nutrition": {{
                        "calories": 450,
                        "protein": 12,
                        "carbs": 80,
                        "fats": 10,
                        "fiber": 4
                    }},
                    "cookingTime": 30,
                    "instructions": "1. Soak rice and dal...\n2. Grind to fine batter...\n3. Ferment overnight...",
                    "dietaryCompatibility": {{
                        "goals": ["weight_loss", "vegetarian"],
                        "restrictions": ["gluten_free"]
                    }},
                    "alternatives": [
                        {{
                            "name": "Ragi Dosa",
                            "reason": "Lower calorie option",
                            "nutrition": {{
                                "calories": 350,
                                "protein": 10,
                                "carbs": 65,
                                "fats": 8
                            }}
                        }}
                    ]
                }}
            ],
            "totalNutrition": {{
                "calories": 2200,
                "protein": 75,
                "carbs": 300,
                "fats": 65,
                "fiber": 25
            }},
            "shoppingList": [
                {{
                    "category": "Grains",
                    "items": [
                        {{
                            "name": "Rice",
                            "quantity": "2 kg",
                            "estimatedCost": 100
                        }}
                    ]
                }}
            ],
            "totalCost": 450
        }}
    ],
    "summary": {{
        "totalDays": {days},
        "averageDailyCost": 450,
        "nutritionalBalance": "Well-balanced with adequate protein and fiber",
        "dietaryCompliance": "Fully compliant with vegetarian requirements",
        "recommendations": [
            "Prep ingredients in advance for faster cooking",
            "Store leftover batter in refrigerator",
            "Consider meal prepping on weekends"
        ]
    }}
}}

IMPORTANT RULES:
1. Use the EXACT same structure as shown above
2. All numeric values MUST be numbers, not strings (e.g., use 450 not "450")
3. All dates MUST be in YYYY-MM-DD format
4. Each meal MUST have at least one alternative
5. Each day MUST include all selected meal types: {', '.join(meal_types)}
6. Each meal's cookingTime MUST be <= {cooking_time}
7. Each day's totalCost MUST be <= {budget}
8. DO NOT include any text outside the JSON structure
9. DO NOT use markdown formatting
10. Use double quotes for all strings
11. Ensure all arrays and objects have matching brackets
12. All prices MUST be in ₹ (INR)"""

        print("\nSending request to Gemini API...")
        response = model.generate_content(prompt)
        
        if not response or not hasattr(response, 'text'):
            print("Error: Invalid response from Gemini API")
            return jsonify({'error': 'Invalid response from meal plan generation service'}), 500
            
        try:
            # Clean up the response text
            meal_plan_text = response.text.strip()
            meal_plan_text = meal_plan_text.replace('```json', '').replace('```', '').strip()
            
            print("\nParsing Gemini response...")
            print(f"Response text: {meal_plan_text[:200]}...")  # Print first 200 chars for debugging
            
            # Parse the response as JSON
            meal_plan = json.loads(meal_plan_text)
            
            # Validate the response structure
            if not isinstance(meal_plan, dict):
                raise ValueError("Response is not a JSON object")
                
            if 'mealPlan' not in meal_plan:
                raise ValueError("Response missing 'mealPlan' array")
                
            if not isinstance(meal_plan['mealPlan'], list):
                raise ValueError("'mealPlan' is not an array")
                
            if len(meal_plan['mealPlan']) != days:
                raise ValueError(f"Expected {days} days in meal plan, got {len(meal_plan['mealPlan'])}")
                
            # Validate each day in the meal plan
            expected_dates = set(date_list)
            found_dates = set()
            
            for day in meal_plan['mealPlan']:
                if not isinstance(day, dict):
                    raise ValueError("Day entry is not an object")
                    
                required_day_fields = ['date', 'meals', 'totalNutrition', 'shoppingList', 'totalCost']
                missing_fields = [field for field in required_day_fields if field not in day]
                if missing_fields:
                    raise ValueError(f"Day missing required fields: {', '.join(missing_fields)}")
                    
                if not isinstance(day['meals'], list):
                    raise ValueError("Day 'meals' is not an array")
                    
                # Validate date format and value
                try:
                    day_date = day['date']
                    datetime.strptime(day_date, '%Y-%m-%d')  # Validate format
                    if day_date not in expected_dates:
                        raise ValueError(f"Unexpected date in meal plan: {day_date}")
                    found_dates.add(day_date)
                except ValueError as e:
                    raise ValueError(f"Invalid date format or unexpected date: {day['date']}")
                    
                # Validate total cost
                if not isinstance(day['totalCost'], (int, float)) or day['totalCost'] > budget:
                    raise ValueError(f"Invalid or over-budget total cost: {day['totalCost']}")
                    
                # Validate meals
                meal_types_found = set()
                for meal in day['meals']:
                    if not isinstance(meal, dict):
                        raise ValueError("Meal entry is not an object")
                        
                    required_meal_fields = ['mealType', 'name', 'description', 'ingredients', 'nutrition', 
                                         'cookingTime', 'instructions', 'dietaryCompatibility', 'alternatives']
                    missing_fields = [field for field in required_meal_fields if field not in meal]
                    if missing_fields:
                        raise ValueError(f"Meal missing required fields: {', '.join(missing_fields)}")
                        
                    # Validate meal type
                    if meal['mealType'] not in meal_types:
                        raise ValueError(f"Invalid meal type: {meal['mealType']}")
                    meal_types_found.add(meal['mealType'])
                    
                    # Validate cooking time
                    if not isinstance(meal['cookingTime'], (int, float)) or meal['cookingTime'] > cooking_time:
                        raise ValueError(f"Invalid or too long cooking time: {meal['cookingTime']}")
                        
                    # Validate alternatives
                    if not isinstance(meal['alternatives'], list) or len(meal['alternatives']) == 0:
                        raise ValueError("Missing meal alternatives")
                        
                    # Validate ingredients
                    if not isinstance(meal['ingredients'], list) or len(meal['ingredients']) == 0:
                        raise ValueError("Missing ingredients")
                    for ingredient in meal['ingredients']:
                        if not all(key in ingredient for key in ['name', 'quantity', 'price']):
                            raise ValueError("Invalid ingredient format")
                        if not isinstance(ingredient['price'], (int, float)):
                            raise ValueError(f"Invalid ingredient price: {ingredient['price']}")
                
                # Check if all required meal types are present
                missing_meal_types = set(meal_types) - meal_types_found
                if missing_meal_types:
                    raise ValueError(f"Missing meal types for day {day['date']}: {', '.join(missing_meal_types)}")
            
            # Validate summary
            if 'summary' not in meal_plan:
                raise ValueError("Missing summary section")
                
            required_summary_fields = ['totalDays', 'averageDailyCost', 'nutritionalBalance', 
                                     'dietaryCompliance', 'recommendations']
            missing_fields = [field for field in required_summary_fields if field not in meal_plan['summary']]
            if missing_fields:
                raise ValueError(f"Summary missing required fields: {', '.join(missing_fields)}")
                
            if meal_plan['summary']['totalDays'] != days:
                raise ValueError(f"Incorrect total days in summary: {meal_plan['summary']['totalDays']}")
            
            print("Successfully validated meal plan structure")
            return jsonify(meal_plan)
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Problematic text: {meal_plan_text}")
            return jsonify({'error': 'Failed to parse meal plan response'}), 500
        except ValueError as e:
            print(f"Validation error: {str(e)}")
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred while processing the meal plan'}), 500
            
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/nutrition-analysis')
def nutrition_analysis():
    return render_template('nutrition-analysis.html')

@app.route('/analyze_nutrition', methods=['POST'])
def analyze_nutrition():
    try:
        data = request.get_json()
        
        # Validate input data
        if not data or 'food' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        food = data.get('food')
        
        # Construct detailed prompt for Gemini
        prompt = f"""Analyze the nutritional content of the following food item and provide a comprehensive nutritional analysis and recommendations.
        
Food Item: {food}

Provide a detailed analysis in the following JSON format:
{{
    "nutrition": {{
        "calories": {{"value": number, "unit": "kcal", "daily_percentage": number}},
        "protein": {{"value": number, "unit": "g", "daily_percentage": number}},
        "carbohydrates": {{"value": number, "unit": "g", "daily_percentage": number}},
        "fats": {{
            "total": {{"value": number, "unit": "g", "daily_percentage": number}},
            "saturated": {{"value": number, "unit": "g", "daily_percentage": number}},
            "unsaturated": {{"value": number, "unit": "g", "daily_percentage": number}},
            "trans": {{"value": number, "unit": "g", "daily_percentage": number}}
        }},
        "fiber": {{"value": number, "unit": "g", "daily_percentage": number}},
        "sugar": {{"value": number, "unit": "g", "daily_percentage": number}},
        "sodium": {{"value": number, "unit": "mg", "daily_percentage": number}},
        "vitamins": [
            {{"name": "Vitamin A", "value": number, "unit": "IU", "daily_percentage": number}},
            {{"name": "Vitamin C", "value": number, "unit": "mg", "daily_percentage": number}},
            {{"name": "Vitamin D", "value": number, "unit": "IU", "daily_percentage": number}},
            {{"name": "Vitamin E", "value": number, "unit": "mg", "daily_percentage": number}},
            {{"name": "Vitamin K", "value": number, "unit": "mcg", "daily_percentage": number}},
            {{"name": "B Vitamins", "value": string, "unit": "N/A", "daily_percentage": "N/A"}}
        ],
        "minerals": [
            {{"name": "Calcium", "value": number, "unit": "mg", "daily_percentage": number}},
            {{"name": "Iron", "value": number, "unit": "mg", "daily_percentage": number}},
            {{"name": "Magnesium", "value": number, "unit": "mg", "daily_percentage": number}},
            {{"name": "Potassium", "value": number, "unit": "mg", "daily_percentage": number}},
            {{"name": "Zinc", "value": number, "unit": "mg", "daily_percentage": number}}
        ]
    }},
    "diet_fit": {{
        "weight_loss": "Detailed analysis of how this food fits into a weight loss diet, including portion recommendations and timing",
        "muscle_gain": "Detailed analysis of how this food supports muscle growth and recovery, including protein content and timing",
        "heart_health": "Detailed analysis of how this food affects heart health, including cholesterol and blood pressure considerations",
        "athletic_performance": "Detailed analysis of how this food benefits athletic performance, including energy provision and recovery"
    }},
    "benefits": [
        {{
            "title": "Specific health benefit 1",
            "description": "Detailed explanation of how this food provides this benefit and its impact on health"
        }},
        {{
            "title": "Specific health benefit 2",
            "description": "Detailed explanation of how this food provides this benefit and its impact on health"
        }},
        {{
            "title": "Specific health benefit 3",
            "description": "Detailed explanation of how this food provides this benefit and its impact on health"
        }},
        {{
            "title": "Specific health benefit 4",
            "description": "Detailed explanation of how this food provides this benefit and its impact on health"
        }}
    ],
    "warnings": [
        {{
            "title": "Specific warning 1",
            "description": "Detailed explanation of the potential concern and who should be cautious"
        }},
        {{
            "title": "Specific warning 2",
            "description": "Detailed explanation of the potential concern and who should be cautious"
        }},
        {{
            "title": "Specific warning 3",
            "description": "Detailed explanation of the potential concern and who should be cautious"
        }}
    ]
}}

Ensure that:
1. All nutritional values are accurate and realistic
2. Provide specific recommendations for different dietary goals
3. Include detailed vitamin and mineral content
4. List specific health benefits and potential concerns
5. Consider standard portion sizes
6. Return ONLY the JSON object, no other text
7. Use double quotes for all strings
8. Do not include any markdown formatting or additional text
9. For diet fit, provide specific, actionable recommendations
10. For benefits, focus on scientifically supported health benefits
11. For warnings, include specific health conditions and populations that should be cautious
12. Make all recommendations practical and easy to understand"""

        # Get response from Gemini
        response = model.generate_content(prompt)
        
        if not response or not hasattr(response, 'text'):
            return jsonify({'error': 'Invalid response from AI service'}), 500
            
        nutrition_text = response.text.strip()
        
        if not nutrition_text:
            return jsonify({'error': 'Empty response from AI service'}), 500
        
        # Clean up the response to ensure it's valid JSON
        nutrition_text = nutrition_text.replace('```json', '').replace('```', '').strip()
        
        try:
            # Parse the response as JSON
            nutrition_data = json.loads(nutrition_text)
            
            # Validate the response structure
            required_nutrition_fields = ['calories', 'protein', 'carbohydrates', 'fats', 'fiber', 'sugar', 'sodium', 'vitamins', 'minerals']
            if not all(field in nutrition_data.get('nutrition', {}) for field in required_nutrition_fields):
                return jsonify({'error': 'Invalid nutrition data format'}), 500
                
            if not isinstance(nutrition_data.get('benefits', []), list):
                return jsonify({'error': 'Invalid benefits format'}), 500
                
            if not isinstance(nutrition_data.get('warnings', []), list):
                return jsonify({'error': 'Invalid warnings format'}), 500
                
            return jsonify(nutrition_data)
            
        except json.JSONDecodeError as e:
            print(f"Error parsing nutrition JSON: {str(e)}")
            print(f"Raw response: {nutrition_text}")
            return jsonify({'error': 'Failed to parse nutrition analysis'}), 500
            
    except Exception as e:
        print(f"Error in nutrition analysis: {str(e)}")
        return jsonify({'error': 'Failed to analyze nutrition'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)