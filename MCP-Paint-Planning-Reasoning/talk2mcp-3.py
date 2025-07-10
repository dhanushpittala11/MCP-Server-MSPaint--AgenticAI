import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and configure Gemini client
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)  

max_iterations = 5
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(model, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
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
        print(f"Error in LLM generation: {repr(e)}")  # More descriptive
        raise

def reset_state():
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()
    print("Starting main execution...")

    # ✅ Create a fresh Gemini model inside main()
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")

    try:
        server_params = StdioServerParameters(
            command="python",
            args=["example2-3.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                tools = tools_result.tools

                tools_description = []
                for i, tool in enumerate(tools):
                    try:
                        params = tool.inputSchema
                        desc = getattr(tool, 'description', 'No description available')
                        name = getattr(tool, 'name', f'tool_{i}')

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
                    except Exception as e:
                        tools_description.append(f"{i+1}. Error processing tool")

                tools_description = "\n".join(tools_description)

                system_prompt = f"""You are an agent executing tasks in iterations.
You have access to various paint tools and mathematical tools.

REASONING PROCESS - THINK STEP BY STEP:
1. **Analyze the Task**: Break down the current task into clear, sequential steps
2. **Plan Your Approach**: Identify which tools are needed for each step
3. **Execute Methodically**: Perform one step at a time, verifying each result
4. **Validate Progress**: Ensure each step brings you closer to the final goal
5. **Document Reasoning**: Internally track your decision-making process

Before responding, always think: "What is the next logical step? Which tool should I use? What parameters do I need? What should I expect as output?"

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...

2. For final answers:
   FINAL_ANSWER: [number]

Important rules:
- Do not skip any of the steps before giving the final answer
- Only give FINAL_ANSWER after completing all the required steps
- Do not repeat function calls with the same parameters

Before each FUNCTION_CALL, internally identify the reasoning type (e.g., arithmetic, logic, string manipulation, visual) and verify that the operation matches the reasoning type. If the reasoning type is unclear, skip execution and state the uncertainty.

You must internally verify the correctness of each intermediate result before proceeding to the next step. If something seems incorrect or inconsistent, retry or adjust accordingly before continuing.

If a function fails, produces an unexpected result, or you are unsure how to proceed, skip the FUNCTION_CALL and halt further actions. Log the issue internally and stop processing.

ERROR HANDLING AND FALLBACK STRATEGIES:
- **Tool Not Found**: If a tool doesn't exist, use ERROR_HALT: [Tool not available]
- **Invalid Parameters**: If parameters seem wrong, use ERROR_HALT: [Invalid parameters for function]
- **Unexpected Results**: If a tool returns unexpected output, use ERROR_HALT: [Unexpected result from function]
- **Uncertainty**: If you're unsure about the next step, use ERROR_HALT: [Uncertain about next action]
- **Logic Errors**: If your reasoning leads to a dead end, use ERROR_HALT: [Logic error in approach]

When using ERROR_HALT, provide a brief reason for the halt to help with debugging.

Examples:
- FUNCTION_CALL: add|5|3
- FUNCTION_CALL: strings_to_chars_to_int|INDIA
- FINAL_ANSWER: [42]

FALLBACK STRATEGIES:
- **Alternative Tools**: If one tool fails, consider if another tool can achieve the same goal
- **Parameter Adjustment**: If parameters fail, try with different values or formats
- **Step Simplification**: If a complex step fails, break it into simpler sub-steps
- **Context Re-evaluation**: If stuck, re-examine the overall task and current progress
- **Graceful Degradation**: If a non-critical step fails, continue with available tools

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:
"""

                query = """First open Paint. Then draw a rectangle from (780, 380) to (1140, 700), by selecting the rectangle button at the coordinate(640, 109). Finally, calculate the sum of the exponentials of the ASCII values of the word Dhanush and add this sum as text inside the rectangle."""

                global iteration, last_response
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(model, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")

                        # ... (no changes below this point)
                        # continue as-is with function call parsing, tool execution, and iteration
                       # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
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
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
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
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Agent Execution Complete ===")
                        # result = await session.call_tool("open_paint")
                        # print(result.content[0].text)

                        # Wait longer for Paint to be fully maximized
                        # await asyncio.sleep(1)

                        # Draw a rectangle
                        # result = await session.call_tool(
                        #     "draw_rectangle",
                        #     arguments={
                        #         "x1": 780,
                        #         "y1": 380,
                        #         "x2": 1140,
                        #         "y2": 700
                        #     }
                        # )
                        # print(result.content[0].text)

                        # Draw rectangle and add text
                        # result = await session.call_tool(
                        #     "add_text_in_paint",
                        #     arguments={
                        #         "text": response_text
                        #     }
                        # )
                        # print(result.content[0].text)
                        break
                    elif response_text.startswith("ERROR_HALT:"):
                        print(f"\n=== Agent Halted Due to Error ===")
                        print(f"Error: {response_text}")
                        break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {repr(e)}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()

if __name__ == "__main__":
    asyncio.run(main())
