# Large Language Model Server (llm-server)

This repository hosts the setup code for an automatic Falcon Large Language Model (LLM) server, designed to run smoothly on LambdaLabs. Currently the server will not run on H100 instances.

**llm-server** is designed with compatibility in mind and supports all major operating systems: MacOS, Linux, and Windows. The only prerequisites are that SSH and Python are installed on your system. 

This project pairs seamlessly with our companion **llm-chat** project, which provides an interactive chat interface that works harmoniously with this server. You can find **llm-chat** [here](https://github.com/Gadersd/llm-chat). 

In essence, this software allows you to easily spin up an instance on LambdaLabs and set up server services. Please follow the guidelines below for the setup process.

## Prerequisites

Make sure you download the .pem ssh key file from LambdaLabs and place it into the project folder before running the installation. Start an instance on LambdaLabs that has enough GPU memory to run the desired Falcon model. For the 40B models ~45 GB is needed.

## Getting Started

1. **Install the requirements:**

```bash
pip install -r requirements.txt
```

2. **Run the installation script:**

```bash
python3 install.py 
```
- This script will ask for the IP for the LambdaLabs instance, transfer necessary files to the instance and trigger setup scripts on the instance. Finally, it will open a new terminal with an SSH session to control the instance.

3. **Once the setup completes and the SSH session starts, run the following commands in the SSH session:**

```bash
cd llm/server
python3 test.py 
python3 chat_server.py
```
- `test.py` - downloads and tests the Falcon 7b instruct model to ensure that model inference works properly.
- `chat_server.py` - downloads the model if needed and starts a Falcon inference server.

Now your server is up and ready to host chat sessions. Please note that to keep the server memory usage in check, currently, only one chat user per server is allowed.

## Terminal Chat Session

For a terminal chat session, execute the following command in the project folder:
```bash
python3 chat_client.py
```
- This script will ask for the server IP address and then begin a chat session in the terminal itself.

## GUI Chat Session

To undertake the GUI chat session in a browser, perform the following steps:

1. Access the `my-ca.crt` file in the `cert` folder in the project folder, which is automatically downloaded by the `python3 install.py` script.
2. Add the `my-ca.crt` file as a certificate authority in your preferred web browser.
3. Download the **llm-chat** project and run with `npm run dev` or visit [here](https://gadersd.github.io/llm-chat/). Enter the server IP address to start the chat session.

## License

This project is licensed under the terms of the MIT license.

## Questions?

If you have any issues, or simply need assistance with the project, feel free to contact us. We're here to help!