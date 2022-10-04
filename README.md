# interactions-transcript

WIP: This extension is currently work-in-progress, which means it might not function well  
WIP: HTML output mode is not yet implemented. Only JSON, CSV, XML and plain text are supported.

## Installation

### Install from PyPi

```bat
Currently not available
```

### Install from github

```bat
pip install git+https://github.com/ItsRqtl/interactions-transcript.git
```

### Build from source

```bat
git clone https://github.com/ItsRqtl/interactions-transcript.git
cd interactions-transcript
pip install .
```

## Usage

### Loading the extension

```py
from interactions import Client

client = Client(token="...")

client.load("interactions.ext.transcript")

client.start()
```

### Using the extension

```py
await Channel.get_transcript(limit=...)
```

### Another way to use

```py
from interactions import Client
from interactions.ext.transcript import get_transcript
...
await get_transcript(Channel, limit=...)
...
client.start()
```

Parameters of method `get_transcript`:

|Parameter|Type|Description|Default Value|
|---|---|---|---|
|channel|`interactions.Channel`|The channel to get transcript from||
|limit|`int`|The limit of messages to get|`100`|
|pytz_timezone|`str`|The timezone to use|`"UTC"`|
|military_time|`bool`|Whether to use military time or not|`False`|
|fancy_time|`bool`|Whether to use fancy time or not (only with html mode)|`False`|
|mode|`str`|The mode to use for the transcript (html, json, xml, csv, or plain)|`"html"`|
