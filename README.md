# MCP_Server_Client_MSPaint_AgenticAI

Prompting is the Key in this project. The prompt is designed in such a way that LLM can call the paint tool through MCP Client Automatically, without the use of any manual commands. 

## Table of Contents
  * [Demo](#demo)
  * [Motivation](#motivation)
  * [What It Does](#what-it-does)
  * [Getting Started](#Getting-started)
  * [Usage](#usage)
  * [Directory Tree](#directory-tree)
  * [To Do](#to-do)
  * [Bug / Feature Request](#bug---feature-request)
  * [Techstack Used](#techstack-used)
  * [License](#license)
  * [Credits](#credits)

## Demo




## Motivation
Any Application needs to have API access in order to build MCP server for that particular application. The MS Paint Application doesn't have any API. Here, I am **hacking the MS Paint application, the application which doesn't have API, to connect it to the MCP CLient**. In a scenario where I need to automatically perform tasks on the paint application with the help of LLM by asking a question to it. How can I do that? This is where MCP comes into play. I write an MCP server which can call the necessary tools when the LLM requests, through the MCP client. I define a **system prompt and user query and with the help of these prompts and MCP Client, I am making the agent to automatically open the paint application, without manually using any paint commands, making the agent to draw a rectangle on the paint window and enter the answer for the user query inside the rectangle.**  

## What It Does
I write an MCP server which can call the necessary tools when the LLM requests, through the MCP client. I define a **system prompt and user query and with the help of these prompts and MCP Client, I am making the agent to automatically open the paint application, without manually using any paint commands, making the agent to draw a rectangle on the paint window and enter the answer for the user query inside the rectangle.**  

**There are further improvements on this task as well which I have divided into further two sections. So, there are three sections in total:**
  **Section 1 :** In the system prompt, I mention the tools to call and required instructions to follow while executing the user query. The Agent   successfully opens the paint application, draws a rectangle and types the text inside it. 

  **Section 2 :** Now I design my system prompt such that it qualifies all the rules mentioned in the file prompt_of_prompts.md[]. This makes sure that   
    - **The model makes step-by-step reasoning**
    - **The Prompt enforces a predictable output format, seperates the reasoning steps from the tool-use, computation steps**
    - **The prompt works in a multi-turn settings, instructs the model to self-verify, encourage the model to identify the type of reasoning used**
    - **The Prompt specifies necessary actions, in uncertain situations and when the tool fails**
    and then repeat the task performed in the section 1.

  **Section 3 :**  Here, I create 4 different modules for 4 cognitive layers: Perception, Memory, Decision-Making, Action. Then in the talk2mcp2.py file, I configure the whole agent by integrating these files. Then I repeat the section 2. Here, I use pydantic for all inputs and outputs and modify the system prompt with pydantic related changes. 
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


## Techstack Used



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

