# 资源网站
`ollama 网址：`https://ollama.com/

`官网Github仓库：`https://github.com/ollama/ollama

`安装包：` https://github.com/ollama/ollama/releases/tag/v0.5.13


# ollama 基础指令

### Pull a model

```shell
ollama pull llama3.2
```

> This command can also be used to update a local model. Only the diff will be pulled.

### Remove a model

```shell
ollama rm llama3.2
```

### Multiline input

For multiline input, you can wrap text with `"""`:

```
>>> """Hello,
... world!
... """
I'm a basic program that prints the famous "Hello, world!" message to the console.
```

### Multimodal models

```
ollama run llava "What's in this image? /Users/jmorgan/Desktop/smile.png"
```

> **Output**: The image features a yellow smiley face, which is likely the central focus of the picture.

### Pass the prompt as an argument

```shell
ollama run llama3.2 "Summarize this file: $(cat README.md)"
```

> **Output**: Ollama is a lightweight, extensible framework for building and running language models on the local machine. It provides a simple API for creating, running, and managing models, as well as a library of pre-built models that can be easily used in a variety of applications.

### Show model information

```shell
ollama show llama3.2
```

### List models on your computer

```shell
ollama list
```

### List which models are currently loaded

```shell
ollama ps
```

### Stop a model which is currently running

```shell
ollama stop llama3.2
```

### Start Ollama

`ollama serve` is used when you want to start ollama without running the desktop application.

## Building

See the [developer guide](https://github.com/ollama/ollama/blob/main/docs/development.md)

### Running local builds

Next, start the server:

```shell
./ollama serve
```

Finally, in a separate shell, run a model:

```shell
./ollama run llama3.2
```

## REST API

Ollama has a REST API for running and managing models.

### Generate a response

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt":"Why is the sky blue?"
}'
```

### Chat with a model

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    { "role": "user", "content": "why is the sky blue?" }
  ]
}'
```

See the [API documentation](./docs/api.md) for all endpoints.




# 启动服务
```shell
export CUDA_VISIBLE_DEVICES=5,6,7
/disk1/shuxun/LLMs/llama/ollama/bin/ollama serve

```

## 选定模型：
```shell

/disk1/shuxun/LLMs/llama/ollama/bin/ollama run llama3.2-vision

```


## 系统提示
2024/12/21 14:40:27 routes.go:1259: INFO server config env="map[CUDA_VISIBLE_DEVICES: GPU_DEVICE_ORDINAL: HIP_VISIBLE_DEVICES: HSA_OVERRIDE_GFX_VERSION: HTTPS_PROXY: HTTP_PROXY: NO_PROXY: OLLAMA_DEBUG:false OLLAMA_FLASH_ATTENTION:false OLLAMA_GPU_OVERHEAD:0 OLLAMA_HOST:http://127.0.0.1:11434 OLLAMA_INTEL_GPU:false OLLAMA_KEEP_ALIVE:5m0s OLLAMA_KV_CACHE_TYPE: OLLAMA_LLM_LIBRARY: OLLAMA_LOAD_TIMEOUT:5m0s OLLAMA_MAX_LOADED_MODELS:0 OLLAMA_MAX_QUEUE:512 OLLAMA_MODELS:/home/shuxun/.ollama/models OLLAMA_MULTIUSER_CACHE:false OLLAMA_NOHISTORY:false OLLAMA_NOPRUNE:false OLLAMA_NUM_PARALLEL:0 OLLAMA_ORIGINS:[http://localhost https://localhost http://localhost:* https://localhost:* http://127.0.0.1 https://127.0.0.1 http://127.0.0.1:* https://127.0.0.1:* http://0.0.0.0 https://0.0.0.0 http://0.0.0.0:* https://0.0.0.0:* app://* file://* tauri://* vscode-webview://*] OLLAMA_SCHED_SPREAD:false ROCR_VISIBLE_DEVICES: http_proxy: https_proxy: no_proxy:]"

https://www.geeksforgeeks.org/how-to-convert-any-huggingface-model-to-gguf-file-format/#


