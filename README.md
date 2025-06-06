# chat-extract

<!-- docs/badge/coverage-badge.svg -->

![Coverage Status](docs/badge/coverage-badge.svg)
![Tests](docs/badge/tests-badge.svg)

Extract data from a screen recording of a chat conversation.

Chat-extract uses the OpenAI API to extract chat messages from a screen recording. It splits the video into frames, then passes those frames directly to a vision-enabled LLM to extract the chat messages. The extracted messages are then saved to a CSV file.

Because it uses a vision-enabled LLM, it can extract messages from any chat application, including WhatsApp, Telegram, and Discord. The downside of this is that it can only extract what is visible on the screen, so certain messaging platforms may not display things like dates or timestamps for every message.

It turns an video like this:

<img src="docs/screen-recording-example.gif" alt="example screen recording" style="max-width: 300px; width: 100%;">

Into a CSV file like this:

| sender       | message                                                                                | timestamp |
| ------------ | -------------------------------------------------------------------------------------- | --------- |
| Connor Smith | "Hey, where should we go for lunch today in SoHo?"                                     |           |
|              | "How about that new place, The Green Stove?"                                           |           |
| Connor Smith | I heard it’s good! But I’m in the mood for something different. Any other suggestions? |           |
|              | "What about Fable & Fork? It’s got great reviews."                                     |           |
| Connor Smith | "Ooh, that sounds nice. What kind of food do they have?"                               |           |
|              | "Mostly farm-to-table, a lot of seasonal options."                                     |           |
| Connor Smith | "That’s perfect. I’m craving something fresh. Is it far from here?"                    |           |
|              | "No, just a few blocks away! We could walk there in about 10 minutes."                 |           |
| Connor Smith | "Alright, but I just remembered, I’m kind of in the mood for sushi."                   |           |
|              | "In that case, let’s hit up Sushi Sora."                                               |           |
| Connor Smith | "I’ve been meaning to try that place!"                                                 |           |
|              | "How about that new place, The Green Stove?"                                           |           |

## Installation

```bash
pipx install chat-extract
```

## Usage

```bash
chat-extract --help
```

## Limitations

Because this tool uses a vision-enabled LLM, it can only extract what is visible on the screen. This means that certain messaging platforms may not display things like dates or timestamps for every message. However, it does mean that it can extract messages from any chat application, including WhatsApp, Telegram, and Discord.

This tool is not perfect. It may misinterpret messages or fail to extract them altogether. It is recommended to review the extracted messages for accuracy and completeness.
