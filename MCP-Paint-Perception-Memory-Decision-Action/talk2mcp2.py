import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial
import json
import ast

def parse_function_call_params(param_parts: list[str]) -> dict:
    """
    Parses key=value parts from the FUNCTION_CALL format.
    Supports nested keys like input.string=foo and list values like input.int_list=[1,2,3]
    Returns a nested dictionary.
    """
    result = {}

    for part in param_parts:
        if "=" not in part:
            raise ValueError(f"Invalid parameter format (expected key=value): {part}")

        key, value = part.split("=", 1)

        # Try to parse as Python literal (int, float, list, etc.)
        try:
            parsed_value = ast.literal_eval(value)
        except Exception:
            parsed_value = value.strip()

        # Support nested keys like input.string
        keys = key.split(".")
        current = result
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = parsed_value

    return result

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

max_iterations = 11
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(model, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    
    # Create a fresh Gemini model
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2-4.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                user_preference = input("Before we begin, please tell me something about your preferences (e.g., your location, tastes, favorite styles): ")

                system_prompt = f"""
You are an intelligent agent that must complete a multi-step task using available tools. You are equipped with reasoning, memory, and action capabilities.

👤 USER PREFERENCE (important): {user_preference}

===============================
🧠 TASK OVERVIEW  
The task must be done step-by-step. Each step uses a different tool. Do not skip steps. Here's the full task:

1. Open Microsoft Paint  
2. Draw a rectangle from (780, 380) to (1140, 700) by selecting the rectangle tool at (640, 109)  
3. Convert the word **Dhanush** into ASCII values  
4. Compute the exponential sum of these ASCII values  
5. Insert the result as text into the drawn rectangle in Paint

===============================
🧩 REASONING STRATEGY (Think before you act)
- Tag your reasoning type: is it visual, arithmetic, or symbolic?
- Internally verify output correctness before moving forward
- If unsure, ask yourself: "Do I have the right output to proceed?"

===============================
🔨 TOOL EXECUTION RULES  
- Use only one FUNCTION_CALL per step  
- Never repeat a tool with the same parameters  
- Use results from prior steps as inputs  
- Always wrap the value passed to `add_text_in_paint.text` in quotes (as a string), even if it is a number or scientific notation.
- If a tool fails, retry once. If it still fails, use:  
  `ERROR_HALT: [reason]`

===============================
✅ OUTPUT FORMAT  
Respond with exactly one line:
1. FUNCTION_CALL: tool_name|param1=value1|param2=value2
2. FINAL_ANSWER: [result]
3. ERROR_HALT: [reason]

📝 Examples:
- FUNCTION_CALL: open_paint  
- FUNCTION_CALL: draw_rectangle|x1=780|y1=380|x2=1140|y2=700  
- FUNCTION_CALL: strings_to_chars_to_int|input.string=Dhanush  
- FUNCTION_CALL: int_list_to_exponential_sum|input.int_list=[68,104,...]  
- FUNCTION_CALL: add_text_in_paint|text="12345.67"  
- FINAL_ANSWER: [12345.67]

===============================
🔁 SELF-CHECK & VALIDATION  
- After each tool call, internally verify: did it succeed?
- Is the output empty? Retry or halt.
- Don't move to the next step unless current one completes successfully

===============================
📍 PREFERENCE INTEGRATION  
Keep the user’s preference in mind throughout.  
Examples:
- Stylize or localize behavior if relevant
- Adjust how you represent the text or interaction (e.g., regional text format)

DO NOT include any explanations or extra text.
Only output a single line starting with FUNCTION_CALL, FINAL_ANSWER, or ERROR_HALT.
"""


                query = """First open Paint. Then draw a rectangle from (780, 380) to (1140, 700), by selecting the rectangle button at the coordinate(640, 109). Finally, calculate the sum of the exponentials of the ASCII values of the word Dhanush and add this sum as text inside the rectangle."""
                
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                # Track progress
                steps_completed = {
                    'paint_opened': False,
                    'rectangle_drawn': False,
                    'ascii_calculated': False,
                    'exponential_calculated': False,
                    'text_added': False
                }
                
                # Track the last successful tool call
                last_successful_tool = None
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    
                    # Improved progress summary
                    progress_summary = (
                        "Steps completed so far:\n"
                        f"1. Paint opened: {steps_completed['paint_opened']}\n"
                        f"2. Rectangle drawn: {steps_completed['rectangle_drawn']}\n"
                        f"3. ASCII calculated: {steps_completed['ascii_calculated']}\n"
                        f"4. Exponential calculated: {steps_completed['exponential_calculated']}\n"
                        f"5. Text added: {steps_completed['text_added']}\n"
                    )
                    previous_results = "\n".join(iteration_response)

                    # Add a hint if the last tool was repeated
                    repeat_hint = ""
                    if last_successful_tool:
                        repeat_hint = f"\nYou have already called {last_successful_tool}. Do not call it again. Move to the next step."

                    if last_response is None:
                        current_query = (
                            f"{query}\n\nStart with the first step."
                        )
                    else:
                        # Encourage step-by-step execution based on current progress
                        current_query = (
                            f"Current progress:\n{progress_summary}\n"
                            f"Recent tool outputs:\n{previous_results}\n"
                            f"{repeat_hint}\n\n"
                            "What should I do next to complete the task?"
    )


                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(model, prompt)
                        # Print the full LLM response for debugging
                        print(f"FULL LLM Response:\n{response.text}")
                        response_text = response.text.strip()
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.strip().startswith("FUNCTION_CALL:"):
                                response_text = line.strip()
                                break
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break

                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, param_parts = parts[0], parts[1:]

                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {param_parts}")

                        # Check if we're repeating the same tool call
                        # if func_name == last_successful_tool:
                        #     print(f"WARNING: Attempting to call {func_name} again. Skipping...")
                        #     iteration_response.append(f"Skipped duplicate call to {func_name}")
                        #     iteration += 1
                        #     continue

                        try:
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Handle tools with no parameters
                            if not param_parts:
                                arguments = {}
                            else:
                                arguments = parse_function_call_params(param_parts)
                            
                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            if func_name == "add_text_in_paint" and "text" in arguments:
                                arguments["text"] = str(arguments["text"])
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")

                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)

                            print(f"DEBUG: Final iteration result: {iteration_result}")

                            result_str = f"[{', '.join(iteration_result)}]" if isinstance(iteration_result, list) else str(iteration_result)

                            # Update progress tracking
                            # Update steps_completed dictionary
                            if func_name == "open_paint":
                                steps_completed['paint_opened'] = True
                            elif func_name == "draw_rectangle":
                                steps_completed['rectangle_drawn'] = True
                            elif func_name == "strings_to_chars_to_int":
                                steps_completed['ascii_calculated'] = True
                            elif func_name == "int_list_to_exponential_sum":
                                steps_completed['exponential_calculated'] = True
                            elif func_name == "add_text_in_paint":
                                steps_completed['text_added'] = True

                            # ✅ Only now mark this tool as the last successful one
                            last_successful_tool = func_name


                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            # Don't break on error, continue to next iteration

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Agent Execution Complete ===")
                        print(f"Final steps completed: {steps_completed}")
                        break

                    iteration += 1

                if iteration >= max_iterations:
                    print("\n=== MAX ITERATIONS REACHED ===")
                    print(f"Final steps completed: {steps_completed}")

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