## 客户端
这两个示例展示了 `ollama` 库中的两种不同客户端：同步的 `Client` 和异步的 `AsyncClient`。它们的主要区别在于请求处理的方式：

### 1. **同步客户端：`Client`**

```python
from ollama import Client
client = Client(
  host='http://localhost:11434',
  headers={'x-some-header': 'some-value'}
)
response = client.chat(model='llama3.2-vision', messages=[
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
])

print(response.get("message")["content"])
```

- **同步请求**：`Client` 是同步的，这意味着请求会阻塞直到收到响应。在这段代码中，`client.chat` 是一个阻塞调用，也就是说，它会等待模型返回响应后才会继续执行后面的代码。
- **使用场景**：适合于简单的单线程应用，或者请求较少、不需要并发处理的场景。
- **执行流程**：调用 `client.chat()` 会等到模型返回聊天的响应之后，才会继续执行下一个语句。

### 2. **异步客户端：`AsyncClient`**

#### 示例 1：基本异步请求

```python
import asyncio
from ollama import AsyncClient

async def chat():
    # 创建异步客户端实例
    client = AsyncClient(
        host='http://localhost:11434',
        headers={'x-some-header': 'some-value'}
    )
    
    # 发送异步请求并获取响应
    response = await client.chat(model='llama3.2-vision', messages=[
        {
            'role': 'user',
            'content': 'Why is the sky blue?',
        },
    ])
    
    # 输出 response 中的 content
    print(response.get("message")["content"])


# 在 Jupyter Notebook 中直接运行
await chat()

# # 运行异步函数
# if __name__ == "__main__":
#     asyncio.run(main())
```

- **异步请求**：`AsyncClient` 是异步的，通过 `await` 关键字，它在等待模型响应时不会阻塞程序执行，而是可以执行其他任务。这意味着你可以同时发起多个请求，而不需要等待一个请求完成。
- **使用场景**：适合于高并发、高效的请求处理，尤其是在需要等待外部服务（如网络请求）的场景下，通过异步编程可以更高效地利用系统资源。
- **执行流程**：`await AsyncClient().chat()` 会启动一个异步请求并挂起该协程，直到收到响应。其他任务（如其它请求或程序中的其他部分）可以在等待响应时继续执行。

#### 示例 2：使用 `stream=True` 进行流式响应

```python
import asyncio
from ollama import AsyncClient

async def chat():
    client = AsyncClient(
        host='http://localhost:11434',
        headers={'x-some-header': 'some-value'}
    )
    message = {'role': 'user', 'content': 'Why is the sky blue?'}
    async for part in await client.chat(model='llama3.2-vision', messages=[message], stream=True):
        print(part['message']['content'], end='', flush=True)

# if __name__ == "__main__":
#     asyncio.run(chat())

await chat()
```

- **流式响应（`stream=True`）**：设置 `stream=True` 后，`chat` 函数会返回一个 **异步生成器**，这意味着响应将会分块（如逐步返回部分内容），而不是等到完整的响应返回后一次性处理。这样可以实时获取模型的输出，并且处理返回的每一部分，而不需要等待完整的响应数据。
- **使用场景**：适合处理大量数据或者需要实时处理响应的场景（例如：实时对话、视频/音频流、长时间运行的模型输出等）。
- **执行流程**：通过 `async for` 循环，程序会逐步处理每一部分的响应内容，并即时打印。

### 总结：

- **同步客户端（`Client`）**：适用于简单的应用程序，执行时会等待响应后才继续执行其他任务。适合不需要高并发的场景。
  
- **异步客户端（`AsyncClient`）**：适用于需要高并发、非阻塞的应用，尤其是在等待外部响应时可以执行其他任务。它使用 `await` 和 `async for`，并且支持流式响应（`stream=True`）来实现更灵活的处理方式。

这两者的主要区别在于：
- `Client` 是阻塞（同步）调用，适用于请求较少的场景；
- `AsyncClient` 是非阻塞（异步）调用，适用于高并发或实时处理的场景。