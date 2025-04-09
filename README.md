# chat-extract

<!-- docs/badge/coverage-badge.svg -->

![Coverage Status](docs/badge/coverage-badge.svg)
![Tests](docs/badge/tests-badge.svg)

Extract data from a screen recording of a chat conversation.

Chat-extract uses the OpenAI API to extract chat messages from a screen recording. It splits the video into frames, then passes those frames directly to a vision-enabled LLM to extract the chat messages. The extracted messages are then saved to a CSV file.

Because it uses a vision-enabled LLM, it can extract messages from any chat application, including WhatsApp, Telegram, and Discord. The downside of this is that it can only extract what is visible on the screen, so certain messaging platforms may not display things like dates or timestamps for every message.

## Installation

```bash
pipx install chat-extract
```

## Usage

```bash
chat-extract --help
```
