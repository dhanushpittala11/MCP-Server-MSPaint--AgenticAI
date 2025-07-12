# MCP_Server_Client_MSPaint_AgenticAI

Prompting is the Key in this project. The prompt is designed in such a way that LLM can call the paint tool through MCP Client Automatically, without the use of any manual commands. 

## Table of Contents
  * [Demo](#demo)
  * [Motivation](#motivation)
  * [What It Does](#what-it-does)
  * [Getting Started](#Getting-started)
  * [Usage](#usage)
  * [Directory Tree](#directory-tree)
  * [Bug / Feature Request](#bug---feature-request)
  * [Techstack Used](#techstack-used)
  * [License](#license)
  * [Credits](#credits)

## Demo
[Demonstration_MCP-Paint-Perception-Memory-Decision-Action :](EAG_A6_DhanushPittala_m.mp4)

[Demonstration_MCP-Paint-Planning-Reasoning :](EAG_A5_DhanushPittala.webm)

https://github.com/user-attachments/assets/90147385-7243-4343-ab11-de200c30e77c


## Motivation
Any Application needs to have API access in order to build MCP server for that particular application. The MS Paint Application doesn't have any API. Here, I am **hacking the MS Paint application, the application which doesn't have API, to connect it to the MCP CLient**. In a scenario where I need to automatically perform tasks on the paint application with the help of LLM by asking a question to it. How can I do that? This is where MCP comes into play. I write an MCP server which can call the necessary tools when the LLM requests, through the MCP client. I define a **system prompt and user query and with the help of these prompts and MCP Client, I am making the agent to automatically open the paint application, without manually using any paint commands, making the agent to draw a rectangle on the paint window and enter the answer for the user query inside the rectangle.**  

## What It Does
I write an MCP server which can call the necessary tools when the LLM requests, through the MCP client. I define a **system prompt and user query and with the help of these prompts and MCP Client, I am making the agent to automatically open the paint application, without manually using any paint commands, making the agent to draw a rectangle on the paint window and enter the answer for the user query inside the rectangle.**  

**There are further improvements on this task as well which I have divided into further two sections. So, there are three sections in total:**
  **Section 1 :** In the system prompt, I mention the tools to call and required instructions to follow while executing the user query. The Agent   successfully opens the paint application, draws a rectangle and types the text inside it. 
  * **MCP Server :** [MCP-Paint/example2-3.py](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/blob/main/MCP-Paint/example2-3.py)
  * **Client and the Agent :** [MCP-Paint/talk2mcp-2.py](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/blob/main/MCP-Paint/talk2mcp-2.py)
    
  **Section 2 :** Now I design my system prompt such that it qualifies all the rules mentioned in the [file](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/blob/main/MCP-Paint/example2-3.py). This makes sure that   
  * **The model makes step-by-step reasoning**
  * **The Prompt enforces a predictable output format, seperates the reasoning steps from the tool-use, computation steps**
  * **The prompt works in a multi-turn settings, instructs the model to self-verify, encourage the model to identify the type of reasoning used**
  * **The Prompt specifies necessary actions, in uncertain situations and when the tool fails**
  and then repeat the task performed in the section 1.
  * **MCP Server :** [MCP-Paint-Planning-Reasoning/example2-3.py](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/tree/main/MCP-Paint-Planning-Reasoning/example2-3.py)
  * **Client and the Agent :** [MCP-Paint-Planning-Reasoning/talk2mcp-3.py](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/blob/main/MCP-Paint-Planning-Reasoning/talk2mcp-3.py)
    
  **Section 3 :**  Here, I create 4 different modules for 4 cognitive layers: Perception, Memory, Decision-Making, Action. Then in the talk2mcp2.py file, I configure the whole agent by integrating these files. Then I repeat the section 2. Here, I use pydantic for all inputs and outputs and modify the system prompt with pydantic related changes. 
  * **MCP Server :** [MCP-Paint-Perception-Memory-Decision-Action/example2-4.py](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/blob/main/MCP-Paint-Perception-Memory-Decision-Action/example2-4.py)
  * **Client and the Agent :** [MCP-Paint-Perception-Memory-Decision-Action/talk2mcp2.py](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/blob/main/MCP-Paint-Perception-Memory-Decision-Action/talk2mcp2.py)
    
## Getting Started
  We will get started with installation and set up process. Clone the repository and open the folders using Vs Code or Cursor IDE.
  ### Clone this repository into a local folder:
  ```
  git clone https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI.git
  ```
  ### Create a .env file to store Gemini API Key.
  ### Create a requirements.txt file
  ### Setup and activate Virtual Environment using:
  ```bash
  python -m venv .venv 
  source .venv/bin/activate 
  ```

  ### Install all the required libraries and packages using the command:
  ```bash
  pip install -r requirements.txt
  ```
## Usage
  ### Run the script for the section 1 using:
      ```bash
      python talk2mcp-2.py
      ```
  ### Run the script for the section 2 using:
      ```bash
      python talk2mcp-3.py
      ```
  ### Run the script for the section 3 using:
      ```bash
      python talk2mcp2.py
      ```
## Directory Tree


## Bug / Feature Request
If you find a bug (the website couldn't handle the query and / or gave undesired results), kindly open an issue [here](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/issues/new)

If you'd like to request a new function, feel free to do so by opening an issue [here](https://github.com/dhanushpittala11/MCP-Server-MSPaint--AgenticAI/issues/new).

## Techstack Used
| Layer                      | Technology/Library                                                  | Purpose                                                               |
| -------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **LLM**                    | `Google Generative AI (Gemini 2.0 Flash)`                           | Natural language reasoning and function planning                      |
| **Server Framework**       | `FastMCP` (`mcp.server.fastmcp`)                                    | Multimodal Command Protocol (MCP) tool interface for LLM-agent system |
| **MCP Transport**          | `StdioServerParameters`, `ClientSession`, `stdio_client`            | Communicate with MCP tools over subprocess (`example2-4.py`)          |
| **UI Automation**          | `pywinauto`                                                         | Control Paint GUI (open, click, type, drag mouse, etc.)               |
| **System APIs**            | `win32gui`, `win32con`, `win32api`, `GetSystemMetrics`              | Handle Paint window placement, interaction, screen resolution         |                                                |
| **Math Computation**       | `math`                                                              | Exponentials, factorials, trigonometric operations                    |
| **Async Handling**         | `asyncio`, `await`, `run_in_executor`                               | Concurrency and tool execution orchestration                          |
| **Environment Management** | `dotenv`                                                            | Load API keys securely from `.env`                                    |
| **Utilities**              | `os`, `sys`, `time`, `traceback`, `functools`, `concurrent.futures` | Miscellaneous operations, error tracing, retries                      |
### Tools Implemented
| Tool Name                       | Functionality                                    |
| ------------------------------- | ------------------------------------------------ |
| `open_paint()`                  | Launch Paint and maximize it on secondary screen |
| `draw_rectangle()`              | Draws a rectangle using mouse events             |
| `add_text_in_paint()`           | Types text inside Paint via GUI automation       |
| `add`, `subtract`, etc.         | Math tools: add, subtract, factorial, etc.       |
| `strings_to_chars_to_int()`     | Convert string to ASCII values                   |
| `int_list_to_exponential_sum()` | Sum of exponentials of a list                    |
| `fibonacci_numbers()`           | Generate Fibonacci sequence                      |
| `create_thumbnail()`            | Create image thumbnail using PIL                 |

### Architecture
```
               ┌─────────────────────────────┐
               │      Google Gemini API      │
               └────────────▲────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
┌────────────────────┐             ┌────────────────────┐
│   talk2mcp-3.py     │            │    talk2mcp2.py    │
│ Agent and Client    │            │ Agent and Client   │
└─────────▲─────── ───┘            └─────────▲──────────┘
          │                                    │
┌─────────┴────────────┐           ┌───────────┴────────────┐
│   example2-3.py       │          │     example2-4.py       │
│  Tool Server (FastMCP)│          │   Tool Server (FastMCP) │
└─────────┬─────────────┘          └──────────┬──────────────┘
          │                                    │
       Paint GUI ←―――― Draw + Type in Paint ―――→ Math/ASCII/Image Tools

```

## License
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

## Team
Dhanush Pittala - [@Linkedin](https://www.linkedin.com/in/dhanush-pittala-83b964225) - dhanushpittala05@gmail.com

## Credits
The School of AI(TSAI) -EAGv1  by Rohan Shravan
