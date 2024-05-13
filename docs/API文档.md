# API文档

参考: https://github.com/novicezk/midjourney-proxy/blob/f2b401070ac5a251e26f6f2c6f6a65dfb4f53177/src/main/resources/api-params/imagine.json

# generate

## API

description:

```http

POST /generate
Content-Type: Application/json

{
    "prompt": "提示词",
    
}
```

## Request Samples

```json
{
    "prompt": "提示词",
    "style": "纹理"
}
```

### Python

```python

```

## Response Samples

### 200

```json


```

### 400

```
```

### 405

```json

{
    "code": 0,
    "message": "405: Method Not Allowed"
}
```

### 500

# ws

```http 
ws /ws/trigger_id
```

# 队列

队列中信息为

```json
{
    "config": {
        "batch_size": 4
    },
    "requestId": "",
    "subTaskId": "",
    "taskId": "",
    "taskType": "TEXTURE",
    "mqParamsId": "",
    "textrue": {
        "prompt": "",
        "tags": [
            ""
        ],
        "styleId": "",
        "aspect": ""
    }
}
```

结果队列必须参数

```json
{
    "data": {
        "images": [],
        "requestId": "",
        "subTaskId": "",
        "taskId": "",
        "mqParamsId": ""
    }
    "code": ""
}

```
