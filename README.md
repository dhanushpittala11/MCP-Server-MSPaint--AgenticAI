# MCP_Server_Client_MSPaint_AgenticAI
The MS Paint Application doesn't have API for the MCP Server to Access and connect it to the MCP Client. So, with the help of prompt, this program is designed such that the the MS Paint App is accessed through an MCP server and connected to the MCP Client automatically, without the use of any functional tool calls. 
Prompting is the Key in this project. The prompt is designed in such a way that LLM can call the paint tool through MCP Client Automatically, without the use of any manual commands. 

## Table of Contents
  * [Demo](#demo)
  * [Overview](#overview)
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



## Overview


## Motivation
Any Application needs to have API access in order to build MCP server for that particular application. The MS Paint Application doesn't have any API. Here, I am **hacking the MS Paint application, the application which doesn't have API, to connect it to the MCP CLient**. In a scenario where I need to automatically perform tasks on the paint application with the help of LLM by asking a question to it. How can I do that? This is where MCP comes into play. I write an MCP server which can call the necessary tools when the LLM requests, through the MCP client. I define a **system prompt and user query and with the help of these prompts and MCP Client, I am making the agent to automatically open the paint application, without manually using any paint commands, making the agent to draw a rectangle on the paint window and enter the answer for the user query inside the rectangle.**  

## What It Does
I write an MCP server which can call the necessary tools when the LLM requests, through the MCP client. I define a **system prompt and user query and with the help of these prompts and MCP Client, I am making the agent to automatically open the paint application, without manually using any paint commands, making the agent to draw a rectangle on the paint window and enter the answer for the user query inside the rectangle.**  

## Getting Started
  We will get started with installation and set up process. Clone the repository and open the folder using Vs Code.
  ### Clone this repository into a local folder:
  ```
  git clone https://github.com/dhanushpittala11/SummarizerText_Hf_End2End_1.git
  ```
  ### Setup Environment using:
  ```bash
  conda create -p venv python==3.10 -y
  ```
  If conda is not installed, run this command in the terminal of the project environment.
  ```bash
  pip install conda
  ```
  ### Activate the environment:
  ```bash
  conda activate venv/
  ```
  ### Install all the required libraries and packages using the command:
  ```bash
  pip install -r requirements.txt
  ```
## Usage
  ### Now run the script using:

## Directory Tree


## Bug / Feature Request


## Techstack Used


 ### Web Frameworks and Deployment
 * **FastAPI**
 * **uvicorn**
 * **Starlette**

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

